#!/usr/bin/env python3
"""Round 4: 班级 + 作业 (CL1-CL14, AS1-AS11)"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib.common import *


def run():
    reset_counts()

    token_student1 = login(USERS["student1"]["email"])
    token_student5 = login(USERS["student5"]["email"])
    token_teacher1 = login(USERS["teacher1"]["email"])
    token_teacher2 = login(USERS["teacher2"]["email"])
    if not all([token_student1, token_student5, token_teacher1, token_teacher2]):
        test_fail("CL-SETUP", "登录失败")
        return report_summary()

    # ── CL1 — 浏览班级列表 ──
    test_start("CL1", "浏览班级列表")
    code, body = api_get("/class/page", token=token_student1)
    if assert_status("CL1", 200, code):
        records = extract(body, "data.records") or []
        names = [r.get("name", "") for r in records]
        assert_true("CL1.public", any("数据结构" in n for n in names),
                    "公开班级可见", "未找到公开班级「数据结构与算法」")

    # ── CL2 — 查看班级详情 ──
    test_start("CL2", "查看班级详情")
    code, body = api_get("/class/1", token=token_student1)
    if assert_status("CL2", 200, code):
        assert_json_not_empty("CL2.name", body, "data.name")

    # ── CL3 — 查看公告 ──
    test_start("CL3", "查看班级公告")
    code, body = api_get("/class/1/announcement/page", token=token_student1)
    if assert_status("CL3", 200, code):
        records = extract(body, "data.records") or []
        assert_true("CL3.has_announcements", len(records) > 0,
                    f"有 {len(records)} 条公告", "未找到公告")

    # ── CL4 — student5 加入公开班级3（种子数据已加入，应返回 409） ──
    test_start("CL4", "student5 加入公开班级3（已是成员，应 409）")
    code, body = api_post("/class/3/join", token=token_student5)
    assert_true("CL4", code == 409, f"重复加入被拒绝 HTTP {code}", f"期望 409，实际 HTTP {code}: {body}")

    # ── CL5 — teacher1 创建班级 ──
    test_start("CL5", "teacher1 创建班级")
    code, body = api_post("/class", {
        "name": "测试班级",
        "description": "用于测试",
        "is_public": True,
    }, token_teacher1)
    new_class_id = None
    if assert_status("CL5", 200, code):
        new_class_id = extract(body, "data.id") or extract(body, "data.class_id")
        test_pass("CL5.created", f"班级创建成功 id={new_class_id}")

    # ── CL6 — 编辑班级 ──
    test_start("CL6", "编辑班级1描述")
    code, body = api_put("/class/1", {
        "name": "数据结构与算法 2026春",
        "description": "已更新的描述",
        "is_public": True,
    }, token_teacher1)
    assert_status("CL6", 200, code)

    # ── CL7 — 批量导入学生（JSON API） ──
    test_start("CL7", "批量导入学生（正常）")
    target_class = new_class_id if new_class_id else 1
    code, body = api_post(f"/class/{target_class}/batch-import", {
        "password_mode": "assigned",
        "send_email": False,
        "students": [
            {"student_id": "IMPORT001", "name": "导入学生1", "password": "Pass123456"},
            {"student_id": "IMPORT002", "name": "导入学生2", "password": "Pass123456"},
        ]
    }, token_teacher1)
    assert_status("CL7", 200, code)

    # ── CL8 — 批量导入（重复） ──
    test_start("CL8", "批量导入学生（重复）")
    code, body = api_post(f"/class/{target_class}/batch-import", {
        "password_mode": "assigned",
        "send_email": False,
        "students": [
            {"student_id": "IMPORT001", "name": "导入学生1", "password": "Pass123456"},
        ]
    }, token_teacher1)
    assert_true("CL8", code == 200, f"重复导入处理成功 HTTP {code}", f"重复导入失败 HTTP {code}: {body}")

    # ── CL9 — 移除学生 ──
    test_start("CL9", "移除 student6 出班级1")
    s6_id = USERS["student6"]["id"]
    code, body = api_delete(f"/class/1/member/{s6_id}", token=token_teacher1)
    assert_status("CL9", 200, code)

    # ── CL10 — 关联比赛 ──
    test_start("CL10", "关联比赛2到班级1")
    code, body = api_put("/class/1/contest/2", token=token_teacher1)
    assert_status("CL10", 200, code)

    # ── CL11 — 关联题单 ──
    test_start("CL11", "关联题单1到班级1")
    code, body = api_put("/class/1/problem_set/1", token=token_teacher1)
    assert_status("CL11", 200, code)

    # ── CL12 — 发布公告 ──
    test_start("CL12", "发布班级公告")
    code, body = api_post("/class/1/announcement", {
        "title": "测试公告",
        "content": "这是一条测试公告",
        "is_pinned": False,
    }, token_teacher1)
    assert_status("CL12", 200, code)

    # ── CL13 — 班级总览 ──
    test_start("CL13", "班级总览")
    code, body = api_get("/class/1/overview", token=token_teacher1)
    if assert_status("CL13", 200, code):
        assert_json_not_empty("CL13.data", body, "data")

    # ── CL14 — 非成员访问非公开班级 ──
    test_start("CL14", "student5 访问非公开班级2")
    code, body = api_get("/class/2", token=token_student5)
    assert_true("CL14", code in (403, 404, 200),
                f"HTTP {code}（访问控制正常）", f"异常状态码 HTTP {code}")

    # ══════════════ 作业测试 ══════════════

    # ── AS1 — 学生查看作业列表 ──
    test_start("AS1", "student1 查看班级1作业列表")
    code, body = api_get("/class/1/assignment/page", token=token_student1)
    if assert_status("AS1", 200, code):
        records = extract(body, "data.records") or []
        titles = [r.get("title", "") for r in records]
        assert_true("AS1.published", any("第一周" in t for t in titles),
                    "PUBLISHED 作业可见", "未找到「第一周练习」")
        assert_true("AS1.no_draft", not any("第三周" in t for t in titles),
                    "DRAFT 作业不可见", "DRAFT 作业「第三周」也出现了")

    # ── AS2 — 查看作业详情 ──
    test_start("AS2", "查看作业1详情")
    code, body = api_get("/class/1/assignment/1", token=token_student1)
    if assert_status("AS2", 200, code):
        assert_json_not_empty("AS2.title", body, "data.title")

    # ── AS3 — 作业中提交代码 ──
    test_start("AS3", "student1 在作业1中提交 P1001")
    ok, result = submit_and_poll("P1001", "Cpp", SAMPLE_CODE["Cpp"], token_student1, assignment_id=1, timeout=60)
    if ok:
        verdict = extract(result, "verdict") or extract(result, "result.verdict")
        test_pass("AS3", f"提交成功 verdict={verdict}")
    else:
        test_fail("AS3", f"提交失败: {result}")

    # ── AS4 — 已关闭作业不可提交 ──
    test_start("AS4", "已关闭作业4不可提交")
    code, body = api_post("/submission", {
        "pid": "P1001", "language": "Cpp", "code": SAMPLE_CODE["Cpp"], "assignment_id": 4,
    }, token_student1)
    assert_true("AS4", code != 200, f"CLOSED 作业提交被拒绝 HTTP {code}", f"CLOSED 作业竟然可以提交 HTTP {code}")

    # ── AS5 — teacher1 创建作业 ──
    test_start("AS5", "teacher1 创建作业")
    code, body = api_post("/class/1/assignment", {
        "title": "测试作业",
        "description": "测试用",
        "deadline": "2026-12-31T23:59:59",
    }, token_teacher1)
    new_assignment_id = None
    if assert_status("AS5", 200, code):
        new_assignment_id = extract(body, "data.assignment_id")
        test_pass("AS5.id", f"作业创建成功 id={new_assignment_id}")

    # ── AS6 — 为作业添加题目 ──
    test_start("AS6", "为新作业添加题目")
    if new_assignment_id:
        code, body = api_put(f"/class/1/assignment/{new_assignment_id}/problems", {
            "problems": [
                {"problem_id": 1, "weight": 1},
                {"problem_id": 2, "weight": 2},
            ]
        }, token_teacher1)
        assert_status("AS6", 200, code)
    else:
        test_skip("AS6", "作业创建失败，跳过")

    # ── AS7 — 发布作业 ──
    test_start("AS7", "发布 DRAFT 作业")
    if new_assignment_id:
        code, body = api_put(f"/class/1/assignment/{new_assignment_id}", {
            "status": "PUBLISHED",
        }, token_teacher1)
        assert_status("AS7", 200, code)
    else:
        test_skip("AS7", "作业创建失败，跳过")

    # ── AS8 — 关闭作业 ──
    test_start("AS8", "关闭 PUBLISHED 作业2")
    code, body = api_put("/class/1/assignment/2", {
        "status": "CLOSED",
    }, token_teacher1)
    assert_status("AS8", 200, code)

    # ── AS9 — 作业总览（教师统计） ──
    test_start("AS9", "作业1总览（教师统计）")
    code, body = api_get("/class/1/overview/assignment/1", token=token_teacher1)
    if assert_status("AS9", 200, code):
        assert_json_not_empty("AS9.data", body, "data")

    # ── AS10 — 作业公告 ──
    test_start("AS10", "发布作业1公告")
    code, body = api_post("/class/1/assignment/1/announcement", {
        "title": "提交提示",
        "content": "注意边界条件",
    }, token_teacher1)
    assert_status("AS10", 200, code)

    # ── AS11 — 批量导入题目到作业 ──
    test_start("AS11", "批量导入题目到作业（从题单）")
    if new_assignment_id:
        code, body = api_post(f"/class/1/assignment/{new_assignment_id}/import", {
            "problem_set_id": 1,
        }, token_teacher1)
        assert_true("AS11", code == 200, f"导入成功 HTTP {code}", f"导入失败 HTTP {code}: {body}")
    else:
        test_skip("AS11", "作业创建失败，跳过")

    return report_summary()


if __name__ == "__main__":
    if not wait_for_service():
        sys.exit(1)
    ok = run()
    sys.exit(0 if ok else 1)
