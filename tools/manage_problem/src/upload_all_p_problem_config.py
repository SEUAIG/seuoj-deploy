#!/usr/bin/env python3
"""批量上传所有 P 开头题目的评测配置。"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple


def parse_front_matter(text: str) -> Dict[str, str]:
    """解析 problem.md 顶部的 YAML front matter。"""
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return {}

    data: Dict[str, str] = {}
    for line in lines[1:end_idx]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data


def extract_pid(problem_dir: Path) -> str:
    """优先从 problem.md front matter 读取 pid，否则回退目录名。"""
    problem_md = problem_dir / "problem.md"
    if problem_md.exists():
        content = problem_md.read_text(encoding="utf-8")
        front = parse_front_matter(content)
        pid = (front.get("pid") or "").strip()
        if pid:
            return pid.upper()
    return problem_dir.name.upper()


def find_problem_dirs(root: Path) -> List[Path]:
    """查找所有以 P/p 开头且包含 problem.md 的目录。"""
    dirs: List[Path] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if not child.name.lower().startswith("p"):
            continue
        if (child / "problem.md").exists():
            dirs.append(child)
    return dirs


def read_pid_file(pid_file: Path) -> List[Tuple[str, str]]:
    """读取上传 CSV，返回 (文件夹名, pid) 列表。"""
    if not pid_file.exists() or not pid_file.is_file():
        raise FileNotFoundError(f"pid 文件不存在或不是文件: {pid_file}")

    records: List[Tuple[str, str]] = []
    with pid_file.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"pid CSV 缺少表头: {pid_file}")
        expected = {"folder", "pid"}
        actual = {name.strip() for name in reader.fieldnames if name}
        if actual != expected:
            raise ValueError(f"pid CSV 表头必须为 folder,pid，当前为: {','.join(reader.fieldnames)}")

        for row in reader:
            folder = (row.get("folder") or "").strip()
            pid = (row.get("pid") or "").strip().upper()
            if not folder or not pid:
                raise ValueError(f"pid CSV 中存在空值行: {row}")
            if not re.fullmatch(r"[A-Z][A-Z0-9]{1,19}", pid):
                raise ValueError(f"pid CSV 中存在非法 pid: {pid}")
            records.append((folder, pid))
    return records


def _to_int(value: object, default: int = 0) -> int:
    """将任意值尽量转换为 int。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    """将任意值尽量转换为 float。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_config_payload(problem_dir: Path) -> Dict:
    """从 info.toml 构造上传题目配置接口所需 JSON。"""
    info_toml = problem_dir / "info.toml"
    if not info_toml.exists() or not info_toml.is_file():
        raise FileNotFoundError(f"缺少配置文件: {info_toml}")

    with info_toml.open("rb") as f:
        raw = tomllib.load(f)

    problem_info_raw = raw.get("problem_info")
    if not isinstance(problem_info_raw, dict):
        raise ValueError(f"problem_info 缺失或格式错误: {info_toml}")

    problem_info = {
        "problem_type": str(problem_info_raw.get("problem_type") or "standard").strip().lower(),
        "checker_type": str(problem_info_raw.get("checker_type") or "standard").strip().lower(),
        "time_limit_ms": _to_int(problem_info_raw.get("time_limit_ms"), 0),
        "memory_limit_kb": _to_int(problem_info_raw.get("memory_limit_kb"), 0),
    }

    testcases: List[Dict] = []
    testcases_raw = raw.get("testcases")
    if isinstance(testcases_raw, list):
        for index, case in enumerate(testcases_raw, start=1):
            if not isinstance(case, dict):
                continue
            testcases.append(
                {
                    "id": _to_int(case.get("id"), index),
                    "in_path": str(case.get("in_path") or "").strip(),
                    "ans_path": str(case.get("ans_path") or "").strip(),
                    "weight": _to_int(case.get("weight"), 1),
                }
            )

    subtasks: List[Dict] = []
    subtasks_raw = raw.get("subtasks")
    if isinstance(subtasks_raw, list):
        for index, subtask in enumerate(subtasks_raw, start=1):
            if not isinstance(subtask, dict):
                continue
            cases_raw = subtask.get("cases")
            pre_subtasks_raw = subtask.get("pre_subtasks")
            cases = [
                _to_int(x)
                for x in (cases_raw if isinstance(cases_raw, list) else [])
            ]
            pre_subtasks = [
                _to_int(x)
                for x in (pre_subtasks_raw if isinstance(pre_subtasks_raw, list) else [])
            ]
            subtasks.append(
                {
                    "id": _to_int(subtask.get("id"), index),
                    "cases": cases,
                    "pre_subtasks": pre_subtasks,
                    "score": _to_int(subtask.get("score"), 0),
                    "type": str(subtask.get("type") or "min").strip().lower(),
                }
            )

    custom_modules_raw = raw.get("custom_modules")
    custom_modules = {
        "checker_path": "",
        "interactor_path": "",
    }
    if isinstance(custom_modules_raw, dict):
        custom_modules["checker_path"] = str(custom_modules_raw.get("checker_path") or "").strip()
        custom_modules["interactor_path"] = str(custom_modules_raw.get("interactor_path") or "").strip()

    return {
        "problem_info": problem_info,
        "testcases": testcases,
        "subtasks": subtasks,
        "custom_modules": custom_modules,
    }


def put_problem_config(base_url: str, token: str, pid: str, payload: Dict, timeout: int) -> Tuple[int, str]:
    """调用接口上传单题配置并返回状态码与响应文本。"""
    base_api = base_url.rstrip("/") + "/api/problem/config"
    url = f"{base_api}/{urllib.parse.quote(pid)}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url=url, data=data, method="PUT")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        return err.code, body
    except urllib.error.URLError as err:
        return 0, f"网络错误: {err.reason}"
    except TimeoutError:
        return 0, "网络错误: 请求超时"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="批量上传所有 P 开头题目配置")
    parser.add_argument("--root", default=".", help="题目根目录，默认当前目录")
    parser.add_argument(
        "--pid-file",
        default="submitted_success_pids.csv",
        help="上传用 pid CSV 文件，默认 submitted_success_pids.csv",
    )
    parser.add_argument(
        "--base-url",
        default="http://10.210.55.111:2280",
        help="服务地址，默认 http://10.210.55.111:2280",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("PROBLEM_API_TOKEN", ""),
        help="Bearer Token；未传时读取环境变量 PROBLEM_API_TOKEN",
    )
    parser.add_argument("--timeout", type=int, default=15, help="单次请求超时秒数，默认 15")
    parser.add_argument("--dry-run", action="store_true", help="仅解析并打印，不实际上传")

    args = parser.parse_args(argv)

    if not args.dry_run and not args.token:
        print("错误: 缺少 token。请使用 --token 或设置 PROBLEM_API_TOKEN", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    root_data_dir = (root / "data").resolve()
    if not root_data_dir.exists() or not root_data_dir.is_dir():
        print(f"错误: 根目录不存在或不是目录: {root_data_dir}", file=sys.stderr)
        return 2

    pid_file = Path(args.pid_file)
    if not pid_file.is_absolute():
        pid_file = (root / pid_file).resolve()

    try:
        records = read_pid_file(pid_file)
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2

    if not records:
        print(f"未在 pid CSV 中找到有效记录: {pid_file}")
        return 0

    print(f"共发现 {len(records)} 个待上传配置记录")

    success = 0
    failed = 0

    for idx, (folder, pid) in enumerate(records, start=1):
        pdir = root_data_dir / folder
        if not pdir.exists() or not pdir.is_dir():
            failed += 1
            print(f"[{idx}/{len(records)}] {folder} 上传配置失败: 目录不存在 {pdir}")
            continue
        try:
            payload = build_config_payload(pdir)
        except Exception as exc:
            failed += 1
            print(f"[{idx}/{len(records)}] {folder} 解析配置失败: {exc}")
            continue

        if args.dry_run:
            print(
                f"[{idx}/{len(records)}] {folder} 解析成功: "
                f"pid={pid}, testcases={len(payload['testcases'])}, subtasks={len(payload['subtasks'])}"
            )
            continue

        status, body = put_problem_config(args.base_url, args.token, pid, payload, args.timeout)

        if status == 0:
            failed += 1
            print(f"[{idx}/{len(records)}] {folder} 上传配置失败: {body}")
            print("检测到服务不可达，提前终止后续上传。请先确认后端服务已启动。")
            failed += len(records) - idx
            break

        if 200 <= status < 300:
            success += 1
            print(f"[{idx}/{len(records)}] {folder} 上传配置成功: HTTP {status}")
        else:
            failed += 1
            short_body = re.sub(r"\s+", " ", body).strip()[:300]
            print(f"[{idx}/{len(records)}] {folder} 上传配置失败: HTTP {status} | {short_body}")

    if args.dry_run:
        print("dry-run 完成")
        return 0

    print(f"上传配置结束: 成功 {success}，失败 {failed}，总计 {len(records)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
