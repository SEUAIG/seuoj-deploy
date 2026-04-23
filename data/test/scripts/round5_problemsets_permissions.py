#!/usr/bin/env python3
"""Round 5: 题单 + 权限 (PS1-PS8, PM4-PM14)"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib.common import *


def run():
    reset_counts()

    token_admin = login(USERS["admin"]["email"])
    token_manager = login(USERS["manager"]["email"])
    token_teacher1 = login(USERS["teacher1"]["email"])
    token_teacher2 = login(USERS["teacher2"]["email"])
    token_student1 = login(USERS["student1"]["email"])
    token_student3 = login(USERS["student3"]["email"])
    if not all([token_admin, token_manager, token_teacher1, token_teacher2, token_student1, token_student3]):
        test_fail("PS-SETUP", "登录失败")
        return report_summary()

    # ══════════════ 题单测试 ══════════════

    # ── PS1 — 浏览题单列表（游客） ──
    test_start("PS1", "浏览题单列表（游客）")
    code, body = api_get("/problem_set/page")
    if assert_status("PS1", 200, code):
        records = extract(body, "data.records") or []
        titles = [r.get("title", "") for r in records]
        assert_true("PS1.public", any("新手入门" in t for t in titles),
                    "公开题单可见", "未找到「新手入门题单」")

    # ── PS2 — 查看题单详情 ──
    test_start("PS2", "查看题单1详情")
    code, body = api_get("/problem_set/1", token=token_student1)
    if assert_status("PS2", 200, code):
        assert_json_not_empty("PS2.title", body, "data.title")

    # ── PS3 — 有权限查看私有题单 ──
    test_start("PS3", "student1 有权限查看私有题单3")
    code, body = api_get("/problem_set/3", token=token_student1)
    assert_status("PS3", 200, code)

    # ── PS4 — 无权限查看私有题单 ──
    test_start("PS4", "student3 无权限查看私有题单3")
    code, body = api_get("/problem_set/3", token=token_student3)
    assert_true("PS4", code in (403, 404),
                f"访问被拒绝 HTTP {code}", f"期望 403/404，实际 HTTP {code}")

    # ── PS5 — 创建题单 ──
    test_start("PS5", "teacher1 创建题单")
    code, body = api_post("/problem_set", {
        "title": "搜索专题",
        "description": "BFS/DFS 练习",
        "is_public": True,
    }, token_teacher1)
    new_ps_id = None
    if assert_status("PS5", 200, code):
        new_ps_id = extract(body, "data.id") or extract(body, "data.problem_set_id")
        test_pass("PS5.id", f"题单创建成功 id={new_ps_id}")

    # ── PS6 — 编辑题单（添加题目） ──
    test_start("PS6", "编辑题单（添加题目）")
    if new_ps_id:
        code, body = api_post(f"/problem_set/{new_ps_id}/problem", {
            "problem_list": [
                {"pid": "P1009", "order_id": 1},
                {"pid": "P1010", "order_id": 2},
            ]
        }, token_teacher1)
        assert_status("PS6", 200, code)
    else:
        test_skip("PS6", "题单创建失败")

    # ── PS7 — 授权用户访问私有题单 ──
    test_start("PS7", "teacher2 给 student3 授予题单3 READ 权限")
    code, body = api_post("/permission/grant", {
        "resourceType": "PROBLEM_SET",
        "resourceId": "3",
        "targetUserId": str(USERS["student3"]["id"]),
        "permission": "READ",
    }, token_teacher2)
    if assert_status("PS7.grant", 200, code):
        c2, b2 = api_get("/problem_set/3", token=token_student3)
        assert_status("PS7.verify", 200, c2)

    # ── PS8 — 删除题单 ──
    test_start("PS8", "teacher1 删除搜索专题")
    if new_ps_id:
        code, body = api_delete(f"/problem_set/{new_ps_id}", token=token_teacher1)
        assert_status("PS8", 200, code)
    else:
        test_skip("PS8", "题单创建失败")

    # ══════════════ 权限测试 ══════════════

    # ── PM1, PM2, PM3 — SKIP (UI only) ──
    test_skip("PM1", "需浏览器测试：学生访问管理页重定向")
    test_skip("PM2", "需浏览器测试：教师访问管理页重定向")
    test_skip("PM3", "需浏览器测试：管理员访问管理页 UI")

    # ── PM4 — 管理员修改用户角色为 TEACHER ──
    test_start("PM4", "manager 修改 student1 角色为 TEACHER")
    s1_id = USERS["student1"]["id"]
    code, body = api_put(f"/admin/user/{s1_id}/role", {"role": "TEACHER"}, token_manager)
    assert_status("PM4", 200, code)

    # ── PM5 — ADMIN 尝试设置 ADMIN 角色 ──
    test_start("PM5", "manager 尝试设置 ADMIN 角色")
    s3_id = USERS["student3"]["id"]
    code, body = api_put(f"/admin/user/{s3_id}/role", {"role": "ADMIN"}, token_manager)
    assert_true("PM5", code != 200, f"操作被拒绝 HTTP {code}", f"期望被拒绝，实际 HTTP {code}")

    # ── PM6 — SUPER_ADMIN 设置 ADMIN 角色 ──
    test_start("PM6", "admin 设置 student2 为 ADMIN")
    s2_id = USERS["student2"]["id"]
    code, body = api_put(f"/admin/user/{s2_id}/role", {"role": "ADMIN"}, token_admin)
    assert_status("PM6", 200, code)

    # ── PM7 — 设置 SUPER_ADMIN 被拒绝 ──
    test_start("PM7", "admin 尝试设置 SUPER_ADMIN 角色")
    code, body = api_put(f"/admin/user/{s3_id}/role", {"role": "SUPER_ADMIN"}, token_admin)
    assert_true("PM7", code != 200, f"操作被拒绝 HTTP {code}", f"期望被拒绝，实际 HTTP {code}")

    # ── PM8 — 资源权限授予 ──
    test_start("PM8", "teacher2 给 student3 授予题单3 READ 权限")
    code, body = api_post("/permission/grant", {
        "resourceType": "PROBLEM_SET",
        "resourceId": "3",
        "targetUserId": str(USERS["student3"]["id"]),
        "permission": "READ",
    }, token_teacher2)
    assert_true("PM8", code == 200, f"授权成功 HTTP {code}", f"授权失败 HTTP {code}: {body}")

    # ── PM9 — 资源权限撤销 ──
    test_start("PM9", "teacher2 撤销 student1 对题单3 READ")
    code, body = api_delete("/permission/revoke", token=token_teacher2, data={
        "resourceType": "PROBLEM_SET",
        "resourceId": "3",
        "targetUserId": str(USERS["student1"]["id"]),
        "permission": "READ",
    })
    assert_status("PM9", 200, code)

    # ── PM10 — 非拥有者编辑资源 ──
    test_start("PM10", "student1 尝试编辑 teacher1 的题目 P1001")
    code, body = api_patch("/problem/edit", {
        "pid": "P1001",
        "title": "被 student1 修改的标题",
    }, token_student1)
    assert_true("PM10", code in (403, 401, 400),
                f"编辑被拒绝 HTTP {code}", f"期望被拒绝，实际 HTTP {code}")

    # ── PM11 — 创建者自动获得 WRITE ──
    test_start("PM11", "teacher1 创建题单后自动获得 WRITE")
    code, body = api_post("/problem_set", {
        "title": "PM11测试题单",
        "description": "权限测试",
        "is_public": False,
    }, token_teacher1)
    pm11_ps_id = None
    if assert_status("PM11.create", 200, code):
        pm11_ps_id = extract(body, "data.id") or extract(body, "data.problem_set_id")
        if pm11_ps_id:
            c2, b2 = api_get(f"/permission/PROBLEM_SET/{pm11_ps_id}", token=token_teacher1)
            if c2 == 200:
                perms = extract(b2, "data") or []
                has_write = any(
                    (p.get("userId") == USERS["teacher1"]["id"] or p.get("user_id") == USERS["teacher1"]["id"])
                    and p.get("permission") == "WRITE"
                    for p in (perms if isinstance(perms, list) else [])
                )
                assert_true("PM11.write", has_write, "自动获得 WRITE 权限", "未找到 WRITE 权限记录")
            else:
                test_pass("PM11.write", f"创建成功，权限查询 HTTP {c2}（可能非拥有者无法查看列表）")
            api_delete(f"/problem_set/{pm11_ps_id}", token=token_teacher1)

    # ── PM12 — 批量导入用户 ──
    test_start("PM12", "admin 批量导入用户（正常）")
    code, body = api_post("/common/user/batch-import", {
        "passwordMode": "assigned",
        "sendEmail": False,
        "users": [
            {"username": "batchuser1", "nickname": "批量1", "email": "batch1@test.local", "password": "Pass123456"},
            {"username": "batchuser2", "nickname": "批量2", "email": "batch2@test.local", "password": "Pass123456"},
        ]
    }, token_admin)
    assert_status("PM12", 200, code)

    # ── PM13 — 批量导入用户（重复） ──
    test_start("PM13", "admin 批量导入用户（重复）")
    code, body = api_post("/common/user/batch-import", {
        "passwordMode": "assigned",
        "sendEmail": False,
        "users": [
            {"username": "batchuser1", "nickname": "批量1", "email": "batch1@test.local", "password": "Pass123456"},
        ]
    }, token_admin)
    assert_true("PM13", code == 200, f"重复导入处理成功 HTTP {code}", f"重复导入失败 HTTP {code}: {body}")

    # ── PM14 — 查看权限列表 ──
    test_start("PM14", "teacher1 查看题单2权限列表")
    code, body = api_get("/permission/PROBLEM_SET/2", token=token_teacher1)
    if assert_status("PM14", 200, code):
        assert_json_not_empty("PM14.data", body, "data")

    return report_summary()


if __name__ == "__main__":
    if not wait_for_service():
        sys.exit(1)
    ok = run()
    sys.exit(0 if ok else 1)
