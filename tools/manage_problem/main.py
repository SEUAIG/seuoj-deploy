#!/usr/bin/env python3
"""统一命令行入口：登录、提交、删除与上传题目相关数据。"""

from __future__ import annotations

import json
import re
import tomllib
import urllib.error
import urllib.request
import csv
import io
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tempfile import TemporaryDirectory

import typer

import src.delete_all_p_problems as delete_mod
import src.submit_all_p_problems as submit_mod
import src.upload_all_p_problem_config as upload_config_mod
import src.upload_all_p_problem_data as upload_mod

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table

    _RICH_AVAILABLE = True
except Exception:
    _RICH_AVAILABLE = False


DEFAULT_AUTH_CONFIG = Path("auth_config.toml")

app = typer.Typer(
    help="题目批量工具：支持 login、submit、delete、upload-data、upload-config 子命令",
    add_completion=False,
)


def _error(message: str) -> None:
    """输出错误并以 2 退出。"""
    typer.echo(f"错误: {message}", err=True)
    raise typer.Exit(2)


class _ProblemStatusBoard:
    """每题一行状态面板；可用 rich 时实时刷新，否则回退到普通日志。"""

    def __init__(self, labels: list[str], title: str) -> None:
        self.labels = labels
        self.title = title
        self.statuses = ["等待中"] * len(labels)
        self._lock = threading.Lock()
        self._use_rich = _RICH_AVAILABLE
        self._console = Console() if self._use_rich else None
        self._live = None

    def _render(self):
        table = Table(title=self.title)
        table.add_column("#", justify="right")
        table.add_column("题目")
        table.add_column("状态")
        for i, (label, status) in enumerate(zip(self.labels, self.statuses), start=1):
            table.add_row(str(i), label, status)
        return table

    def __enter__(self):
        if self._use_rich:
            self._live = Live(self._render(), console=self._console, refresh_per_second=8, transient=False)
            self._live.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._use_rich and self._live is not None:
            self._live.__exit__(exc_type, exc, tb)
            self._live = None

    def update(self, idx0: int, status: str) -> None:
        with self._lock:
            self.statuses[idx0] = status
            if self._use_rich and self._live is not None:
                self._live.update(self._render(), refresh=True)
            else:
                typer.echo(f"[{idx0 + 1}/{len(self.labels)}] {self.labels[idx0]} | {status}")


def _quote_toml_string(value: str) -> str:
    """把普通字符串转成可写入 TOML 的字符串。"""
    return json.dumps(value, ensure_ascii=False)


def _load_auth_config(config_path: Path) -> dict[str, str]:
    """读取认证配置文件。"""
    if not config_path.exists() or not config_path.is_file():
        raise FileNotFoundError(f"认证配置文件不存在或不是文件: {config_path}")

    with config_path.open("rb") as f:
        data = tomllib.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"认证配置文件格式不正确: {config_path}")

    result: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = value
        else:
            result[key] = str(value)
    return result


def _write_auth_config(config_path: Path, config: dict[str, str]) -> None:
    """写回认证配置文件。"""
    config_path.parent.mkdir(parents=True, exist_ok=True)

    ordered_keys = ["baseurl", "identifier", "password", "jwt"]
    lines = [
        "# 认证配置文件",
        "# login 命令会读取 baseurl/identifier/password，成功后把 jwt 写回这里。",
        "",
    ]

    written_keys: set[str] = set()
    for key in ordered_keys:
        value = config.get(key, "")
        lines.append(f"{key} = {_quote_toml_string(str(value))}")
        written_keys.add(key)

    for key, value in config.items():
        if key in written_keys:
            continue
        lines.append(f"{key} = {_quote_toml_string(str(value))}")

    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_config_value(config: dict[str, str], key: str) -> str:
    """从配置中读取字符串值。"""
    return (config.get(key) or "").strip()


def _resolve_token(config_path: Path) -> str:
    """从认证配置文件解析 token。"""
    if config_path.exists():
        config = _load_auth_config(config_path)
        token = _read_config_value(config, "jwt") or _read_config_value(config, "token")
        if token:
            return token

    raise ValueError(f"认证配置中缺少 jwt/token: {config_path}")


def _resolve_base_url(config_path: Path) -> str:
    """从认证配置文件解析 baseurl。"""
    if not config_path.exists() or not config_path.is_file():
        raise ValueError(f"认证配置文件不存在或不是文件: {config_path}")

    config = _load_auth_config(config_path)
    value = _read_config_value(config, "baseurl")
    if not value:
        raise ValueError(f"认证配置中缺少 baseurl: {config_path}")
    return value


def _read_pids_from_csv(pid_file: Path) -> list[str]:
    """读取 CSV 中的 pid 列。只要求存在 pid 列，其他列可选。"""
    if not pid_file.exists() or not pid_file.is_file():
        raise FileNotFoundError(f"pid 文件不存在或不是文件: {pid_file}")

    content = pid_file.read_text(encoding="utf-8")
    # 兼容历史损坏文件: 可能把表头和第一条记录粘连在一起。
    if content.startswith("folder,pid") and not (
        content.startswith("folder,pid\n") or content.startswith("folder,pid\r\n")
    ):
        content = content.replace("folder,pid", "folder,pid\n", 1)
    if content.startswith("pid") and not (content.startswith("pid\n") or content.startswith("pid\r\n")):
        content = content.replace("pid", "pid\n", 1)

    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise ValueError(f"pid CSV 缺少表头: {pid_file}")

    normalized = {name.strip(): name for name in reader.fieldnames if name}
    if "pid" not in normalized:
        raise ValueError(f"pid CSV 必须包含 pid 列，当前为: {','.join(reader.fieldnames)}")

    pids: list[str] = []
    for row in reader:
        pid = (row.get(normalized["pid"]) or "").strip().upper()
        if not pid:
            raise ValueError(f"pid CSV 中存在空 pid 行: {row}")
        if not re.fullmatch(r"[A-Z][A-Z0-9]{1,19}", pid):
            raise ValueError(f"pid CSV 中存在非法 pid: {pid}")
        pids.append(pid)
    return pids


def _login_request(base_url: str, identifier: str, password: str, timeout: int) -> dict[str, str]:
    """调用登录接口并返回 jwt。"""
    url = base_url.rstrip("/") + "/api/auth/login"
    payload = json.dumps({"identifier": identifier, "password": password}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url=url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as err:
        status = err.code
        body = err.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as err:
        raise RuntimeError(f"登录失败: 网络错误 {err.reason}") from err
    except TimeoutError as err:
        raise RuntimeError("登录失败: 请求超时") from err

    try:
        response = json.loads(body)
    except json.JSONDecodeError as err:
        raise RuntimeError(f"登录返回不是有效 JSON: {body[:300]}") from err

    if not isinstance(response, dict):
        raise RuntimeError(f"登录返回格式不正确: {body[:300]}")

    data = response.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"登录返回缺少 data 字段: {body[:300]}")

    jwt = _read_config_value(data, "jwt")
    message = str(response.get("message") or "").strip()

    if status >= 400:
        raise RuntimeError(f"登录失败: HTTP {status} | {message or body[:300]}")

    if not jwt:
        raise RuntimeError(f"登录成功但没有返回 jwt: {message or body[:300]}")

    return {"jwt": jwt}


def _sleep_before_retry(attempt: int, retry_delay: float) -> None:
    """重试前等待，使用简单线性退避。"""
    if retry_delay <= 0:
        return
    time.sleep(retry_delay * attempt)


def _request_status_with_retry(
    request_fn,
    retries: int,
    retry_delay: float,
) -> tuple[int, str]:
    """对返回 (status, body) 的请求执行重试，成功条件为 HTTP 2xx。"""
    max_attempts = retries + 1
    last_status = 0
    last_body = ""
    for attempt in range(1, max_attempts + 1):
        try:
            status, body = request_fn()
        except Exception as exc:
            status, body = 0, str(exc)
        last_status, last_body = status, body
        if 200 <= status < 300:
            return status, body
        if attempt < max_attempts:
            _sleep_before_retry(attempt, retry_delay)
    return last_status, last_body


def _delete_with_retry(
    request_fn,
    retries: int,
    retry_delay: float,
    ignore_not_found: bool,
) -> tuple[bool, int, str]:
    """对删除请求执行重试。"""
    max_attempts = retries + 1
    last_ok = False
    last_status = 0
    last_body = ""
    for attempt in range(1, max_attempts + 1):
        try:
            ok, status, body = request_fn()
        except Exception as exc:
            ok, status, body = False, 0, str(exc)
        if not ok and ignore_not_found and status == 404:
            ok = True
        last_ok, last_status, last_body = ok, status, body
        if ok:
            return ok, status, body
        if attempt < max_attempts:
            _sleep_before_retry(attempt, retry_delay)
    return last_ok, last_status, last_body


def _call_with_retry(func, retries: int, retry_delay: float):
    """对可能抛异常的调用执行重试。"""
    max_attempts = retries + 1
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts:
                _sleep_before_retry(attempt, retry_delay)
    assert last_exc is not None
    raise last_exc


def _build_submit_targets(
    root_data_dir: Path,
    success_pid_file: Path,
    new: bool,
    base_url: str,
    resolved_token: str,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> list[tuple[Path, str]]:
    """构建提交目标列表，返回 (题目目录, 指定 pid)。"""
    targets: list[tuple[Path, str]] = []
    if new:
        problem_dirs = submit_mod.find_problem_dirs(root_data_dir)
        if not problem_dirs:
            return []
        current_pid = _call_with_retry(
            lambda: submit_mod.fetch_next_pid(base_url, resolved_token, timeout),
            retries=retries,
            retry_delay=retry_delay,
        )
        current_pid = submit_mod.normalize_p_pid(current_pid)
        for pdir in problem_dirs:
            targets.append((pdir, current_pid))
            current_pid = submit_mod.increment_pid(current_pid)
        return targets

    if not success_pid_file.exists() or not success_pid_file.is_file():
        raise FileNotFoundError(f"update 模式需要已有 CSV 文件: {success_pid_file}；如需全量新建请加 --new")
    records = delete_mod.read_pid_file(success_pid_file)
    for folder, pid in records:
        pdir = root_data_dir / folder
        targets.append((pdir, submit_mod.normalize_p_pid(pid)))
    return targets


@app.command("login")
def login_command(
    config: Path = typer.Option(DEFAULT_AUTH_CONFIG, "--config", help="认证配置文件，默认 auth_config.toml"),
    timeout: int = typer.Option(15, "--timeout", help="单次请求超时秒数"),
    retries: int = typer.Option(2, "--retries", help="每次网络请求失败后的重试次数"),
    retry_delay: float = typer.Option(0.5, "--retry-delay", help="重试间隔秒数"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅检查配置，不实际登录"),
) -> None:
    """使用配置文件里的邮箱和密码登录，并把 jwt 写回配置文件。"""
    if timeout <= 0:
        _error("单次请求超时秒数必须大于 0")
    if retries < 0:
        _error("重试次数不能小于 0")
    if retry_delay < 0:
        _error("重试间隔秒数不能小于 0")

    config = config.resolve()
    try:
        config_data = _load_auth_config(config)
    except Exception as exc:
        _error(str(exc))

    try:
        base_url = _resolve_base_url(config)
    except Exception as exc:
        _error(str(exc))

    identifier = _read_config_value(config_data, "identifier") or _read_config_value(config_data, "email")
    password = _read_config_value(config_data, "password")
    if not identifier:
        _error(f"认证配置中缺少 identifier: {config}")
    if not password:
        _error(f"认证配置中缺少 password: {config}")

    if dry_run:
        typer.echo(f"将使用配置文件登录: {config}")
        typer.echo(f"identifier={identifier}")
        typer.echo(f"base_url={base_url}")
        typer.echo("dry-run 完成")
        raise typer.Exit(0)

    try:
        login_result = _call_with_retry(
            lambda: _login_request(base_url, identifier, password, timeout),
            retries=retries,
            retry_delay=retry_delay,
        )
    except Exception as exc:
        _error(str(exc))

    config_data.pop("email", None)
    config_data.update(
        {
            "baseurl": _read_config_value(config_data, "baseurl") or base_url,
            "identifier": identifier,
            "password": password,
            "jwt": login_result["jwt"],
        }
    )
    _write_auth_config(config, config_data)

    typer.echo(f"登录成功，token 已写入: {config}")
    raise typer.Exit(0)


@app.command("submit")
def submit_command(
    root: Path = typer.Option(Path("."), "--root", help="题目根目录，默认当前目录"),
    config: Path = typer.Option(DEFAULT_AUTH_CONFIG, "--config", help="认证配置文件，默认 auth_config.toml"),
    timeout: int = typer.Option(15, "--timeout", help="单次请求超时秒数"),
    workers: int = typer.Option(4, "--workers", help="并发线程数"),
    retries: int = typer.Option(2, "--retries", help="每次网络请求失败后的重试次数"),
    retry_delay: float = typer.Option(0.5, "--retry-delay", help="重试间隔秒数"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅解析并打印，不实际提交"),
    new: bool = typer.Option(False, "--new", help="全量新建模式：忽略已有 CSV，按自增 P pid 新建并重建 CSV"),
    success_pid_file: Path = typer.Option(Path("submitted_success_pids.csv"), "--success-pid-file", help="成功提交 pid 记录文件"),
) -> None:
    """批量提交所有包含 problem.md 的题目目录。"""
    config = config.resolve()
    try:
        base_url = _resolve_base_url(config)
    except Exception as exc:
        _error(str(exc))

    if timeout <= 0:
        _error("单次请求超时秒数必须大于 0")
    if workers <= 0:
        _error("并发线程数必须大于 0")
    if retries < 0:
        _error("重试次数不能小于 0")
    if retry_delay < 0:
        _error("重试间隔秒数不能小于 0")

    try:
        resolved_token = _resolve_token(config)
    except Exception as exc:
        _error(str(exc))

    root_data_dir = root.resolve()
    if not root_data_dir.exists() or not root_data_dir.is_dir():
        _error(f"根目录不存在或不是目录: {root_data_dir}")

    success = 0
    failed = 0
    success_pid_file = success_pid_file.resolve()
    try:
        targets = _build_submit_targets(
            root_data_dir=root_data_dir,
            success_pid_file=success_pid_file,
            new=new,
            base_url=base_url,
            resolved_token=resolved_token,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
        )
    except Exception as exc:
        _error(str(exc))

    if not targets:
        if new:
            typer.echo("未找到任何包含 problem.md 的题目目录")
        else:
            typer.echo(f"CSV 中没有可提交记录: {success_pid_file}")
        raise typer.Exit(0)

    if new:
        typer.echo(f"起始 pid: {targets[0][1]}")
        typer.echo(f"共发现 {len(targets)} 个题目目录（new 模式）")
    else:
        typer.echo(f"共发现 {len(targets)} 条 CSV 记录（update 模式）")

    if new and not dry_run:
        success_pid_file.parent.mkdir(parents=True, exist_ok=True)
        with success_pid_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["folder", "pid"])

    success_rows: list[tuple[int, str, str]] = []
    submit_labels = [pdir.name for pdir, _ in targets]
    board = _ProblemStatusBoard(submit_labels, title="Submit 状态")

    def _submit_one(idx: int, pdir: Path, assigned_pid: str) -> tuple[int, bool, str, str | None]:
        idx0 = idx - 1
        board.update(idx0, "解析题面")
        if not pdir.exists() or not pdir.is_dir():
            board.update(idx0, "失败: 目录不存在")
            return idx, False, f"[{idx}/{len(targets)}] {pdir.name} 提交失败: 目录不存在 {pdir}", None

        try:
            payload = submit_mod.build_payload(pdir)
            payload["pid"] = assigned_pid
        except Exception as exc:
            board.update(idx0, "失败: 解析题面")
            return idx, False, f"[{idx}/{len(targets)}] {pdir.name} 解析失败: {exc}", None

        if dry_run:
            board.update(idx0, "完成(dry-run)")
            return idx, True, (
                f"[{idx}/{len(targets)}] {pdir.name} 解析成功: "
                f"pid={payload['pid']}, title={payload['title']}, examples={len(payload['example'])}"
            ), None

        board.update(idx0, "提交中")
        if new:
            request_fn = lambda: submit_mod.post_problem(base_url, resolved_token, payload, timeout)
        else:
            request_fn = lambda: submit_mod.patch_problem(base_url, resolved_token, payload, timeout)
        status, body = _request_status_with_retry(
            request_fn=request_fn,
            retries=retries,
            retry_delay=retry_delay,
        )
        if 200 <= status < 300:
            board.update(idx0, f"完成 HTTP {status}")
            return idx, True, f"[{idx}/{len(targets)}] {pdir.name} 提交成功: HTTP {status}", payload["pid"]
        short_body = body.replace("\n", " ")[:300]
        board.update(idx0, f"失败 HTTP {status}")
        return idx, False, f"[{idx}/{len(targets)}] {pdir.name} 提交失败: HTTP {status} | {short_body}", None

    with board:
        futures = []
        with ThreadPoolExecutor(max_workers=min(workers, max(1, len(targets)))) as executor:
            for idx, (pdir, assigned_pid) in enumerate(targets, start=1):
                futures.append(executor.submit(_submit_one, idx, pdir, assigned_pid))
            results = [f.result() for f in as_completed(futures)]

    for idx, ok, message, success_pid in sorted(results, key=lambda x: x[0]):
        if ok:
            success += 1
            if new and not dry_run and success_pid is not None:
                success_rows.append((idx, targets[idx - 1][0].name, success_pid))
        else:
            failed += 1

    if dry_run:
        typer.echo("dry-run 完成")
        raise typer.Exit(0)

    if new:
        success_pid_file.parent.mkdir(parents=True, exist_ok=True)
        with success_pid_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["folder", "pid"])
            for _, folder, pid in sorted(success_rows, key=lambda x: x[0]):
                writer.writerow([folder, pid])

    typer.echo(f"提交结束: 成功 {success}，失败 {failed}，总计 {len(targets)}")
    raise typer.Exit(0 if failed == 0 else 1)


@app.command("delete")
def delete_command(
    config: Path = typer.Option(DEFAULT_AUTH_CONFIG, "--config", help="认证配置文件，默认 auth_config.toml"),
    pid_file: Path = typer.Option(Path("submitted_success_pids.csv"), "--pid-file", help="待删除 pid CSV 文件"),
    timeout: int = typer.Option(15, "--timeout", help="单次请求超时秒数"),
    workers: int = typer.Option(4, "--workers", help="并发线程数"),
    retries: int = typer.Option(2, "--retries", help="每次网络请求失败后的重试次数"),
    retry_delay: float = typer.Option(0.5, "--retry-delay", help="重试间隔秒数"),
    ignore_not_found: bool = typer.Option(False, "--ignore-not-found", help="将 404 视为成功"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅打印将删除的 pid，不实际调用接口"),
) -> None:
    """批量删除题目。"""
    config = config.resolve()
    try:
        base_url = _resolve_base_url(config)
    except Exception as exc:
        _error(str(exc))

    if timeout <= 0:
        _error("单次请求超时秒数必须大于 0")
    if workers <= 0:
        _error("并发线程数必须大于 0")
    if retries < 0:
        _error("重试次数不能小于 0")
    if retry_delay < 0:
        _error("重试间隔秒数不能小于 0")

    try:
        resolved_token = _resolve_token(config)
    except Exception as exc:
        if dry_run:
            resolved_token = ""
        else:
            _error(str(exc))

    pid_file = pid_file if pid_file.is_absolute() else (Path.cwd() / pid_file)
    pid_file = pid_file.resolve()
    if not pid_file.exists() or not pid_file.is_file():
        _error(f"pid 文件不存在或不是文件: {pid_file}")

    try:
        pids = _read_pids_from_csv(pid_file)
    except Exception as exc:
        _error(str(exc))

    if not pids:
        typer.echo(f"未在 pid CSV 中找到有效记录: {pid_file}")
        raise typer.Exit(0)

    typer.echo(f"共发现 {len(pids)} 个待删除 pid")

    success = 0
    failed = 0

    board = _ProblemStatusBoard(pids, title="Delete 状态")

    def _delete_one(idx: int, pid: str) -> tuple[int, bool, str]:
        idx0 = idx - 1
        if dry_run:
            board.update(idx0, "完成(dry-run)")
            return idx, True, f"[{idx}/{len(pids)}] 将删除 pid={pid}"

        board.update(idx0, "删除中")
        ok, status, body = _delete_with_retry(
            request_fn=lambda: delete_mod.delete_problem(base_url, resolved_token, pid, timeout),
            retries=retries,
            retry_delay=retry_delay,
            ignore_not_found=ignore_not_found,
        )
        if ok:
            board.update(idx0, f"完成 HTTP {status}")
            return idx, True, f"[{idx}/{len(pids)}] 删除成功 pid={pid} | HTTP {status}"
        short_body = re.sub(r"\s+", " ", body).strip()[:300]
        board.update(idx0, f"失败 HTTP {status}")
        return idx, False, f"[{idx}/{len(pids)}] 删除失败 pid={pid} | HTTP {status} | {short_body}"

    with board:
        futures = []
        with ThreadPoolExecutor(max_workers=min(workers, max(1, len(pids)))) as executor:
            for idx, pid in enumerate(pids, start=1):
                futures.append(executor.submit(_delete_one, idx, pid))
            results = [f.result() for f in as_completed(futures)]

    for _, ok, message in sorted(results, key=lambda x: x[0]):
        if ok:
            success += 1
        else:
            failed += 1

    if dry_run:
        typer.echo("dry-run 完成")
        raise typer.Exit(0)

    typer.echo(f"删除结束: 成功 {success}，失败 {failed}，总计 {len(pids)}")
    raise typer.Exit(0 if failed == 0 else 1)


@app.command("upload-data")
def upload_data_command(
    root: Path = typer.Option(Path("."), "--root", help="题目根目录，默认当前目录"),
    config: Path = typer.Option(DEFAULT_AUTH_CONFIG, "--config", help="认证配置文件，默认 auth_config.toml"),
    pid_file: Path = typer.Option(Path("submitted_success_pids.csv"), "--pid-file", help="上传用 CSV 文件，默认 submitted_success_pids.csv"),
    timeout: int = typer.Option(15, "--timeout", help="单次请求超时秒数"),
    workers: int = typer.Option(4, "--workers", help="并发线程数"),
    retries: int = typer.Option(2, "--retries", help="每次网络请求失败后的重试次数"),
    retry_delay: float = typer.Option(0.5, "--retry-delay", help="重试间隔秒数"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅检查并打印将上传的数据，不实际调用接口"),
) -> None:
    """批量上传所有题目的数据包。"""
    config = config.resolve()
    try:
        base_url = _resolve_base_url(config)
    except Exception as exc:
        _error(str(exc))

    if timeout <= 0:
        _error("单次请求超时秒数必须大于 0")
    if workers <= 0:
        _error("并发线程数必须大于 0")
    if retries < 0:
        _error("重试次数不能小于 0")
    if retry_delay < 0:
        _error("重试间隔秒数不能小于 0")

    try:
        resolved_token = _resolve_token(config)
    except Exception as exc:
        if dry_run:
            resolved_token = ""
        else:
            _error(str(exc))

    root = root.resolve()
    root_data_dir = root
    if not root_data_dir.exists() or not root_data_dir.is_dir():
        _error(f"根目录不存在或不是目录: {root_data_dir}")

    pid_file = pid_file if pid_file.is_absolute() else (Path.cwd() / pid_file)
    pid_file = pid_file.resolve()
    if not pid_file.exists() or not pid_file.is_file():
        _error(f"pid 文件不存在或不是文件: {pid_file}")

    try:
        records = delete_mod.read_pid_file(pid_file)
    except Exception as exc:
        _error(str(exc))

    if not records:
        typer.echo(f"未在 pid CSV 中找到有效记录: {pid_file}")
        raise typer.Exit(0)

    typer.echo(f"共发现 {len(records)} 个待上传数据记录")

    success = 0
    failed = 0

    with TemporaryDirectory(prefix="problem_data_upload_") as temp_dir:
        temp_root = Path(temp_dir)

        labels = [folder for folder, _ in records]
        board = _ProblemStatusBoard(labels, title="Upload-Data 状态")

        def _upload_data_one(idx: int, folder: str, pid: str) -> tuple[int, bool, str]:
            idx0 = idx - 1
            pdir = root_data_dir / folder
            data_dir = pdir / "data"

            if not pdir.exists() or not pdir.is_dir():
                board.update(idx0, "失败: 目录不存在")
                return idx, False, f"[{idx}/{len(records)}] {folder} 上传失败: 目录不存在 {pdir}"

            try:
                board.update(idx0, "打包中")
                zip_path = temp_root / f"{idx}_{pid}.zip"
                file_count = upload_mod.zip_problem_data(data_dir, zip_path)
            except Exception as exc:
                board.update(idx0, "失败: 打包")
                return idx, False, f"[{idx}/{len(records)}] {folder} 打包失败: {exc}"

            if dry_run:
                board.update(idx0, "完成(dry-run)")
                return idx, True, (
                    f"[{idx}/{len(records)}] {folder} 打包成功: "
                    f"pid={pid}, files={file_count}, zip={zip_path.name}"
                )

            board.update(idx0, "上传中")
            status, body = _request_status_with_retry(
                request_fn=lambda: upload_mod.upload_zip(
                    base_url=base_url,
                    token=resolved_token,
                    pid=pid,
                    zip_path=zip_path,
                    upload_filename=f"{pid}.zip",
                    timeout=timeout,
                ),
                retries=retries,
                retry_delay=retry_delay,
            )
            if 200 <= status < 300:
                board.update(idx0, f"完成 HTTP {status}")
                return idx, True, f"[{idx}/{len(records)}] {folder} 上传成功: HTTP {status}"
            short_body = re.sub(r"\s+", " ", body).strip()[:300]
            board.update(idx0, f"失败 HTTP {status}")
            return idx, False, f"[{idx}/{len(records)}] {folder} 上传失败: HTTP {status} | {short_body}"

        with board:
            futures = []
            with ThreadPoolExecutor(max_workers=min(workers, max(1, len(records)))) as executor:
                for idx, (folder, pid) in enumerate(records, start=1):
                    futures.append(executor.submit(_upload_data_one, idx, folder, pid))
                results = [f.result() for f in as_completed(futures)]

        for _, ok, message in sorted(results, key=lambda x: x[0]):
            if ok:
                success += 1
            else:
                failed += 1

    if dry_run:
        typer.echo("dry-run 完成")
        raise typer.Exit(0)

    typer.echo(f"上传结束: 成功 {success}，失败 {failed}，总计 {len(records)}")
    raise typer.Exit(0 if failed == 0 else 1)


@app.command("upload-config")
def upload_config_command(
    root: Path = typer.Option(Path("."), "--root", help="题目根目录，默认当前目录"),
    config: Path = typer.Option(DEFAULT_AUTH_CONFIG, "--config", help="认证配置文件，默认 auth_config.toml"),
    pid_file: Path = typer.Option(Path("submitted_success_pids.csv"), "--pid-file", help="上传用 CSV 文件，默认 submitted_success_pids.csv"),
    timeout: int = typer.Option(15, "--timeout", help="单次请求超时秒数"),
    workers: int = typer.Option(4, "--workers", help="并发线程数"),
    retries: int = typer.Option(2, "--retries", help="每次网络请求失败后的重试次数"),
    retry_delay: float = typer.Option(0.5, "--retry-delay", help="重试间隔秒数"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅解析并打印，不实际上传"),
) -> None:
    """批量上传所有题目的评测配置。"""
    config = config.resolve()
    try:
        base_url = _resolve_base_url(config)
    except Exception as exc:
        _error(str(exc))

    if timeout <= 0:
        _error("单次请求超时秒数必须大于 0")
    if workers <= 0:
        _error("并发线程数必须大于 0")
    if retries < 0:
        _error("重试次数不能小于 0")
    if retry_delay < 0:
        _error("重试间隔秒数不能小于 0")

    try:
        resolved_token = _resolve_token(config)
    except Exception as exc:
        if dry_run:
            resolved_token = ""
        else:
            _error(str(exc))

    root = root.resolve()
    root_data_dir = root
    if not root_data_dir.exists() or not root_data_dir.is_dir():
        _error(f"根目录不存在或不是目录: {root_data_dir}")

    pid_file = pid_file if pid_file.is_absolute() else (Path.cwd() / pid_file)
    pid_file = pid_file.resolve()
    if not pid_file.exists() or not pid_file.is_file():
        _error(f"pid 文件不存在或不是文件: {pid_file}")

    try:
        records = delete_mod.read_pid_file(pid_file)
    except Exception as exc:
        _error(str(exc))

    if not records:
        typer.echo(f"未在 pid CSV 中找到有效记录: {pid_file}")
        raise typer.Exit(0)

    typer.echo(f"共发现 {len(records)} 个待上传配置记录")

    success = 0
    failed = 0

    labels = [folder for folder, _ in records]
    board = _ProblemStatusBoard(labels, title="Upload-Config 状态")

    def _upload_config_one(idx: int, folder: str, pid: str) -> tuple[int, bool, str]:
        idx0 = idx - 1
        pdir = root_data_dir / folder
        if not pdir.exists() or not pdir.is_dir():
            board.update(idx0, "失败: 目录不存在")
            return idx, False, f"[{idx}/{len(records)}] {folder} 上传配置失败: 目录不存在 {pdir}"
        try:
            board.update(idx0, "解析配置")
            payload = upload_config_mod.build_config_payload(pdir)
        except Exception as exc:
            board.update(idx0, "失败: 解析配置")
            return idx, False, f"[{idx}/{len(records)}] {folder} 解析配置失败: {exc}"

        if dry_run:
            board.update(idx0, "完成(dry-run)")
            return idx, True, (
                f"[{idx}/{len(records)}] {folder} 解析成功: "
                f"pid={pid}, testcases={len(payload['testcases'])}, subtasks={len(payload['subtasks'])}"
            )

        board.update(idx0, "上传中")
        status, body = _request_status_with_retry(
            request_fn=lambda: upload_config_mod.put_problem_config(
                base_url=base_url,
                token=resolved_token,
                pid=pid,
                payload=payload,
                timeout=timeout,
            ),
            retries=retries,
            retry_delay=retry_delay,
        )
        if 200 <= status < 300:
            board.update(idx0, f"完成 HTTP {status}")
            return idx, True, f"[{idx}/{len(records)}] {folder} 上传配置成功: HTTP {status}"
        short_body = re.sub(r"\s+", " ", body).strip()[:300]
        board.update(idx0, f"失败 HTTP {status}")
        return idx, False, f"[{idx}/{len(records)}] {folder} 上传配置失败: HTTP {status} | {short_body}"

    with board:
        futures = []
        with ThreadPoolExecutor(max_workers=min(workers, max(1, len(records)))) as executor:
            for idx, (folder, pid) in enumerate(records, start=1):
                futures.append(executor.submit(_upload_config_one, idx, folder, pid))
            results = [f.result() for f in as_completed(futures)]

    for _, ok, message in sorted(results, key=lambda x: x[0]):
        if ok:
            success += 1
        else:
            failed += 1

    if dry_run:
        typer.echo("dry-run 完成")
        raise typer.Exit(0)

    typer.echo(f"上传配置结束: 成功 {success}，失败 {failed}，总计 {len(records)}")
    raise typer.Exit(0 if failed == 0 else 1)


@app.command("run")
def run_command(
    root: Path = typer.Option(Path("."), "--root", help="题目根目录，默认当前目录"),
    config: Path = typer.Option(DEFAULT_AUTH_CONFIG, "--config", help="认证配置文件，默认 auth_config.toml"),
    pid_file: Path = typer.Option(Path("submitted_success_pids.csv"), "--pid-file", help="提交成功 CSV 文件路径"),
    timeout: int = typer.Option(15, "--timeout", help="单次请求超时秒数"),
    workers: int = typer.Option(4, "--workers", help="并发线程数"),
    retries: int = typer.Option(2, "--retries", help="每次网络请求失败后的重试次数"),
    retry_delay: float = typer.Option(0.5, "--retry-delay", help="重试间隔秒数"),
    new: bool = typer.Option(False, "--new", help="全量新建模式：忽略已有 CSV，按自增 P pid 新建并重建 CSV"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅演练流程，不实际提交/上传"),
) -> None:
    """一键执行：登录后并发处理题目（每题按 提交 -> 上传数据 -> 上传评测配置 顺序）。"""
    if timeout <= 0:
        _error("单次请求超时秒数必须大于 0")
    if workers <= 0:
        _error("并发线程数必须大于 0")
    if retries < 0:
        _error("重试次数不能小于 0")
    if retry_delay < 0:
        _error("重试间隔秒数不能小于 0")

    root_data_dir = root.resolve()
    if not root_data_dir.exists() or not root_data_dir.is_dir():
        _error(f"根目录不存在或不是目录: {root_data_dir}")
    config = config.resolve()
    pid_file = pid_file if pid_file.is_absolute() else (Path.cwd() / pid_file)
    pid_file = pid_file.resolve()

    typer.echo("[开始] 登录")
    try:
        login_command(config=config, timeout=timeout, retries=retries, retry_delay=retry_delay, dry_run=dry_run)
    except typer.Exit as exc:
        exit_code = exc.exit_code if exc.exit_code is not None else 0
        if exit_code != 0:
            typer.echo(f"[失败] 登录，退出码 {exit_code}", err=True)
            raise typer.Exit(exit_code)
    typer.echo("[完成] 登录")

    try:
        base_url = _resolve_base_url(config)
        resolved_token = _resolve_token(config) if not dry_run else ""
    except Exception as exc:
        _error(str(exc))

    try:
        targets = _build_submit_targets(
            root_data_dir=root_data_dir,
            success_pid_file=pid_file,
            new=new,
            base_url=base_url,
            resolved_token=resolved_token,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
        )
    except Exception as exc:
        _error(str(exc))

    if not targets:
        if new:
            typer.echo("未找到任何包含 problem.md 的题目目录")
        else:
            typer.echo(f"CSV 中没有可处理记录: {pid_file}")
        raise typer.Exit(0)

    if new:
        typer.echo(f"起始 pid: {targets[0][1]}")
        if not dry_run:
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            with pid_file.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["folder", "pid"])
    typer.echo(f"共需并发处理 {len(targets)} 题")

    success = 0
    failed = 0
    success_rows: list[tuple[int, str, str]] = []
    labels = [pdir.name for pdir, _ in targets]
    board = _ProblemStatusBoard(labels, title="Run 状态")
    with TemporaryDirectory(prefix="problem_run_upload_") as temp_dir:
        temp_root = Path(temp_dir)
        def _run_one(idx: int, pdir: Path, pid: str) -> tuple[int, bool, str]:
            idx0 = idx - 1
            folder = pdir.name
            if not pdir.exists() or not pdir.is_dir():
                board.update(idx0, "失败: 目录不存在")
                return idx, False, f"[{idx}/{len(targets)}] {folder} 失败: 目录不存在 {pdir}"

            try:
                board.update(idx0, "解析题面")
                submit_payload = submit_mod.build_payload(pdir)
                submit_payload["pid"] = pid
            except Exception as exc:
                board.update(idx0, "失败: 解析题面")
                return idx, False, f"[{idx}/{len(targets)}] {folder} 失败: 解析题面失败 {exc}"

            data_dir = pdir / "data"
            try:
                board.update(idx0, "打包数据")
                zip_path = temp_root / f"{idx}_{pid}.zip"
                file_count = upload_mod.zip_problem_data(data_dir, zip_path)
            except Exception as exc:
                board.update(idx0, "失败: 打包数据")
                return idx, False, f"[{idx}/{len(targets)}] {folder} 失败: 打包数据失败 {exc}"

            try:
                board.update(idx0, "解析配置")
                config_payload = upload_config_mod.build_config_payload(pdir)
            except Exception as exc:
                board.update(idx0, "失败: 解析配置")
                return idx, False, f"[{idx}/{len(targets)}] {folder} 失败: 解析评测配置失败 {exc}"

            if dry_run:
                board.update(idx0, "完成(dry-run)")
                return idx, True, (
                    f"[{idx}/{len(targets)}] {folder} dry-run: "
                    f"pid={pid}, examples={len(submit_payload['example'])}, files={file_count}, "
                    f"testcases={len(config_payload['testcases'])}, subtasks={len(config_payload['subtasks'])}"
                )

            board.update(idx0, "提交题目")
            submit_status, submit_body = _request_status_with_retry(
                request_fn=(
                    (lambda: submit_mod.post_problem(base_url, resolved_token, submit_payload, timeout))
                    if new
                    else (lambda: submit_mod.patch_problem(base_url, resolved_token, submit_payload, timeout))
                ),
                retries=retries,
                retry_delay=retry_delay,
            )
            if not (200 <= submit_status < 300):
                short_body = submit_body.replace("\n", " ")[:300]
                board.update(idx0, f"失败: 提交 HTTP {submit_status}")
                return idx, False, f"[{idx}/{len(targets)}] {folder} 失败: 提交题目 HTTP {submit_status} | {short_body}"

            board.update(idx0, "上传数据")
            data_status, data_body = _request_status_with_retry(
                request_fn=lambda: upload_mod.upload_zip(
                    base_url=base_url,
                    token=resolved_token,
                    pid=pid,
                    zip_path=zip_path,
                    upload_filename=f"{pid}.zip",
                    timeout=timeout,
                ),
                retries=retries,
                retry_delay=retry_delay,
            )
            if not (200 <= data_status < 300):
                short_body = re.sub(r"\s+", " ", data_body).strip()[:300]
                board.update(idx0, f"失败: 数据 HTTP {data_status}")
                return idx, False, f"[{idx}/{len(targets)}] {folder} 失败: 上传数据 HTTP {data_status} | {short_body}"

            board.update(idx0, "上传配置")
            config_status, config_body = _request_status_with_retry(
                request_fn=lambda: upload_config_mod.put_problem_config(
                    base_url=base_url,
                    token=resolved_token,
                    pid=pid,
                    payload=config_payload,
                    timeout=timeout,
                ),
                retries=retries,
                retry_delay=retry_delay,
            )
            if not (200 <= config_status < 300):
                short_body = re.sub(r"\s+", " ", config_body).strip()[:300]
                board.update(idx0, f"失败: 配置 HTTP {config_status}")
                return idx, False, f"[{idx}/{len(targets)}] {folder} 失败: 上传配置 HTTP {config_status} | {short_body}"
            board.update(idx0, "完成")
            return idx, True, f"[{idx}/{len(targets)}] {folder} 完成: pid={pid}"

        with board:
            futures = []
            with ThreadPoolExecutor(max_workers=min(workers, max(1, len(targets)))) as executor:
                for idx, (pdir, pid) in enumerate(targets, start=1):
                    futures.append(executor.submit(_run_one, idx, pdir, pid))
                results = [f.result() for f in as_completed(futures)]

        for idx, ok, message in sorted(results, key=lambda x: x[0]):
            if ok:
                success += 1
                if new and not dry_run:
                    folder = targets[idx - 1][0].name
                    pid = targets[idx - 1][1]
                    success_rows.append((idx, folder, pid))
            else:
                failed += 1

    if dry_run:
        typer.echo("dry-run 完成")
        raise typer.Exit(0)

    if new:
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        with pid_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["folder", "pid"])
            for _, folder, pid in sorted(success_rows, key=lambda x: x[0]):
                writer.writerow([folder, pid])

    typer.echo(f"全部步骤执行结束: 成功 {success}，失败 {failed}，总计 {len(targets)}")
    raise typer.Exit(0 if failed == 0 else 1)


def main() -> None:
    """程序主入口。"""
    app()


if __name__ == "__main__":
    main()
