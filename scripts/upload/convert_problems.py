#!/usr/bin/env python3
"""Convert problems from 洛谷-style format to SEUOJ format.

Source structure (per problem):
  T{id} {name}/
    problem.md       — 洛谷-style markdown
    data.zip         — test data (various naming conventions)

Target structure (per problem):
  {pid}/
    problem.md       — SEUOJ markdown (YAML frontmatter + fixed sections)
    info.toml        — problem config (testcases, limits, etc.)
    data/
      1.in, 1.ans, 2.in, 2.ans, ...

Usage:
  python scripts/convert_problems.py <source_dir> <output_dir> [--start-pid P2001]
"""

import argparse
import os
import re
import shutil
import zipfile
from pathlib import Path


def parse_source_md(md_text: str) -> dict:
    """Parse 洛谷-style problem.md into structured sections."""
    lines = md_text.replace("\r\n", "\n").split("\n")

    title = ""
    background = ""
    description = ""
    input_fmt = ""
    output_fmt = ""
    hint = ""
    examples = []

    current_section = None
    current_example = None
    current_example_part = None
    section_lines = []

    def flush_section():
        nonlocal background, description, input_fmt, output_fmt, hint
        nonlocal current_example, current_example_part
        content = "\n".join(section_lines).strip()
        if current_section == "题目背景":
            background = content
        elif current_section == "题目描述":
            description = content
        elif current_section == "输入格式":
            input_fmt = content
        elif current_section == "输出格式":
            output_fmt = content
        elif current_section and current_section.startswith("说明") or current_section == "提示":
            hint = content
        elif current_section and current_section.startswith("输入输出样例"):
            if current_example is not None:
                if current_example_part == "output":
                    current_example["ans"] = extract_code_block(section_lines)
                elif current_example_part == "input":
                    current_example["in"] = extract_code_block(section_lines)
                examples.append(current_example)
                current_example = None
                current_example_part = None

    def extract_code_block(block_lines: list[str]) -> str:
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

    for line in lines:
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue

        h2_match = re.match(r"^## (.+)$", line)
        if h2_match:
            flush_section()
            section_lines = []
            heading = h2_match.group(1).strip()
            current_section = heading

            if heading.startswith("输入输出样例"):
                current_example = {"in": "", "ans": "", "description": ""}
                current_example_part = None
            continue

        h3_match = re.match(r"^### (.+)$", line)
        if h3_match and current_section and current_section.startswith("输入输出样例"):
            h3_heading = h3_match.group(1).strip()
            if current_example_part == "output":
                current_example["ans"] = extract_code_block(section_lines)
            elif current_example_part == "input":
                current_example["in"] = extract_code_block(section_lines)
            section_lines = []
            if h3_heading.startswith("输入"):
                current_example_part = "input"
            elif h3_heading.startswith("输出"):
                current_example_part = "output"
            continue

        section_lines.append(line)

    flush_section()

    if background and description:
        description = background + "\n\n" + description
    elif background:
        description = background

    # Strip Txxxxxx prefix from title (e.g. "T602077 投票问题" → "投票问题")
    title = re.sub(r"^T\d+\s+", "", title)

    return {
        "title": title,
        "description": description,
        "input": input_fmt,
        "output": output_fmt,
        "hint": hint,
        "examples": examples,
    }


def generate_problem_md(pid: str, parsed: dict) -> str:
    """Generate SEUOJ-format problem.md."""
    out = []
    out.append("---")
    out.append(f"pid: {pid}")
    if parsed.get("title"):
        out.append(f"title: {parsed['title']}")
    out.append("---")
    out.append("")
    out.append("## 题目描述")
    out.append("")
    out.append(parsed["description"])
    out.append("")
    out.append("## 输入格式")
    out.append("")
    out.append(parsed["input"])
    out.append("")
    out.append("## 输出格式")
    out.append("")
    out.append(parsed["output"])
    out.append("")

    if parsed["examples"]:
        out.append("## 样例")
        out.append("")
        for i, ex in enumerate(parsed["examples"], 1):
            out.append(f"### 样例 {i}")
            out.append("")
            out.append("#### 输入")
            out.append("")
            out.append("```")
            out.append(ex["in"])
            out.append("```")
            out.append("")
            out.append("#### 输出")
            out.append("")
            out.append("```")
            out.append(ex["ans"])
            out.append("```")
            out.append("")
            if ex.get("description"):
                out.append(ex["description"])
                out.append("")

    out.append("## 提示")
    out.append("")
    if parsed["hint"]:
        out.append(parsed["hint"])
    out.append("")

    return "\n".join(out)


def process_data_zip(zip_path: Path, output_data_dir: Path) -> list[dict]:
    """Extract and rename test data from zip, return testcase configs."""
    output_data_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        in_files = {}
        out_files = {}

        for name in names:
            basename = os.path.basename(name)
            # Extract number from filename
            num_match = re.search(r"(\d+)", basename)
            if not num_match:
                continue
            num = int(num_match.group(1))
            lower = basename.lower()
            if lower.startswith("input") or lower.endswith(".in"):
                in_files[num] = name
            elif lower.startswith("output") or lower.endswith(".out"):
                out_files[num] = name

        testcases = []
        case_nums = sorted(set(in_files.keys()) & set(out_files.keys()))

        for idx, num in enumerate(case_nums, 1):
            in_name = f"{idx}.in"
            ans_name = f"{idx}.ans"

            in_data = zf.read(in_files[num])
            out_data = zf.read(out_files[num])

            (output_data_dir / in_name).write_bytes(in_data)
            (output_data_dir / ans_name).write_bytes(out_data)

            testcases.append({
                "id": idx,
                "in_path": in_name,
                "ans_path": ans_name,
            })

    return testcases


def generate_info_toml(
    testcases: list[dict],
    time_limit_ms: int = 1000,
    memory_limit_kb: int = 262144,
) -> str:
    """Generate info.toml content."""
    lines = []
    lines.append("[problem_info]")
    lines.append('problem_type = "Standard"')
    lines.append('checker_type = "Standard"')
    lines.append(f"time_limit_ms = {time_limit_ms}")
    lines.append(f"memory_limit_kb = {memory_limit_kb}")
    lines.append("")

    for tc in testcases:
        lines.append("[[testcases]]")
        lines.append(f"id = {tc['id']}")
        lines.append(f'in_path = "{tc["in_path"]}"')
        lines.append(f'ans_path = "{tc["ans_path"]}"')
        lines.append("weight = 1")
        lines.append("")

    return "\n".join(lines)


def convert_problem(
    source_dir: Path,
    output_dir: Path,
    pid: str,
    time_limit_ms: int = 1000,
    memory_limit_kb: int = 262144,
) -> bool:
    """Convert a single problem directory."""
    problem_md_path = source_dir / "problem.md"
    data_zip_path = source_dir / "data.zip"

    if not problem_md_path.exists():
        print(f"  [SKIP] No problem.md found in {source_dir}")
        return False
    if not data_zip_path.exists():
        print(f"  [SKIP] No data.zip found in {source_dir}")
        return False

    md_text = problem_md_path.read_text(encoding="utf-8")
    parsed = parse_source_md(md_text)

    target_dir = output_dir / pid
    target_dir.mkdir(parents=True, exist_ok=True)

    target_md = generate_problem_md(pid, parsed)
    (target_dir / "problem.md").write_text(target_md, encoding="utf-8")

    testcases = process_data_zip(data_zip_path, target_dir / "data")

    if not testcases:
        print(f"  [WARN] No valid testcases found in data.zip")

    info_toml = generate_info_toml(testcases, time_limit_ms, memory_limit_kb)
    (target_dir / "info.toml").write_text(info_toml, encoding="utf-8")

    return True


def main():
    parser = argparse.ArgumentParser(description="Convert 洛谷-style problems to SEUOJ format")
    parser.add_argument("source_dir", help="Source directory containing problem folders")
    parser.add_argument("output_dir", help="Output directory for converted problems")
    parser.add_argument(
        "--start-pid",
        default="P2001",
        help="Starting problem ID prefix+number (default: P2001)",
    )
    parser.add_argument("--time-limit", type=int, default=1000, help="Time limit in ms")
    parser.add_argument("--memory-limit", type=int, default=262144, help="Memory limit in KB")
    args = parser.parse_args()

    source = Path(args.source_dir)
    output = Path(args.output_dir)

    pid_match = re.match(r"^([A-Za-z]*)(\d+)$", args.start_pid)
    if not pid_match:
        print(f"Error: invalid start-pid format: {args.start_pid}")
        return

    prefix = pid_match.group(1)
    start_num = int(pid_match.group(2))

    problem_dirs = sorted(
        [d for d in source.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )

    print(f"Found {len(problem_dirs)} problem directories")
    print(f"Output: {output}")
    print(f"PID range: {prefix}{start_num} ~ {prefix}{start_num + len(problem_dirs) - 1}")
    print()

    converted = 0
    for i, pdir in enumerate(problem_dirs):
        pid = f"{prefix}{start_num + i}"
        print(f"[{i+1}/{len(problem_dirs)}] {pdir.name} -> {pid}")
        if convert_problem(pdir, output, pid, args.time_limit, args.memory_limit):
            converted += 1

    print(f"\nDone: {converted}/{len(problem_dirs)} problems converted")


if __name__ == "__main__":
    main()
