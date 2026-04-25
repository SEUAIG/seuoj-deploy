#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["toml"]
# ///
"""Convert legacy OJ problems (plain-text format) to SEUOJ judgend standard format.

Source structure (per problem):
  {id}/
    problem        — plain text (title + Description/Input/Output/Sample sections)
    input          — single test input file
    output         — single test output file
    limit          — time/memory limits
    special.cpp    — (optional) SPJ checker source
    interactor.cpp — (optional) interactive judge source
    *.png / *.jpg  — (optional) images referenced in problem text

Target structure (per problem):
  P{id}/
    problem.md     — SEUOJ markdown (YAML frontmatter + sections)
    info.toml      — evaluation config
    data/
      1.in, 1.ans  — test data
      checker.cpp  — (if SPJ)
      interactor.cpp — (if interactive)
      *.png / *.jpg — (if images exist)

Usage:
  uv run scripts/convert_legacy.py <source_dir> <output_dir> [--pid-prefix P]
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

import toml


def parse_limit(limit_text: str) -> tuple[int, int]:
    """Parse limit file → (time_limit_ms, memory_limit_kb)."""
    time_ms = 1000
    mem_kb = 262144

    for line in limit_text.strip().split("\n"):
        line = line.strip().lower()
        if line.startswith("timelimit:"):
            num = re.search(r"(\d+)", line)
            if num:
                time_ms = int(num.group(1))
        elif line.startswith("memorylimit:"):
            num = re.search(r"(\d+)", line)
            if num:
                mem_kb = int(num.group(1))

    return time_ms, mem_kb


def parse_legacy_problem(text: str) -> dict:
    """Parse legacy plain-text problem file into structured sections."""
    lines = text.replace("\r\n", "\n").split("\n")

    title = ""
    description = ""
    input_fmt = ""
    output_fmt = ""
    hint = ""
    sample_in = ""
    sample_out = ""

    current_section = None
    section_lines: list[str] = []

    known_sections = {
        "description", "input", "output",
        "sample input", "sample output",
        "hint", "提示",
    }

    def flush():
        nonlocal description, input_fmt, output_fmt, hint, sample_in, sample_out
        content = "\n".join(section_lines).strip()
        if current_section == "description":
            description = content
        elif current_section == "input":
            input_fmt = content
        elif current_section == "output":
            output_fmt = content
        elif current_section == "sample input":
            sample_in = content
        elif current_section == "sample output":
            sample_out = content
        elif current_section in ("hint", "提示"):
            hint = content

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if not title and not current_section and stripped and lower not in known_sections:
            title = stripped
            continue

        if lower in known_sections:
            flush()
            section_lines = []
            current_section = lower
            continue

        if current_section is None and stripped == "":
            continue

        if current_section is None:
            if stripped.startswith("示例代码") or stripped.startswith("题目判定提示"):
                current_section = "__skip__"
                continue
            continue

        if current_section == "__skip__":
            continue

        section_lines.append(line)

    flush()

    # Detect trailing "示例代码" or "题目判定提示" blocks in sample_out and strip them
    if sample_out:
        cut_patterns = ["示例代码", "题目判定提示"]
        out_lines = sample_out.split("\n")
        cut_idx = len(out_lines)
        for i, ol in enumerate(out_lines):
            for pat in cut_patterns:
                if pat in ol:
                    cut_idx = i
                    break
            if cut_idx < len(out_lines):
                break
        sample_out = "\n".join(out_lines[:cut_idx]).strip()

    # Also strip trailing hint/code from hint
    if hint:
        hint_lines = hint.split("\n")
        cut_idx = len(hint_lines)
        for i, hl in enumerate(hint_lines):
            if hl.strip().startswith("示例代码") or hl.strip().startswith("题目判定提示"):
                cut_idx = i
                break
        hint = "\n".join(hint_lines[:cut_idx]).strip()

    examples = []
    if sample_in or sample_out:
        examples.append({
            "in": sample_in,
            "ans": sample_out,
            "description": "",
        })

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

    out.append("## 提示")
    out.append("")
    if parsed["hint"]:
        out.append(parsed["hint"])
    out.append("")

    return "\n".join(out)


def generate_info_toml(
    time_ms: int,
    mem_kb: int,
    problem_type: str = "Standard",
    checker_type: str = "Standard",
    checker_path: str | None = None,
    interactor_path: str | None = None,
) -> dict:
    """Generate info.toml dict."""
    config: dict = {
        "problem_info": {
            "problem_type": problem_type,
            "checker_type": checker_type,
            "time_limit_ms": time_ms,
            "memory_limit_kb": mem_kb,
        },
        "testcases": [
            {
                "id": 1,
                "in_path": "1.in",
                "ans_path": "1.ans",
                "weight": 1.0,
            }
        ],
    }

    if checker_path or interactor_path:
        modules: dict = {}
        if checker_path:
            modules["checker_path"] = checker_path
        if interactor_path:
            modules["interactor_path"] = interactor_path
        config["custom_modules"] = modules

    return config


def convert_legacy_problem(
    source_dir: Path, output_dir: Path, pid: str
) -> bool:
    """Convert a single legacy problem directory."""
    problem_file = source_dir / "problem"
    input_file = source_dir / "input"
    output_file = source_dir / "output"
    limit_file = source_dir / "limit"

    if not problem_file.exists():
        print(f"  [跳过] 无 problem 文件: {source_dir.name}")
        return False
    if not input_file.exists() or not output_file.exists():
        print(f"  [跳过] 无 input/output 文件: {source_dir.name}")
        return False

    problem_text = problem_file.read_text(encoding="utf-8", errors="replace")
    parsed = parse_legacy_problem(problem_text)

    time_ms, mem_kb = (1000, 262144)
    if limit_file.exists():
        time_ms, mem_kb = parse_limit(limit_file.read_text(encoding="utf-8", errors="replace"))

    # Detect problem type
    has_special = (source_dir / "special.cpp").exists()
    has_interactor = (source_dir / "interactor.cpp").exists()

    if has_interactor:
        problem_type = "Interactive"
        checker_type = "Interactor"
    elif has_special:
        problem_type = "Special"
        checker_type = "Special"
    else:
        problem_type = "Standard"
        checker_type = "Standard"

    # Create output structure
    target_dir = output_dir / pid
    data_dir = target_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Write problem.md
    md_content = generate_problem_md(pid, parsed)
    (target_dir / "problem.md").write_text(md_content, encoding="utf-8")

    # Copy test data
    shutil.copy2(input_file, data_dir / "1.in")
    shutil.copy2(output_file, data_dir / "1.ans")

    # Copy special judge / interactor
    checker_path = None
    interactor_path = None
    if has_special:
        shutil.copy2(source_dir / "special.cpp", data_dir / "checker.cpp")
        checker_path = "checker.cpp"
    if has_interactor:
        shutil.copy2(source_dir / "interactor.cpp", data_dir / "interactor.cpp")
        interactor_path = "interactor.cpp"

    # Copy images
    for img in source_dir.glob("*.png"):
        shutil.copy2(img, data_dir / img.name)
    for img in source_dir.glob("*.jpg"):
        shutil.copy2(img, data_dir / img.name)
    for img in source_dir.glob("*.PNG"):
        if not (data_dir / img.name.lower()).exists():
            shutil.copy2(img, data_dir / img.name)
    for img in source_dir.glob("*.JPG"):
        if not (data_dir / img.name.lower()).exists():
            shutil.copy2(img, data_dir / img.name)

    # Write info.toml
    config = generate_info_toml(
        time_ms, mem_kb,
        problem_type, checker_type,
        checker_path, interactor_path,
    )
    (target_dir / "info.toml").write_text(
        toml.dumps(config), encoding="utf-8"
    )

    type_tag = ""
    if problem_type != "Standard":
        type_tag = f" [{problem_type}]"
    print(f"  [OK] {source_dir.name} → {pid} — {parsed['title']}{type_tag}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Convert legacy OJ problems to SEUOJ judgend format"
    )
    parser.add_argument("source_dir", help="Source directory containing numbered problem folders")
    parser.add_argument("output_dir", help="Output directory for converted problems")
    parser.add_argument(
        "--pid-prefix", default="P",
        help="Prefix for generated PIDs (default: P → P1000, P1001, ...)"
    )
    args = parser.parse_args()

    source = Path(args.source_dir)
    output = Path(args.output_dir)

    if not source.is_dir():
        print(f"错误: 源目录不存在 — {source}")
        sys.exit(1)

    problem_dirs = sorted(
        [d for d in source.iterdir() if d.is_dir() and (d / "problem").exists()],
        key=lambda d: d.name,
    )

    print(f"发现 {len(problem_dirs)} 个题目目录")
    print(f"输出: {output}")
    print()

    converted = 0
    for pdir in problem_dirs:
        pid = f"{args.pid_prefix}{pdir.name}"
        if convert_legacy_problem(pdir, output, pid):
            converted += 1

    print(f"\n完成: {converted}/{len(problem_dirs)} 题目已转换")


if __name__ == "__main__":
    main()
