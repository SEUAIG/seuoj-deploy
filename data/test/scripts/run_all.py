#!/usr/bin/env python3
"""SEUOJ 自动化测试运行器

用法:
    python run_all.py              # 运行全部 6 轮
    python run_all.py 1 3 5        # 只运行第 1、3、5 轮
    python run_all.py --no-reset   # 不重置数据库（调试用）
"""

import importlib
import subprocess
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
from lib.common import wait_for_service, GREEN, RED, YELLOW, CYAN, NC

ROUNDS = [
    ("round1_auth_browse",             "认证 + 只读浏览"),
    ("round2_submissions",             "提交与判题"),
    ("round3_contests",                "比赛全流程"),
    ("round4_classes_assignments",     "班级 + 作业"),
    ("round5_problemsets_permissions", "题单 + 权限"),
    ("round6_problem_crud",            "题目 CRUD"),
]

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def dev_run():
    print(f"\n{CYAN}{'=' * 50}")
    print(f"  make dev_run — 重置开发环境")
    print(f"{'=' * 50}{NC}\n")
    r = subprocess.run(["make", "dev_run"], cwd=PROJECT_ROOT, timeout=300)
    if r.returncode != 0:
        print(f"{RED}make dev_run 失败 (exit {r.returncode}){NC}")
        return False
    return True


def dev_down():
    subprocess.run(["make", "dev_down"], cwd=PROJECT_ROOT, timeout=120)


def run_round(module_name: str, label: str) -> tuple[int, int, int]:
    mod = importlib.import_module(module_name)
    importlib.reload(mod)
    from lib import common
    common.reset_counts()
    mod.run()
    return common.PASS_COUNT, common.FAIL_COUNT, common.SKIP_COUNT


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    no_reset = "--no-reset" in sys.argv

    if args:
        selected = [int(a) - 1 for a in args]
    else:
        selected = list(range(len(ROUNDS)))

    total_pass = total_fail = total_skip = 0
    round_results = []

    for idx in selected:
        if idx < 0 or idx >= len(ROUNDS):
            print(f"{RED}无效轮次: {idx + 1}{NC}")
            continue

        module_name, label = ROUNDS[idx]
        round_num = idx + 1

        print(f"\n{CYAN}{'#' * 60}")
        print(f"  Round {round_num}: {label}")
        print(f"{'#' * 60}{NC}\n")

        if not no_reset:
            if not dev_run():
                round_results.append((round_num, label, 0, 0, 0, "RESET_FAIL"))
                continue

            if not wait_for_service():
                round_results.append((round_num, label, 0, 0, 0, "SERVICE_FAIL"))
                continue

        p, f, s = run_round(module_name, label)
        total_pass += p
        total_fail += f
        total_skip += s
        round_results.append((round_num, label, p, f, s, "OK"))

    if not no_reset:
        dev_down()

    # ── 汇总 ──
    print(f"\n{'=' * 60}")
    print(f"  SEUOJ 自动化测试汇总")
    print(f"{'=' * 60}")
    for rnum, label, p, f, s, status in round_results:
        if status != "OK":
            print(f"  Round {rnum}: {label} — {RED}{status}{NC}")
        else:
            color = GREEN if f == 0 else RED
            print(f"  Round {rnum}: {label} — {GREEN}{p} pass{NC}  {RED}{f} fail{NC}  {YELLOW}{s} skip{NC}")
    total = total_pass + total_fail + total_skip
    print(f"{'=' * 60}")
    print(f"  {GREEN}PASS: {total_pass}{NC}  {RED}FAIL: {total_fail}{NC}  {YELLOW}SKIP: {total_skip}{NC}  TOTAL: {total}")
    print(f"{'=' * 60}")

    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
