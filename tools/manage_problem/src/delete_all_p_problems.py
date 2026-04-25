#!/usr/bin/env python3
"""批量删除所有 P 开头题目的脚本。"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
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
    """读取待删除 CSV，返回 (文件夹名, pid) 列表。"""
    if not pid_file.exists() or not pid_file.is_file():
        raise FileNotFoundError(f"pid 文件不存在或不是文件: {pid_file}")

    records: List[Tuple[str, str]] = []
    content = pid_file.read_text(encoding="utf-8")
    # 兼容历史损坏文件: 首行可能是 "folder,pid" 与第一条记录粘连。
    if content.startswith("folder,pid") and not (
        content.startswith("folder,pid\n") or content.startswith("folder,pid\r\n")
    ):
        content = content.replace("folder,pid", "folder,pid\n", 1)

    reader = csv.DictReader(io.StringIO(content))
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


def send_delete_request(url: str, token: str, timeout: int) -> Tuple[int, str]:
    """发送 DELETE 请求并返回状态码与响应文本。

    约定: status=0 表示请求未发到服务端（如连接拒绝/超时/DNS 失败）。
    """
    data = None
    req = None
    req = urllib.request.Request(url=url, data=data, method="DELETE")
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_body = resp.read().decode("utf-8", errors="replace")
            return resp.status, resp_body
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8", errors="replace")
        return err.code, err_body
    except urllib.error.URLError as err:
        return 0, f"网络错误: {err.reason}"
    except TimeoutError:
        return 0, "网络错误: 请求超时"


def delete_problem(base_url: str, token: str, pid: str, timeout: int) -> Tuple[bool, int, str]:
    """按固定路径 /api/problem/{pid} 删除题目。

    返回: (是否成功, 状态码, 响应内容)
    """
    base_api = base_url.rstrip("/") + "/api/problem"
    url = f"{base_api}/{urllib.parse.quote(pid)}"
    status, body = send_delete_request(url, token, timeout)
    return 200 <= status < 300, status, body


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="批量删除所有 P 开头题目")
    parser.add_argument("--root", default=".", help="题目根目录，默认当前目录")
    parser.add_argument(
        "--pid-file",
        default="submitted_success_pids.csv",
        help="待删除 pid CSV 文件，默认 submitted_success_pids.csv",
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
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="单次请求超时秒数，默认 15",
    )
    parser.add_argument(
        "--ignore-not-found",
        action="store_true",
        help="将 404 视为成功（幂等删除场景）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印将删除的 pid，不实际调用接口",
    )

    args = parser.parse_args(argv)

    if not args.dry_run and not args.token:
        print("错误: 缺少 token。请使用 --token 或设置 PROBLEM_API_TOKEN", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
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

    print(f"共发现 {len(records)} 个待删除记录")

    success = 0
    failed = 0

    for idx, (folder, pid) in enumerate(records, start=1):
        if args.dry_run:
            print(f"[{idx}/{len(records)}] 将删除 folder={folder} pid={pid}")
            continue

        ok, status, body = delete_problem(
            base_url=args.base_url,
            token=args.token,
            pid=pid,
            timeout=args.timeout,
        )

        if status == 0:
            failed += 1
            print(f"[{idx}/{len(records)}] 删除失败 folder={folder} pid={pid} | {body}")
            print("检测到服务不可达，提前终止后续删除。请先确认后端服务已启动。")
            failed += len(records) - idx
            break

        if not ok and args.ignore_not_found and status == 404:
            ok = True

        if ok:
            success += 1
            print(f"[{idx}/{len(records)}] 删除成功 folder={folder} pid={pid} | HTTP {status}")
        else:
            failed += 1
            short_body = re.sub(r"\s+", " ", body).strip()[:300]
            print(
                f"[{idx}/{len(records)}] 删除失败 folder={folder} pid={pid} | HTTP {status} | {short_body}"
            )

    if args.dry_run:
        print("dry-run 完成")
        return 0

    print(f"删除结束: 成功 {success}，失败 {failed}，总计 {len(records)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
