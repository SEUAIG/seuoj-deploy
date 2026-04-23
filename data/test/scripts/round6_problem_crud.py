#!/usr/bin/env python3
"""Round 6: 题目 CRUD (P8, P10-P12)"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib.common import *


def run():
    reset_counts()

    token_admin = login(USERS["admin"]["email"])
    if not token_admin:
        test_fail("P-SETUP", "admin 登录失败")
        return report_summary()

    # ── P8 — 创建题目 ──
    test_start("P8", "admin 创建题目 P9999")
    code, body = api_post("/problem", {
        "pid": "P9999",
        "title": "测试题目",
        "is_public": True,
        "description": "这是一道测试题目",
        "input": "两个整数 a, b",
        "output": "a + b 的值",
        "example": [{"in": "1 2", "ans": "3"}],
        "hint": "",
        "tags": [],
    }, token_admin)
    if assert_status("P8", 200, code):
        c2, b2 = api_get("/problem/P9999")
        assert_status("P8.verify", 200, c2)

    # ── P9 — 上传测试数据 (SKIP) ──
    test_skip("P9", "需浏览器测试：multipart 文件上传")

    # ── P10 — 配置判题参数 ──
    test_start("P10", "配置 P9999 判题参数")
    code, body = api_put("/problem/config/P9999", {
        "problem_info": {
            "problem_type": "Standard",
            "checker_type": "Standard",
            "time_limit_ms": 1000,
            "memory_limit_kb": 262144,
        },
        "testcases": [],
    }, token_admin)
    if code == 200:
        test_pass("P10", "判题参数配置成功")
        c2, b2 = api_get("/problem/config/P9999", token=token_admin)
        if c2 == 200:
            test_pass("P10.verify", "配置读取成功")
    else:
        test_fail("P10", f"配置失败 HTTP {code}: {body}")

    # ── P11 — 编辑题目 ──
    test_start("P11", "编辑 P9999 标题")
    code, body = api_patch("/problem/edit", {
        "pid": "P9999",
        "title": "测试题目（已修改）",
    }, token_admin)
    if assert_status("P11", 200, code):
        c2, b2 = api_get("/problem/P9999")
        if c2 == 200:
            title = extract(b2, "data.title")
            assert_json_contains("P11.verify", b2, "data.title", "已修改")

    # ── P12 — 删除题目 ──
    test_start("P12", "删除 P9999")
    code, body = api_delete("/problem/P9999", token=token_admin)
    if assert_status("P12", 200, code):
        c2, b2 = api_get("/problem/P9999")
        assert_true("P12.verify", c2 in (404, 400),
                    f"题目已被删除 HTTP {c2}", f"题目仍存在 HTTP {c2}")

    return report_summary()


if __name__ == "__main__":
    if not wait_for_service():
        sys.exit(1)
    ok = run()
    sys.exit(0 if ok else 1)
