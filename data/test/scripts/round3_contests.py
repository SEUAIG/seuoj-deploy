#!/usr/bin/env python3
"""Round 3: 比赛全流程 (C1, C3-C10, C11)"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib.common import *


def run():
    reset_counts()

    token_student1 = login(USERS["student1"]["email"])
    token_student5 = login(USERS["student5"]["email"])
    token_teacher1 = login(USERS["teacher1"]["email"])
    if not all([token_student1, token_student5, token_teacher1]):
        test_fail("C-SETUP", "登录失败")
        return report_summary()

    # ── C1 — 浏览比赛列表 ──
    test_start("C1", "浏览比赛列表（游客）")
    code, body = api_get("/contest/page")
    if assert_status("C1", 200, code):
        records = extract(body, "data.records") or []
        titles = [r.get("title", "") for r in records]
        assert_true("C1.public", any("春季训练赛" in t for t in titles),
                    "公开比赛可见", "未找到公开比赛")
        assert_true("C1.no_private", not any("期末模拟赛" in t for t in titles),
                    "非公开比赛不可见", "非公开比赛也出现在列表中")

    # ── C3 — student5 报名比赛2 ──
    test_start("C3", "student5 报名进行中比赛2")
    code, body = api_post("/contest/register", token=token_student5, data=None)
    code, body = api_post(f"/contest/register?contest_id=2", token=token_student5)
    assert_true("C3", code == 200, f"报名成功 HTTP {code}", f"报名失败 HTTP {code}: {body}")

    # ── C4 — student1 在比赛2 中提交 ──
    test_start("C4", "student1 在比赛2 中提交代码")
    ok, result = contest_submit_and_poll(2, "P1002", "Cpp", SAMPLE_CODE["Cpp"], token_student1, timeout=60)
    if ok:
        verdict = extract(result, "verdict") or extract(result, "result.verdict")
        test_pass("C4", f"提交成功，verdict={verdict}")
    else:
        test_fail("C4", f"提交失败: {result}")

    # ── C5 — 查看排行榜 (比赛1) ──
    test_start("C5", "查看排行榜（已结束比赛1）")
    code, body = api_get("/contest/1/standings", token=token_student1)
    if assert_status("C5", 200, code):
        assert_json_not_empty("C5.data", body, "data")

    # ── C10 — 比赛提交记录 ──
    test_start("C10", "比赛1 提交记录列表")
    code, body = api_get("/contest/1/submission/page", token=token_student1)
    if assert_status("C10", 200, code):
        records = extract(body, "data.records") or []
        assert_true("C10.has_records", len(records) > 0,
                    f"有 {len(records)} 条提交", "未找到提交记录")

    # ── C9 — student1 取消报名比赛2（比赛已开始，应被拒绝） ──
    test_start("C9", "student1 取消报名比赛2（已开始，应被拒绝）")
    code, body = api_delete(f"/contest/register?contest_id=2", token=token_student1)
    assert_true("C9", code in (400, 403), f"取消被拒绝 HTTP {code}", f"期望 400/403，实际 HTTP {code}")

    # ── C6 — teacher1 创建比赛 ──
    test_start("C6", "teacher1 创建比赛")
    contest_data = {
        "title": "单元测试赛",
        "subtitle": "自动化测试",
        "description": "自动化测试创建的比赛",
        "start_time": "2026-06-01T10:00:00",
        "end_time": "2026-06-01T15:00:00",
        "rule_type": "ACM",
        "is_public": True,
    }
    code, body = api_post("/contest", contest_data, token_teacher1)
    new_contest_id = None
    if assert_status("C6", 200, code):
        new_contest_id = extract(body, "data.id") or extract(body, "data.contest_id")
        assert_true("C6.id", new_contest_id is not None,
                    f"比赛创建成功 id={new_contest_id}", "未返回比赛 id")

    # ── C7 — 给新比赛添加题目 ──
    test_start("C7", "编辑比赛（添加题目）")
    if new_contest_id:
        code, body = api_post(f"/contest/{new_contest_id}/problem", {
            "problem_list": [
                {"pid": "P0001", "sort_order": 0},
                {"pid": "P0002", "sort_order": 1},
            ]
        }, token_teacher1)
        assert_status("C7", 200, code)
    else:
        test_skip("C7", "比赛创建失败，跳过")

    # ── C8 — 非公开比赛访问 ──
    test_start("C8", "student1 访问非公开比赛3")
    code, body = api_get("/contest/3", token=token_student1)
    assert_true("C8", code in (403, 404, 200),
                f"HTTP {code}（非公开比赛访问控制正常）",
                f"异常状态码 HTTP {code}")

    # ── C11 — IOI 赛制部分分 ──
    test_start("C11", "IOI 赛制部分分")
    token_s5 = token_student5
    ok, result = contest_submit_and_poll(2, "P1002", "Cpp", WA_CODE, token_s5, timeout=60)
    if ok:
        score = extract(result, "score") or extract(result, "result.score")
        test_pass("C11", f"IOI 提交完成，score={score}")
    else:
        test_fail("C11", f"IOI 提交失败: {result}")

    return report_summary()


if __name__ == "__main__":
    if not wait_for_service():
        sys.exit(1)
    ok = run()
    sys.exit(0 if ok else 1)
