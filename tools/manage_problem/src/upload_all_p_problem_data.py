#!/usr/bin/env python3
"""批量上传所有 P 开头题目的数据包（当前仅支持 zip）。"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
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


def build_multipart_body(zip_path: Path, file_name: str, file_field: str, format_field: str) -> Tuple[str, bytes]:
    """构建 multipart/form-data 请求体。"""
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    with zip_path.open("rb") as f:
        file_bytes = f.read()

    head = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"{file_field}\"; filename=\"{file_name}\"\r\n"
        f"Content-Type: application/zip\r\n\r\n"
    ).encode("utf-8")

    middle = (
        f"\r\n--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"{format_field}\"\r\n\r\n"
        f"zip"
    ).encode("utf-8")

    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = head + file_bytes + middle + tail
    content_type = f"multipart/form-data; boundary={boundary}"
    return content_type, body


def zip_problem_data(problem_data_dir: Path, output_zip: Path) -> int:
    """将题目 data 目录打包为 zip，并返回打包文件数。"""
    if not problem_data_dir.exists() or not problem_data_dir.is_dir():
        raise FileNotFoundError(f"数据目录不存在: {problem_data_dir}")

    files: List[Path] = []
    for path in sorted(problem_data_dir.rglob("*")):
        if path.is_file():
            files.append(path)

    if not files:
        raise ValueError(f"数据目录为空: {problem_data_dir}")

    with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            arcname = path.relative_to(problem_data_dir).as_posix()
            zf.write(path, arcname=arcname)

    return len(files)


def upload_zip(
    base_url: str,
    token: str,
    pid: str,
    zip_path: Path,
    upload_filename: str,
    timeout: int,
) -> Tuple[int, str]:
    """上传 zip 数据包并返回状态码和响应文本。"""
    base_api = base_url.rstrip("/") + "/api/problem/data"
    url = f"{base_api}/{urllib.parse.quote(pid)}"
    content_type, body = build_multipart_body(
        zip_path=zip_path,
        file_name=upload_filename,
        file_field="file",
        format_field="format",
    )

    req = urllib.request.Request(url=url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", content_type)

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


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="批量上传所有 P 开头题目数据（仅 zip）")
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
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="单次请求超时秒数，默认 15",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅检查并打印将上传的数据，不实际调用接口",
    )

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

    print(f"共发现 {len(records)} 个待上传数据记录")

    success = 0
    failed = 0

    with TemporaryDirectory(prefix="problem_data_upload_") as temp_dir:
        temp_root = Path(temp_dir)

        for idx, (folder, pid) in enumerate(records, start=1):
            pdir = root_data_dir / folder
            data_dir = pdir / "data"

            if not pdir.exists() or not pdir.is_dir():
                failed += 1
                print(f"[{idx}/{len(records)}] {folder} 上传失败: 目录不存在 {pdir}")
                continue

            try:
                zip_path = temp_root / f"{pid}.zip"
                file_count = zip_problem_data(data_dir, zip_path)
            except Exception as exc:
                failed += 1
                print(f"[{idx}/{len(records)}] {folder} 打包失败: {exc}")
                continue

            if args.dry_run:
                print(
                    f"[{idx}/{len(records)}] {folder} 打包成功: "
                    f"pid={pid}, files={file_count}, zip={zip_path.name}"
                )
                continue

            status, body = upload_zip(
                base_url=args.base_url,
                token=args.token,
                pid=pid,
                zip_path=zip_path,
                upload_filename=f"{pid}.zip",
                timeout=args.timeout,
            )

            if status == 0:
                failed += 1
                print(f"[{idx}/{len(records)}] {folder} 上传失败: {body}")
                print("检测到服务不可达，提前终止后续上传。请先确认后端服务已启动。")
                failed += len(records) - idx
                break

            if 200 <= status < 300:
                success += 1
                print(f"[{idx}/{len(records)}] {folder} 上传成功: HTTP {status}")
            else:
                failed += 1
                short_body = re.sub(r"\s+", " ", body).strip()[:300]
                print(
                    f"[{idx}/{len(records)}] {folder} 上传失败: "
                    f"HTTP {status} | {short_body}"
                )

    if args.dry_run:
        print("dry-run 完成")
        return 0

    print(f"上传结束: 成功 {success}，失败 {failed}，总计 {len(records)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
