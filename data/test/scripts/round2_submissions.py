#!/usr/bin/env python3
"""Round 2: 提交与判题 (S1-S13)"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib.common import *


def run():
    reset_counts()

    token = login(USERS["student1"]["email"])
    if not token:
        test_fail("S-SETUP", "student1 登录失败")
        return report_summary()

    # ── S1~S6: 6 种语言 AC ──
    langs = [
        ("S1", "Cpp",        "C++ AC"),
        ("S2", "Java17",     "Java AC"),
        ("S3", "Python3_12", "Python AC"),
        ("S4", "C",          "C AC"),
        ("S5", "Go1_22",     "Go AC"),
        ("S6", "Nodejs22",   "Node.js AC"),
    ]
    for tid, lang, desc in langs:
        test_start(tid, desc)
        ok, result = submit_and_poll("P0001", lang, SAMPLE_CODE[lang], token, timeout=60)
        if ok:
            verdict = extract(result, "verdict") or extract(result, "result.verdict")
            score = extract(result, "score") or extract(result, "result.score")
            assert_true(tid, str(verdict) == "Accepted",
                        f"verdict=Accepted, score={score}", f"verdict={verdict}, score={score}")
        else:
            test_fail(tid, f"提交或轮询失败: {result}")

    # ── S7: WrongAnswer ──
    test_start("S7", "WrongAnswer")
    ok, result = submit_and_poll("P0001", "Cpp", WA_CODE, token)
    if ok:
        verdict = extract(result, "verdict") or extract(result, "result.verdict")
        assert_true("S7", str(verdict) == "WrongAnswer",
                    f"verdict={verdict}", f"期望 WrongAnswer，实际 {verdict}")
    else:
        test_fail("S7", f"提交或轮询失败: {result}")

    # ── S8: TimeLimitExceeded ──
    test_start("S8", "TimeLimitExceeded")
    ok, result = submit_and_poll("P0001", "Cpp", TLE_CODE, token, timeout=60)
    if ok:
        verdict = extract(result, "verdict") or extract(result, "result.verdict")
        assert_true("S8", str(verdict) == "TimeLimitExceeded",
                    f"verdict={verdict}", f"期望 TimeLimitExceeded，实际 {verdict}")
    else:
        test_fail("S8", f"提交或轮询失败: {result}")

    # ── S9: RuntimeError ──
    test_start("S9", "RuntimeError")
    ok, result = submit_and_poll("P0001", "Cpp", RE_CODE, token)
    if ok:
        verdict = extract(result, "verdict") or extract(result, "result.verdict")
        assert_true("S9", str(verdict) == "RuntimeError",
                    f"verdict={verdict}", f"期望 RuntimeError，实际 {verdict}")
    else:
        test_fail("S9", f"提交或轮询失败: {result}")

    # ── S10: CompileError ──
    test_start("S10", "CompileError")
    ok, result = submit_and_poll("P0001", "Cpp", CE_CODE, token)
    if ok:
        verdict = extract(result, "verdict") or extract(result, "result.verdict")
        assert_true("S10", str(verdict) == "CompileError",
                    f"verdict={verdict}", f"期望 CompileError，实际 {verdict}")
    else:
        test_fail("S10", f"提交或轮询失败: {result}")

    # ── S11: MemoryLimitExceeded ──
    test_skip("S11", "MLE 行为依赖 sandbox 实现，跳过")

    # ── S12: 查看提交详情 ──
    test_start("S12", "查看提交详情")
    code, body = api_get("/submission/page", token, params={"pid": "P0001", "size": "1"})
    if assert_status("S12.list", 200, code):
        records = extract(body, "data.records") or []
        if records:
            sub_no = records[0].get("submissionNo") or records[0].get("submission_no")
            if sub_no:
                c2, b2 = api_get(f"/submission/{sub_no}", token)
                if assert_status("S12.detail", 200, c2):
                    assert_json_not_empty("S12.verdict", b2, "data.verdict")

    # ── S13: 评测列表筛选 ──
    test_start("S13", "评测列表筛选")
    code, body = api_get("/submission/page", params={"pid": "P0001", "verdict": "Accepted"})
    if assert_status("S13.filter", 200, code):
        records = extract(body, "data.records") or []
        assert_true("S13.result", len(records) > 0,
                    f"筛选到 {len(records)} 条 AC 记录", "未筛选到 AC 记录")

    # ── S14 — SKIP ──
    test_skip("S14", "需浏览器测试：判题实时状态变化动画")

    return report_summary()


if __name__ == "__main__":
    if not wait_for_service():
        sys.exit(1)
    ok = run()
    sys.exit(0 if ok else 1)
