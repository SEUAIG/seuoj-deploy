#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "toml"]
# ///
"""Discover, preview, and upload problems in judgend format to SEUOJ.

Scans a directory tree for problem folders (containing problem.md + info.toml + data/),
shows a preview table, then uploads each problem via the OJ REST API.

Usage:
  uv run scripts/upload_problems.py <source_dir> [--public] [--dry-run]
"""

import argparse
import getpass
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import requests
import toml

# ── Configurable constants ──────────────────────────────────────────
# Change these to skip interactive prompts.
BASE_URL = "CHANGE_ME"
USERNAME = "CHANGE_ME"
PASSWORD = "CHANGE_ME"
# ────────────────────────────────────────────────────────────────────


def prompt_config() -> tuple[str, str, str]:
    """Prompt for BASE_URL / USERNAME / PASSWORD if they are still placeholder values."""
    url = BASE_URL
    user = USERNAME
    pw = PASSWORD

    if url == "CHANGE_ME":
        url = input("OJ 地址 (例如 http://localhost:2280): ").strip().rstrip("/")
        if not url:
            print("错误: OJ 地址不能为空")
            sys.exit(1)

    if user == "CHANGE_ME":
        user = input("用户名或邮箱: ").strip()
        if not user:
            print("错误: 用户名不能为空")
            sys.exit(1)

    if pw == "CHANGE_ME":
        pw = getpass.getpass("密码: ")
        if not pw:
            print("错误: 密码不能为空")
            sys.exit(1)

    return url, user, pw


def login(base_url: str, identifier: str, password: str) -> str:
    """Login and return JWT token."""
    resp = requests.post(
        f"{base_url}/api/auth/login",
        json={"identifier": identifier, "password": password},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"登录失败 (HTTP {resp.status_code}): {resp.text}")
        sys.exit(1)

    data = resp.json()
    jwt = data.get("data", {}).get("jwt")
    if not jwt:
        print(f"登录响应中未找到 JWT: {data}")
        sys.exit(1)

    role = data.get("data", {}).get("role", "")
    username = data.get("data", {}).get("username", "")
    print(f"登录成功: {username} ({role})")
    return jwt


# ── problem.md parsing ──────────────────────────────────────────────

SECTION_MAP = {
    "题目描述": "description",
    "Description": "description",
    "输入格式": "input",
    "Input": "input",
    "输出格式": "output",
    "Output": "output",
    "提示": "hint",
    "Hint": "hint",
    "样例": "examples",
    "Examples": "examples",
}


def parse_problem_md(text: str) -> dict:
    """Parse SEUOJ-format problem.md into structured fields."""
    text = text.replace("\r\n", "\n")

    pid = ""
    title = ""
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).split("\n"):
            if line.strip().startswith("pid:"):
                pid = line.split(":", 1)[1].strip()
            elif line.strip().startswith("title:"):
                title = line.split(":", 1)[1].strip()
        text = text[fm_match.end():]

    lines = text.split("\n")

    sections: dict[str, list[str]] = {}
    current_key = None

    for line in lines:
        if not title and line.startswith("# "):
            title = line[2:].strip()
            continue

        h2 = re.match(r"^## (.+)$", line)
        if h2:
            heading = h2.group(1).strip()
            key = SECTION_MAP.get(heading)
            if key:
                current_key = key
                sections.setdefault(key, [])
            else:
                current_key = None
            continue

        if current_key:
            sections.setdefault(current_key, []).append(line)

    description = "\n".join(sections.get("description", [])).strip()
    input_fmt = "\n".join(sections.get("input", [])).strip()
    output_fmt = "\n".join(sections.get("output", [])).strip()
    hint = "\n".join(sections.get("hint", [])).strip()
    examples = _parse_examples(sections.get("examples", []))

    return {
        "pid": pid,
        "title": title or pid,
        "description": description,
        "input": input_fmt,
        "output": output_fmt,
        "hint": hint,
        "examples": examples,
    }


def _parse_examples(lines: list[str]) -> list[dict]:
    """Parse example sections from lines under ## 样例."""
    examples = []
    current = None
    part = None
    buf: list[str] = []
    in_code = False

    def flush():
        nonlocal current, part
        if current and part and buf:
            code = _extract_code_block(buf)
            if part == "input":
                current["in"] = code
            elif part == "output":
                current["ans"] = code

    for line in lines:
        h3 = re.match(r"^### (.+)$", line)
        if h3:
            flush()
            if current and (current.get("in") or current.get("ans")):
                examples.append(current)
            current = {"in": "", "ans": "", "description": ""}
            part = None
            buf = []
            in_code = False
            continue

        h4 = re.match(r"^#### (.+)$", line)
        if h4:
            flush()
            buf = []
            in_code = False
            heading = h4.group(1).strip()
            if "输入" in heading or heading.lower() == "input":
                part = "input"
            elif "输出" in heading or heading.lower() == "output":
                part = "output"
            else:
                part = None
            continue

        buf.append(line)

    flush()
    if current and (current.get("in") or current.get("ans")):
        examples.append(current)

    return examples


def _extract_code_block(block_lines: list[str]) -> str:
    in_block = False
    code_lines = []
    for line in block_lines:
        trimmed = line.strip()
        if not in_block and trimmed.startswith("```"):
            in_block = True
            continue
        if in_block:
            if trimmed == "```" or (trimmed.startswith("```") and trimmed.strip("`") == ""):
                break
            code_lines.append(line)
    return "\n".join(code_lines)


# ── Directory discovery ─────────────────────────────────────────────


def discover_problems(root: Path) -> list[Path]:
    """Recursively find directories containing problem.md + info.toml + data/."""
    results = []
    for dirpath in sorted(root.rglob("*")):
        if not dirpath.is_dir():
            continue
        if (
            (dirpath / "problem.md").is_file()
            and (dirpath / "info.toml").is_file()
            and (dirpath / "data").is_dir()
        ):
            results.append(dirpath)

    if (
        root.is_dir()
        and (root / "problem.md").is_file()
        and (root / "info.toml").is_file()
        and (root / "data").is_dir()
    ):
        if root not in results:
            results.insert(0, root)

    results.sort(key=lambda p: p.name)
    return results


def load_problem(pdir: Path) -> dict:
    """Load and parse a problem directory into upload-ready data."""
    md_text = (pdir / "problem.md").read_text(encoding="utf-8")
    parsed = parse_problem_md(md_text)

    config = toml.load(pdir / "info.toml")

    data_files = sorted(f.name for f in (pdir / "data").iterdir() if f.is_file())

    return {
        "dir": pdir,
        "pid": str(parsed["pid"]),
        "title": parsed["title"],
        "description": parsed["description"],
        "input": parsed["input"],
        "output": parsed["output"],
        "hint": parsed["hint"],
        "examples": parsed["examples"],
        "config": config,
        "testcase_count": len(config.get("testcases", [])),
        "data_files": data_files,
    }


# ── Preview ─────────────────────────────────────────────────────────


def preview_problems(problems: list[dict]):
    """Print a compact table of discovered problems."""
    if not problems:
        print("未发现任何题目目录")
        return

    pid_w = max(len(p["pid"]) for p in problems)
    pid_w = max(pid_w, 3)
    title_w = max(len(p["title"][:30]) for p in problems)
    title_w = max(title_w, 4)

    header = f"  {'#':>3}  {'PID':<{pid_w}}  {'标题':<{title_w}}  {'测试点':>4}  {'文件数':>4}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for i, p in enumerate(problems, 1):
        title_display = p["title"][:30]
        print(
            f"  {i:>3}  {p['pid']:<{pid_w}}  {title_display:<{title_w}}  {p['testcase_count']:>4}  {len(p['data_files']):>4}"
        )
    print()


# ── Upload ──────────────────────────────────────────────────────────


def make_data_zip(data_dir: Path) -> bytes:
    """Create an in-memory ZIP of the data/ directory contents."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(data_dir.iterdir()):
            if f.is_file():
                zf.write(f, f.name)
    return buf.getvalue()


def upload_problem(
    base_url: str,
    token: str,
    problem: dict,
    is_public: bool,
) -> str:
    """Upload a single problem. Returns 'ok', 'skipped', or 'failed'."""
    headers = {"Authorization": f"Bearer {token}"}
    pid = problem["pid"]

    # Step 1: Create problem
    create_body = {
        "pid": pid,
        "title": problem["title"],
        "is_public": is_public,
        "description": problem["description"],
        "input": problem["input"],
        "output": problem["output"],
        "example": problem["examples"],
        "hint": problem["hint"],
    }

    resp = requests.post(
        f"{base_url}/api/problem",
        json=create_body,
        headers=headers,
        timeout=15,
    )

    if resp.status_code != 200:
        body = resp.text
        if "pid 已存在" in body or "pid已存在" in body:
            print(f"  [跳过] {pid} — pid 已存在")
            return "skipped"
        print(f"  [失败] {pid} 创建题目失败 (HTTP {resp.status_code}): {body[:200]}")
        return "failed"

    # Step 2: Upload test data
    data_dir = problem["dir"] / "data"
    zip_bytes = make_data_zip(data_dir)

    resp = requests.post(
        f"{base_url}/api/problem/data/{pid}",
        files={"file": ("data.zip", zip_bytes, "application/zip")},
        headers=headers,
        timeout=60,
    )

    if resp.status_code != 200:
        print(f"  [失败] {pid} 上传测试数据失败 (HTTP {resp.status_code}): {resp.text[:200]}")
        return "failed"

    # Step 3: Update judge config
    resp = requests.put(
        f"{base_url}/api/problem/config/{pid}",
        json=problem["config"],
        headers=headers,
        timeout=15,
    )

    if resp.status_code != 200:
        print(f"  [失败] {pid} 更新评测配置失败 (HTTP {resp.status_code}): {resp.text[:200]}")
        return "failed"

    print(f"  [成功] {pid} — {problem['title']}")
    return "ok"


# ── Main ────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="批量上传 judgend 标准格式题目到 SEUOJ",
    )
    parser.add_argument("source_dir", help="题目源目录（自动递归搜索子目录）")
    parser.add_argument("--public", action="store_true", default=False, help="设置题目为公开（默认不公开）")
    parser.add_argument("--dry-run", action="store_true", default=False, help="仅预览，不实际上传")
    args = parser.parse_args()

    source = Path(args.source_dir)
    if not source.is_dir():
        print(f"错误: 目录不存在 — {source}")
        sys.exit(1)

    # Discover
    print(f"扫描目录: {source}")
    problem_dirs = discover_problems(source)
    if not problem_dirs:
        print("未发现任何符合 judgend 格式的题目目录")
        sys.exit(0)

    print(f"发现 {len(problem_dirs)} 个题目目录\n")

    # Load & preview
    problems = []
    for pdir in problem_dirs:
        try:
            problems.append(load_problem(pdir))
        except Exception as e:
            print(f"  [警告] 加载 {pdir.name} 失败: {e}")

    preview_problems(problems)

    if args.dry_run:
        print("(--dry-run 模式，不执行上传)")
        return

    # Auth
    base_url, user, pw = prompt_config()
    token = login(base_url, user, pw)
    print()

    # Confirm
    answer = input(f"即将上传 {len(problems)} 道题目到 {base_url}，继续？[y/N] ").strip().lower()
    if answer not in ("y", "yes"):
        print("已取消")
        return

    print()

    # Upload
    ok = skipped = failed = 0
    for problem in problems:
        result = upload_problem(base_url, token, problem, args.public)
        if result == "ok":
            ok += 1
        elif result == "skipped":
            skipped += 1
        else:
            failed += 1

    print(f"\n完成: 成功 {ok} / 跳过 {skipped} / 失败 {failed}")


if __name__ == "__main__":
    main()
