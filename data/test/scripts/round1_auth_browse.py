#!/usr/bin/env python3
"""Round 1: 认证 + 只读浏览 (A1-A6, P1-P4, PS1-PS2, C1-C2, C5)"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib.common import *


def run():
    reset_counts()

    # ── A1 — 正常登录 (admin) ──
    test_start("A1", "正常登录 (admin)")
    token_admin = login(USERS["admin"]["email"])
    assert_true("A1", token_admin is not None, "登录成功，获取到 JWT", "登录失败")

    # ── A2 — 错误密码 ──
    test_start("A2", "错误密码")
    code, body = api_post("/auth/login", {"email": USERS["admin"]["email"], "password": "wrongpassword"})
    assert_true("A2", code != 200, f"登录被拒绝 HTTP {code}", f"期望登录失败，实际 HTTP {code}")

    # ── A3 — 注册新用户 ──
    test_start("A3", "注册新用户")
    ok, body = register_user("testuser1", "testuser1@test.local", "Test123456")
    if assert_true("A3", ok, "注册成功", f"注册失败: {body}"):
        token_new = login("testuser1@test.local", "Test123456")
        assert_true("A3.1", token_new is not None, "新用户可登录", "新用户登录失败")

    # ── A4 — 重复邮箱注册 ──
    test_start("A4", "重复邮箱注册")
    ok2, body2 = register_user("duplicate1", "admin@seuoj.local", "Test123456")
    assert_true("A4", not ok2, "重复邮箱注册被拒绝", f"期望注册失败，实际成功: {body2}")

    # ── A8(API) — 各角色登录验证 ──
    tokens = {}
    for uname in ["admin", "manager", "teacher1", "teacher2",
                   "student1", "student2", "student3", "student4", "student5", "student6"]:
        test_start(f"A8-{uname}", f"角色登录验证 ({uname})")
        t = login(USERS[uname]["email"])
        if assert_true(f"A8-{uname}", t is not None, "登录成功", "登录失败"):
            tokens[uname] = t

    # ── P1 — 浏览题库（游客） ──
    test_start("P1", "浏览题库（游客）")
    code, body = api_get("/problem/page", params={"size": "50"})
    if assert_status("P1", 200, code):
        total = extract(body, "data.total")
        assert_json_gt("P1.total", body, "data.total", 0)

    # ── P2 — 搜索题目 ──
    test_start("P2", "搜索题目")
    code, body = api_get("/problem/page", params={"title": "区间"})
    if assert_status("P2", 200, code):
        records = extract(body, "data.records") or []
        found = any("区间" in (r.get("title") or "") for r in records)
        assert_true("P2.result", found, "搜索结果包含「区间」相关题目", "未找到「区间」相关题目")

    # ── P3 — 标签筛选 ──
    test_start("P3", "标签筛选")
    code, body = api_get("/problem/page", params={"tag": "动态规划"})
    if assert_status("P3", 200, code):
        records = extract(body, "data.records") or []
        found = any("最大子段和" in (r.get("title") or "") for r in records)
        if not found:
            code2, body2 = api_get("/problem/page", params={"tag_id": "2"})
            if code2 == 200:
                records2 = extract(body2, "data.records") or []
                found = any("最大子段和" in (r.get("title") or "") for r in records2)
        assert_true("P3.result", found, "标签筛选包含「最大子段和」", "标签筛选未找到预期题目（可能标签参数不同）")

    # ── P4 — 查看题面 ──
    test_start("P4", "查看题面")
    t1 = tokens.get("student1")
    code, body = api_get("/problem/P0001", token=t1)
    if assert_status("P4", 200, code):
        assert_json_not_empty("P4.title", body, "data.title")

    # ── PS1 — 浏览题单列表（游客） ──
    test_start("PS1", "浏览题单列表（游客）")
    code, body = api_get("/problem_set/page")
    if assert_status("PS1", 200, code):
        records = extract(body, "data.records") or []
        titles = [r.get("title", "") for r in records]
        assert_true("PS1.public", any("新手入门" in t for t in titles),
                    "公开题单可见", "未找到公开题单「新手入门题单」")

    # ── PS2 — 查看题单详情 ──
    test_start("PS2", "查看题单详情")
    t1 = tokens.get("student1")
    if t1:
        code, body = api_get("/problem_set/1", token=t1)
        if assert_status("PS2", 200, code):
            assert_json_not_empty("PS2.title", body, "data.title")

    # ── C1 — 浏览比赛列表（游客） ──
    test_start("C1", "浏览比赛列表（游客）")
    code, body = api_get("/contest/page")
    if assert_status("C1", 200, code):
        records = extract(body, "data.records") or []
        titles = [r.get("title", "") for r in records]
        assert_true("C1.public", any("春季训练赛" in t for t in titles),
                    "公开比赛可见", "未找到公开比赛")

    # ── C2 — 查看已结束比赛 ──
    test_start("C2", "查看已结束比赛")
    t1 = tokens.get("student1")
    if t1:
        code, body = api_get("/contest/1", token=t1)
        if assert_status("C2", 200, code):
            assert_json_not_empty("C2.title", body, "data.title")

    # ── C5 — 查看排行榜 ──
    test_start("C5", "查看排行榜（已结束比赛）")
    t1 = tokens.get("student1")
    code, body = api_get("/contest/1/standings", token=t1)
    if assert_status("C5", 200, code):
        assert_json_not_empty("C5.data", body, "data")

    # ── A5 — 忘记密码重置 (student1) ──
    test_start("A5", "忘记密码重置 (student1)")
    code, body = api_post("/auth/reset-password/send-code", {"email": USERS["student1"]["email"]})
    if assert_status("A5.send", 200, code):
        vid = extract(body, "data.verification_id")
        code2, body2 = api_post("/auth/reset-password", {
            "email": USERS["student1"]["email"],
            "verification_id": vid,
            "code": "123456",
            "new_password": "NewPassword123",
        })
        if assert_status("A5.reset", 200, code2):
            new_token = login(USERS["student1"]["email"], "NewPassword123")
            assert_true("A5.login_new", new_token is not None, "新密码可登录", "新密码登录失败")
            old_token = login(USERS["student1"]["email"], "password123")
            assert_true("A5.login_old", old_token is None, "旧密码已失效", "旧密码仍可登录")

    # ── A6 — 修改密码 (student2) ──
    test_start("A6", "修改密码 (student2)")
    t2 = tokens.get("student2")
    if t2:
        code, body = api_post("/auth/change-password", {
            "old_password": "password123",
            "new_password": "Changed123",
        }, token=t2)
        if assert_status("A6.change", 200, code):
            new_t = login(USERS["student2"]["email"], "Changed123")
            assert_true("A6.login_new", new_t is not None, "新密码可登录", "新密码登录失败")

    # ── A7 — 未登录访问受保护页面 (SKIP: UI only) ──
    test_skip("A7", "需浏览器测试：SPA 路由守卫重定向")
    test_skip("A8-UI", "需浏览器测试：不同角色 UI 差异")

    return report_summary()


if __name__ == "__main__":
    if not wait_for_service():
        sys.exit(1)
    ok = run()
    sys.exit(0 if ok else 1)
