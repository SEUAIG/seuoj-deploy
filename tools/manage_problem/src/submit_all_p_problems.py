#!/usr/bin/env python3
"""批量提交所有包含 problem.md 的题目目录。"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
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


def parse_level2_sections(text: str) -> Dict[str, str]:
    """按二级标题（##）拆分文档内容。"""
    # 去掉 front matter，避免干扰。
    text_wo_front = re.sub(r"\A---\n.*?\n---\n?", "", text, flags=re.S)
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text_wo_front, flags=re.M))
    sections: Dict[str, str] = {}

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text_wo_front)
        content = text_wo_front[start:end].strip()
        sections[title] = content
    return sections


def extract_code_block(section_text: str, heading_aliases: List[str]) -> str:
    """从某个小节中提取指定标题后的第一个代码块。"""
    heading_pattern = "|".join(re.escape(x) for x in heading_aliases)
    pattern = (
        rf"^####\s*(?:{heading_pattern})\s*$"
        rf"(?:\r?\n)+```(?:[^\n]*)\n(.*?)\n```"
    )
    match = re.search(pattern, section_text, flags=re.S | re.M)
    return match.group(1).strip() if match else ""


def parse_examples(example_section: str) -> List[Dict[str, str]]:
    """解析样例段，支持多个样例。"""
    sample_headers = list(re.finditer(r"^###\s+.*$", example_section, flags=re.M))
    blocks: List[str] = []

    if sample_headers:
        for i, header in enumerate(sample_headers):
            start = header.start()
            end = sample_headers[i + 1].start() if i + 1 < len(sample_headers) else len(example_section)
            blocks.append(example_section[start:end].strip())
    else:
        blocks = [example_section.strip()]

    result: List[Dict[str, str]] = []
    for block in blocks:
        sample_in = extract_code_block(block, ["输入", "Input"])
        sample_out = extract_code_block(block, ["输出", "Output"])
        if not sample_in and not sample_out:
            continue
        result.append({"in": sample_in, "ans": sample_out, "description": ""})

    return result


def pick_section(sections: Dict[str, str], names: List[str]) -> str:
    """根据多个候选标题取值。"""
    for name in names:
        if name in sections:
            return sections[name].strip()
    return ""


def build_payload(problem_dir: Path) -> Dict:
    """将题目目录转换为接口需要的 JSON 结构。"""
    problem_md = problem_dir / "problem.md"
    if not problem_md.exists():
        raise FileNotFoundError(f"缺少文件: {problem_md}")

    content = problem_md.read_text(encoding="utf-8")
    front = parse_front_matter(content)
    sections = parse_level2_sections(content)

    pid = front.get("pid") or problem_dir.name
    title = front.get("title") or pid

    description = pick_section(sections, ["题目描述", "描述", "Description"])
    input_text = pick_section(sections, ["输入格式", "输入", "Input"])
    output_text = pick_section(sections, ["输出格式", "输出", "Output"])
    example_text = pick_section(sections, ["样例", "示例", "Examples", "Example"])
    hint = pick_section(sections, ["提示", "Hint", "备注", "说明"])

    payload = {
        "pid": pid,
        "title": title,
        "is_public": True,
        "description": description,
        "input": input_text,
        "output": output_text,
        "example": parse_examples(example_text),
        "hint": hint,
    }
    return payload


def fetch_next_pid(base_url: str, token: str, timeout: int) -> str:
    """调用接口获取下一个可用 pid，返回标准化的大写 pid。"""
    url = base_url.rstrip("/") + "/api/problem/next_id"
    req = urllib.request.Request(url=url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace").strip()
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"获取 next_id 失败: HTTP {err.code} | {body[:300]}") from err
    except urllib.error.URLError as err:
        raise RuntimeError(f"获取 next_id 失败: 网络错误 {err.reason}") from err
    except TimeoutError as err:
        raise RuntimeError("获取 next_id 失败: 请求超时") from err

    pid_candidate = body
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            for key in ("next_id", "pid", "id", "data"):
                value = parsed.get(key)
                if isinstance(value, str) and value.strip():
                    pid_candidate = value.strip()
                    break
        elif isinstance(parsed, str) and parsed.strip():
            pid_candidate = parsed.strip()
    except json.JSONDecodeError:
        pass

    match = re.search(r"([A-Z])([A-Z0-9]*)", pid_candidate)
    if not match:
        raise RuntimeError(f"获取 next_id 失败: 无法解析 pid，响应为: {body[:200]}")

    pid = match.group(0).strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,19}", pid):
        raise RuntimeError(f"获取 next_id 失败: pid 格式不合法，响应为: {body[:200]}")
    return pid


def normalize_p_pid(pid: str) -> str:
    """将任意 pid 规范化为 P 前缀。"""
    normalized = pid.strip().upper()
    match = re.search(r"(\d+)", normalized)
    if not match:
        raise ValueError(f"非法 pid 格式: {pid}")
    number = match.group(1)
    return f"P{int(number)}"


def increment_pid(pid: str) -> str:
    """将 pid 规范为 P 前缀并自增 1。"""
    normalized = normalize_p_pid(pid)
    match = re.fullmatch(r"P(\d+)", normalized)
    if not match:
        raise ValueError(f"非法 pid 格式: {pid}")
    return f"P{int(match.group(1)) + 1}"


def append_success_pid(file_path: Path, folder_name: str, pid: str) -> None:
    """将成功提交的文件夹名与 pid 追加到 CSV 文件。"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = file_path.exists()
    file_size = file_path.stat().st_size if file_exists else 0
    need_header = not file_exists or file_size == 0
    need_leading_newline = False
    if file_exists and file_size > 0:
        with file_path.open("rb") as f:
            f.seek(-1, 2)
            last_byte = f.read(1)
        need_leading_newline = last_byte not in {b"\n", b"\r"}

    with file_path.open("a", encoding="utf-8", newline="") as f:
        if need_leading_newline:
            f.write("\n")
        writer = csv.writer(f)
        if need_header:
            writer.writerow(["folder", "pid"])
        writer.writerow([folder_name, pid])


def post_problem(base_url: str, token: str, payload: Dict, timeout: int) -> Tuple[int, str]:
    """向接口提交单题并返回状态码和响应文本。"""
    url = base_url.rstrip("/") + "/api/problem"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url=url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        return err.code, body


def find_problem_dirs(root: Path) -> List[Path]:
    """查找所有包含 problem.md 的目录。"""
    dirs: List[Path] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if (child / "problem.md").exists():
            dirs.append(child)
    return dirs


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="批量提交所有包含 problem.md 的题目目录")
    parser.add_argument(
        "--root",
        default=".",
        help="题目根目录，默认当前目录",
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
        help="仅解析并打印，不实际提交",
    )
    parser.add_argument(
        "--success-pid-file",
        default="submitted_success_pids.csv",
        help="成功提交 pid 记录文件，默认 submitted_success_pids.csv",
    )

    args = parser.parse_args(argv)

    if not args.token:
        print("错误: 缺少 token。请使用 --token 或设置 PROBLEM_API_TOKEN", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"错误: 根目录不存在或不是目录: {root}", file=sys.stderr)
        return 2

    problem_dirs = find_problem_dirs(root)
    if not problem_dirs:
        print("未找到任何 P 开头的题目目录")
        return 0

    success = 0
    failed = 0
    success_pid_file = Path(args.success_pid_file).resolve()

    try:
        current_pid = fetch_next_pid(args.base_url, args.token, args.timeout)
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2

    print(f"起始 pid: {current_pid}")

    print(f"共发现 {len(problem_dirs)} 个 P 开头题目目录")

    for idx, pdir in enumerate(problem_dirs, start=1):
        try:
            payload = build_payload(pdir)
            payload["pid"] = current_pid
        except Exception as exc:
            failed += 1
            print(f"[{idx}/{len(problem_dirs)}] {pdir.name} 解析失败: {exc}")
            current_pid = increment_pid(current_pid)
            continue

        if args.dry_run:
            print(
                f"[{idx}/{len(problem_dirs)}] {pdir.name} 解析成功: "
                f"pid={payload['pid']}, title={payload['title']}, examples={len(payload['example'])}"
            )
            current_pid = increment_pid(current_pid)
            continue

        status, body = post_problem(args.base_url, args.token, payload, args.timeout)
        if 200 <= status < 300:
            success += 1
            print(f"[{idx}/{len(problem_dirs)}] {pdir.name} 提交成功: HTTP {status}")
            append_success_pid(success_pid_file, pdir.name, payload["pid"])
        else:
            failed += 1
            short_body = body.replace("\n", " ")[:300]
            print(f"[{idx}/{len(problem_dirs)}] {pdir.name} 提交失败: HTTP {status} | {short_body}")

        current_pid = increment_pid(current_pid)

    if args.dry_run:
        print("dry-run 完成")
        return 0

    print(f"提交结束: 成功 {success}，失败 {failed}，总计 {len(problem_dirs)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
