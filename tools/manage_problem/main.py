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
from pathlib import Path
from tempfile import TemporaryDirectory

import typer

import src.delete_all_p_problems as delete_mod
import src.submit_all_p_problems as submit_mod
import src.upload_all_p_problem_config as upload_config_mod
import src.upload_all_p_problem_data as upload_mod


DEFAULT_AUTH_CONFIG = Path("auth_config.toml")

app = typer.Typer(
    help="题目批量工具：支持 login、submit、delete、upload-data、upload-config 子命令",
    add_completion=False,
)


def _error(message: str) -> None:
    """输出错误并以 2 退出。"""
    typer.echo(f"错误: {message}", err=True)
    raise typer.Exit(2)


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


@app.command("login")
def login_command(
    config: Path = typer.Option(DEFAULT_AUTH_CONFIG, "--config", help="认证配置文件，默认 auth_config.toml"),
    timeout: int = typer.Option(15, "--timeout", help="单次请求超时秒数"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅检查配置，不实际登录"),
) -> None:
    """使用配置文件里的邮箱和密码登录，并把 jwt 写回配置文件。"""
    if timeout <= 0:
        _error("单次请求超时秒数必须大于 0")

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
        login_result = _login_request(base_url, identifier, password, timeout)
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
    targets: list[tuple[Path, str]] = []

    if new:
        problem_dirs = submit_mod.find_problem_dirs(root_data_dir)
        if not problem_dirs:
            typer.echo("未找到任何包含 problem.md 的题目目录")
            raise typer.Exit(0)

        try:
            current_pid = submit_mod.fetch_next_pid(base_url, resolved_token, timeout)
            current_pid = submit_mod.normalize_p_pid(current_pid)
        except Exception as exc:
            _error(str(exc))

        typer.echo(f"起始 pid: {current_pid}")
        typer.echo(f"共发现 {len(problem_dirs)} 个题目目录（new 模式）")

        for pdir in problem_dirs:
            targets.append((pdir, current_pid))
            current_pid = submit_mod.increment_pid(current_pid)

        if not dry_run:
            success_pid_file.parent.mkdir(parents=True, exist_ok=True)
            with success_pid_file.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["folder", "pid"])
    else:
        if not success_pid_file.exists() or not success_pid_file.is_file():
            _error(f"update 模式需要已有 CSV 文件: {success_pid_file}；如需全量新建请加 --new")
        try:
            records = delete_mod.read_pid_file(success_pid_file)
        except Exception as exc:
            _error(str(exc))
        if not records:
            typer.echo(f"CSV 中没有可提交记录: {success_pid_file}")
            raise typer.Exit(0)
        typer.echo(f"共发现 {len(records)} 条 CSV 记录（update 模式）")
        for folder, pid in records:
            pdir = root_data_dir / folder
            targets.append((pdir, submit_mod.normalize_p_pid(pid)))

    for idx, (pdir, assigned_pid) in enumerate(targets, start=1):
        if not pdir.exists() or not pdir.is_dir():
            failed += 1
            typer.echo(f"[{idx}/{len(targets)}] {pdir.name} 提交失败: 目录不存在 {pdir}")
            continue

        try:
            payload = submit_mod.build_payload(pdir)
            payload["pid"] = assigned_pid
        except Exception as exc:
            failed += 1
            typer.echo(f"[{idx}/{len(targets)}] {pdir.name} 解析失败: {exc}")
            continue

        if dry_run:
            typer.echo(
                f"[{idx}/{len(targets)}] {pdir.name} 解析成功: "
                f"pid={payload['pid']}, title={payload['title']}, examples={len(payload['example'])}"
            )
            continue

        status, body = submit_mod.post_problem(base_url, resolved_token, payload, timeout)
        if 200 <= status < 300:
            success += 1
            typer.echo(f"[{idx}/{len(targets)}] {pdir.name} 提交成功: HTTP {status}")
            if new:
                submit_mod.append_success_pid(success_pid_file, pdir.name, payload["pid"])
        else:
            failed += 1
            short_body = body.replace("\n", " ")[:300]
            typer.echo(f"[{idx}/{len(targets)}] {pdir.name} 提交失败: HTTP {status} | {short_body}")

    if dry_run:
        typer.echo("dry-run 完成")
        raise typer.Exit(0)

    typer.echo(f"提交结束: 成功 {success}，失败 {failed}，总计 {len(targets)}")
    raise typer.Exit(0 if failed == 0 else 1)


@app.command("delete")
def delete_command(
    config: Path = typer.Option(DEFAULT_AUTH_CONFIG, "--config", help="认证配置文件，默认 auth_config.toml"),
    pid_file: Path = typer.Option(Path("submitted_success_pids.csv"), "--pid-file", help="待删除 pid CSV 文件"),
    timeout: int = typer.Option(15, "--timeout", help="单次请求超时秒数"),
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

    for idx, pid in enumerate(pids, start=1):
        if dry_run:
            typer.echo(f"[{idx}/{len(pids)}] 将删除 pid={pid}")
            continue

        ok, status, body = delete_mod.delete_problem(base_url, resolved_token, pid, timeout)

        if status == 0:
            failed += 1
            typer.echo(f"[{idx}/{len(pids)}] 删除失败 pid={pid} | {body}")
            typer.echo("检测到服务不可达，提前终止后续删除。请先确认后端服务已启动。")
            failed += len(pids) - idx
            break

        if not ok and ignore_not_found and status == 404:
            ok = True

        if ok:
            success += 1
            typer.echo(f"[{idx}/{len(pids)}] 删除成功 pid={pid} | HTTP {status}")
        else:
            failed += 1
            short_body = re.sub(r"\s+", " ", body).strip()[:300]
            typer.echo(f"[{idx}/{len(pids)}] 删除失败 pid={pid} | HTTP {status} | {short_body}")

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

        for idx, (folder, pid) in enumerate(records, start=1):
            pdir = root_data_dir / folder
            data_dir = pdir / "data"

            if not pdir.exists() or not pdir.is_dir():
                failed += 1
                typer.echo(f"[{idx}/{len(records)}] {folder} 上传失败: 目录不存在 {pdir}")
                continue

            try:
                zip_path = temp_root / f"{pid}.zip"
                file_count = upload_mod.zip_problem_data(data_dir, zip_path)
            except Exception as exc:
                failed += 1
                typer.echo(f"[{idx}/{len(records)}] {folder} 打包失败: {exc}")
                continue

            if dry_run:
                typer.echo(
                    f"[{idx}/{len(records)}] {folder} 打包成功: "
                    f"pid={pid}, files={file_count}, zip={zip_path.name}"
                )
                continue

            status, body = upload_mod.upload_zip(
                base_url=base_url,
                token=resolved_token,
                pid=pid,
                zip_path=zip_path,
                upload_filename=f"{pid}.zip",
                timeout=timeout,
            )

            if status == 0:
                failed += 1
                typer.echo(f"[{idx}/{len(records)}] {folder} 上传失败: {body}")
                typer.echo("检测到服务不可达，提前终止后续上传。请先确认后端服务已启动。")
                failed += len(records) - idx
                break

            if 200 <= status < 300:
                success += 1
                typer.echo(f"[{idx}/{len(records)}] {folder} 上传成功: HTTP {status}")
            else:
                failed += 1
                short_body = re.sub(r"\s+", " ", body).strip()[:300]
                typer.echo(
                    f"[{idx}/{len(records)}] {folder} 上传失败: HTTP {status} | {short_body}"
                )

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

    for idx, (folder, pid) in enumerate(records, start=1):
        pdir = root_data_dir / folder
        if not pdir.exists() or not pdir.is_dir():
            failed += 1
            typer.echo(f"[{idx}/{len(records)}] {folder} 上传配置失败: 目录不存在 {pdir}")
            continue
        try:
            payload = upload_config_mod.build_config_payload(pdir)
        except Exception as exc:
            failed += 1
            typer.echo(f"[{idx}/{len(records)}] {folder} 解析配置失败: {exc}")
            continue

        if dry_run:
            typer.echo(
                f"[{idx}/{len(records)}] {folder} 解析成功: "
                f"pid={pid}, testcases={len(payload['testcases'])}, subtasks={len(payload['subtasks'])}"
            )
            continue

        status, body = upload_config_mod.put_problem_config(
            base_url=base_url,
            token=resolved_token,
            pid=pid,
            payload=payload,
            timeout=timeout,
        )

        if status == 0:
            failed += 1
            typer.echo(f"[{idx}/{len(records)}] {folder} 上传配置失败: {body}")
            typer.echo("检测到服务不可达，提前终止后续上传。请先确认后端服务已启动。")
            failed += len(records) - idx
            break

        if 200 <= status < 300:
            success += 1
            typer.echo(f"[{idx}/{len(records)}] {folder} 上传配置成功: HTTP {status}")
        else:
            failed += 1
            short_body = re.sub(r"\s+", " ", body).strip()[:300]
            typer.echo(
                f"[{idx}/{len(records)}] {folder} 上传配置失败: HTTP {status} | {short_body}"
            )

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
    dry_run: bool = typer.Option(False, "--dry-run", help="仅演练流程，不实际提交/上传"),
) -> None:
    """一键执行：登录 -> 上传题目信息 -> 上传数据 -> 上传评测配置。"""
    if timeout <= 0:
        _error("单次请求超时秒数必须大于 0")

    def _run_step(step_name: str, func, **kwargs) -> None:
        typer.echo(f"[开始] {step_name}")
        try:
            func(**kwargs)
        except typer.Exit as exc:
            exit_code = exc.exit_code if exc.exit_code is not None else 0
            if exit_code != 0:
                typer.echo(f"[失败] {step_name}，退出码 {exit_code}", err=True)
                raise typer.Exit(exit_code)
        typer.echo(f"[完成] {step_name}")

    _run_step(
        "登录",
        login_command,
        config=config,
        timeout=timeout,
        dry_run=dry_run,
    )

    _run_step(
        "上传题目信息",
        submit_command,
        root=root,
        config=config,
        timeout=timeout,
        dry_run=dry_run,
        success_pid_file=pid_file,
    )

    _run_step(
        "上传题目数据",
        upload_data_command,
        root=root,
        config=config,
        pid_file=pid_file,
        timeout=timeout,
        dry_run=dry_run,
    )

    _run_step(
        "上传评测配置",
        upload_config_command,
        root=root,
        config=config,
        pid_file=pid_file,
        timeout=timeout,
        dry_run=dry_run,
    )

    typer.echo("全部步骤执行完成。")
    raise typer.Exit(0)


def main() -> None:
    """程序主入口。"""
    app()


if __name__ == "__main__":
    main()
