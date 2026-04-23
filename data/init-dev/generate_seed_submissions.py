#!/usr/bin/env python3
"""
生成幂等的 dev seed 提交数据。
输出：
  - data/init-dev/08-seed-submissions.sql
  - data/backend-seed/user-code/*.txt
"""
import json
import os
import random
import sys
from pathlib import Path

random.seed(42)

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
SQL_OUTPUT = SCRIPT_DIR / "08-seed-submissions.sql"
CODE_OUTPUT_DIR = REPO_ROOT / "data" / "backend-seed" / "user-code"

# ---------------------------------------------------------------------------
# 题目元数据：(problem_id, pid, title, num_testcases, time_limit_ms, mem_limit_kb)
# ---------------------------------------------------------------------------
PROBLEMS = [
    (1,  "P0001", "a+b",            1,  1000, 262144),
    (2,  "P0002", "数组求和",        2,  1000, 256000),
    (3,  "P1001", "区间求和",        10, 1000, 262144),
    (4,  "P1002", "最大子段和",      10, 1000, 262144),
    (5,  "P1003", "括号序列的深度",  10, 1000, 262144),
    (6,  "P1004", "两数之和",        10, 1000, 262144),
    (7,  "P1005", "切绳子",          10, 1000, 262144),
    (8,  "P1006", "合并果子",        10, 1000, 262144),
    (9,  "P1007", "逆序对",          10, 1000, 262144),
    (10, "P1008", "重排回文",        10, 1000, 262144),
    (11, "P1009", "迷宫寻路",        10, 1000, 262144),
    (12, "P1010", "岛屿计数",        10, 1000, 262144),
]

PROB_META = {p[0]: {"pid": p[1], "title": p[2], "ntc": p[3], "tl": p[4], "ml": p[5]} for p in PROBLEMS}

# 期望统计
EXPECTED = {
    1:  (10, 8), 2:  (6, 4), 3:  (5, 3), 4:  (4, 2),
    5:  (3, 1),  6:  (8, 6), 7:  (3, 2), 8:  (4, 2),
    9:  (2, 1),  10: (3, 1), 11: (5, 2), 12: (4, 1),
}

# ---------------------------------------------------------------------------
# 57 条提交分配表
# (submission_id, user_id, problem_id, language, verdict, context_type, context_id)
# context_type: 'contest' | 'assignment' | 'free'
# ---------------------------------------------------------------------------
SUBMISSIONS = [
    # P0001: 10 submit, 8 accept
    (1,  5,  1, "Cpp",        "Accepted",              "contest", 1),
    (2,  6,  1, "Java17",     "Accepted",              "contest", 1),
    (3,  7,  1, "Python3_12", "Accepted",              "contest", 1),
    (4,  8,  1, "C",          "Accepted",              "contest", 1),
    (5,  9,  1, "Cpp",        "Accepted",              "contest", 1),
    (6,  10, 1, "Cpp",        "Accepted",              "contest", 1),
    (7,  5,  1, "Cpp",        "Accepted",              "assignment", 4),
    (8,  6,  1, "Java17",     "WrongAnswer",           "assignment", 4),
    (9,  9,  1, "Cpp17",      "Accepted",              "free", None),
    (10, 10, 1, "C",          "WrongAnswer",           "free", None),
    # P0002: 6 submit, 4 accept
    (11, 5,  2, "Cpp",        "WrongAnswer",           "contest", 1),
    (12, 5,  2, "Cpp",        "Accepted",              "contest", 1),
    (13, 6,  2, "Java17",     "TimeLimitExceeded",     "contest", 1),
    (14, 7,  2, "Python3_12", "Accepted",              "free", None),
    (15, 8,  2, "C",          "Accepted",              "free", None),
    (16, 9,  2, "Cpp",        "Accepted",              "free", None),
    # P1001: 5 submit, 3 accept
    (17, 7,  3, "Python3_12", "RuntimeError",          "contest", 1),
    (18, 5,  3, "Cpp",        "Accepted",              "assignment", 1),
    (19, 6,  3, "Java17",     "Accepted",              "assignment", 1),
    (20, 9,  3, "Cpp",        "Accepted",              "free", None),
    (21, 10, 3, "C",          "WrongAnswer",           "free", None),
    # P1002: 4 submit, 2 accept
    (22, 5,  4, "Cpp",        "Accepted",              "contest", 2),
    (23, 6,  4, "Java17",     "WrongAnswer",           "contest", 2),
    (24, 7,  4, "Cpp",        "Accepted",              "contest", 2),
    (25, 8,  4, "C",          "TimeLimitExceeded",     "free", None),
    # P1003: 3 submit, 1 accept
    (26, 5,  5, "Cpp",        "Accepted",              "contest", 2),
    (27, 8,  5, "C",          "WrongAnswer",           "contest", 2),
    (28, 7,  5, "Python3_12", "RuntimeError",          "assignment", 1),
    # P1004: 8 submit, 6 accept
    (29, 5,  6, "Cpp",        "Accepted",              "contest", 2),
    (30, 6,  6, "Java17",     "Accepted",              "contest", 2),
    (31, 7,  6, "Cpp17",      "Accepted",              "contest", 2),
    (32, 8,  6, "C",          "Accepted",              "assignment", 1),
    (33, 9,  6, "Cpp",        "Accepted",              "assignment", 1),
    (34, 10, 6, "Python3_12", "WrongAnswer",           "assignment", 1),
    (35, 5,  6, "Cpp",        "Accepted",              "free", None),
    (36, 9,  6, "Cpp",        "MemoryLimitExceeded",   "free", None),
    # P1005: 3 submit, 2 accept
    (37, 6,  7, "Java17",     "WrongAnswer",           "contest", 2),
    (38, 8,  7, "C",          "Accepted",              "contest", 2),
    (39, 5,  7, "Cpp",        "Accepted",              "assignment", 2),
    # P1006: 4 submit, 2 accept
    (40, 5,  8, "Cpp",        "Accepted",              "assignment", 2),
    (41, 6,  8, "Java17",     "TimeLimitExceeded",     "assignment", 2),
    (42, 7,  8, "Cpp17",      "Accepted",              "free", None),
    (43, 8,  8, "C",          "WrongAnswer",           "free", None),
    # P1007: 2 submit, 1 accept
    (44, 7,  9, "Cpp",        "Accepted",              "assignment", 2),
    (45, 8,  9, "C",          "RuntimeError",          "free", None),
    # P1008: 3 submit, 1 accept
    (46, 5,  10, "Cpp",        "Accepted",             "free", None),
    (47, 6,  10, "Java17",     "WrongAnswer",          "free", None),
    (48, 7,  10, "Python3_12", "TimeLimitExceeded",    "free", None),
    # P1009: 5 submit, 2 accept
    (49, 5,  11, "Cpp",        "Accepted",             "free", None),
    (50, 6,  11, "Java17",     "WrongAnswer",          "free", None),
    (51, 7,  11, "Cpp17",      "Accepted",             "free", None),
    (52, 8,  11, "C",          "RuntimeError",         "free", None),
    (53, 9,  11, "Cpp",        "MemoryLimitExceeded",  "free", None),
    # P1010: 4 submit, 1 accept
    (54, 6,  12, "Java17",     "WrongAnswer",          "free", None),
    (55, 7,  12, "Cpp",        "Accepted",             "free", None),
    (56, 8,  12, "C",          "TimeLimitExceeded",    "free", None),
    (57, 10, 12, "Python3_12", "WrongAnswer",          "free", None),
]

# ---------------------------------------------------------------------------
# 时间戳策略
# ---------------------------------------------------------------------------
# Contest 1: 2026-03-01 09:00 ~ 12:00
# Contest 2: 2026-04-01 09:00 ~ ongoing
# Assignment 1: visible_from 2026-03-01
# Assignment 2: visible_from 2026-03-08
# Assignment 4: closed, was 2026-01-15 ~ 2026-02-15

def make_timestamp(sub_id, context_type, context_id):
    if context_type == "contest" and context_id == 1:
        base_min = 10 + (sub_id - 1) * 7
        h, m = divmod(base_min, 60)
        return f"2026-03-01 {9+h:02d}:{m:02d}:00"
    elif context_type == "contest" and context_id == 2:
        base_min = 10 + (sub_id - 22) * 8
        h, m = divmod(base_min, 60)
        return f"2026-04-01 {9+h:02d}:{m:02d}:00"
    elif context_type == "assignment" and context_id == 1:
        day = 10 + (sub_id % 5)
        hour = 9 + (sub_id % 8)
        return f"2026-03-{day:02d} {hour:02d}:{(sub_id*7)%60:02d}:00"
    elif context_type == "assignment" and context_id == 2:
        day = 15 + (sub_id % 5)
        hour = 10 + (sub_id % 6)
        return f"2026-03-{day:02d} {hour:02d}:{(sub_id*7)%60:02d}:00"
    elif context_type == "assignment" and context_id == 4:
        day = 1 + (sub_id % 10)
        return f"2026-02-{day:02d} 14:{(sub_id*11)%60:02d}:00"
    else:  # free
        day = 15 + (sub_id % 14)
        hour = 8 + (sub_id % 10)
        return f"2026-04-{day:02d} {hour:02d}:{(sub_id*13)%60:02d}:00"

def finish_time(submit_time, sub_id):
    # 评测耗时 3-12 秒
    secs = 3 + (sub_id * 7) % 10
    # 简单地在秒字段上加
    return submit_time[:-2] + f"{secs:02d}"


# ---------------------------------------------------------------------------
# submission_no: 确定性
# ---------------------------------------------------------------------------
def make_submission_no(sub_id):
    return f"00000000-0000-0000-0000-{sub_id:012d}"


# ---------------------------------------------------------------------------
# result_detail JSON 生成
# ---------------------------------------------------------------------------
def make_result_detail(problem_id, verdict, sub_id):
    meta = PROB_META[problem_id]
    ntc = meta["ntc"]
    tl = meta["tl"]
    ml = meta["ml"]

    items = []
    if verdict == "Accepted":
        for tc in range(1, ntc + 1):
            t = random.randint(5, min(200, tl - 100))
            m = random.randint(1024000, 30 * 1024 * 1024)
            items.append({
                "id": tc, "in": f"(test {tc} input)", "out": "(output)",
                "ans": "(output)", "sys": "ok", "time": t, "mem": m,
                "type": "Accepted", "score": 100 // ntc + (1 if tc <= 100 % ntc else 0),
            })
    else:
        fail_at = random.randint(1, ntc)
        for tc in range(1, ntc + 1):
            if tc < fail_at:
                t = random.randint(5, 150)
                m = random.randint(1024000, 20 * 1024 * 1024)
                items.append({
                    "id": tc, "in": f"(test {tc} input)", "out": "(output)",
                    "ans": "(output)", "sys": "ok", "time": t, "mem": m,
                    "type": "Accepted", "score": 100 // ntc,
                })
            elif tc == fail_at:
                if verdict == "WrongAnswer":
                    t = random.randint(10, 200)
                    m = random.randint(1024000, 20 * 1024 * 1024)
                    items.append({
                        "id": tc, "in": f"(test {tc} input)", "out": "(wrong)",
                        "ans": "(expected)", "sys": "wrong answer: expected '5', got '3'",
                        "time": t, "mem": m, "type": "WrongAnswer", "score": 0,
                    })
                elif verdict == "TimeLimitExceeded":
                    items.append({
                        "id": tc, "in": f"(test {tc} input)", "out": "",
                        "ans": "(expected)", "sys": "time limit exceeded",
                        "time": tl, "mem": random.randint(1024000, 20 * 1024 * 1024),
                        "type": "TimeLimitExceeded", "score": 0,
                    })
                elif verdict == "RuntimeError":
                    items.append({
                        "id": tc, "in": f"(test {tc} input)", "out": "",
                        "ans": "(expected)", "sys": "runtime error: segmentation fault",
                        "time": random.randint(1, 50), "mem": random.randint(1024000, 10 * 1024 * 1024),
                        "type": "RuntimeError", "score": 0,
                    })
                elif verdict == "MemoryLimitExceeded":
                    items.append({
                        "id": tc, "in": f"(test {tc} input)", "out": "",
                        "ans": "(expected)", "sys": "memory limit exceeded",
                        "time": random.randint(50, 500),
                        "mem": ml * 1024, "type": "MemoryLimitExceeded", "score": 0,
                    })
                else:
                    items.append({
                        "id": tc, "in": f"(test {tc} input)", "out": "",
                        "ans": "(expected)", "sys": verdict,
                        "time": 0, "mem": 0, "type": verdict, "score": 0,
                    })
            else:
                items.append({
                    "id": tc, "in": f"(test {tc} input)", "out": "",
                    "ans": "", "sys": "skipped", "time": 0, "mem": 0,
                    "type": "Skipped", "score": 0,
                })
    return items


def compute_score(result_detail):
    return sum(item["score"] for item in result_detail)


# ---------------------------------------------------------------------------
# 源码模板
# ---------------------------------------------------------------------------
CODE_TEMPLATES = {
    ("Cpp", "Accepted"): '#include <iostream>\nusing namespace std;\n// {title}\nint main() {{\n    int a, b;\n    cin >> a >> b;\n    cout << a + b << endl;\n    return 0;\n}}\n',
    ("Cpp", "WrongAnswer"): '#include <iostream>\nusing namespace std;\n// {title} - wrong\nint main() {{\n    int a, b;\n    cin >> a >> b;\n    cout << a - b << endl;  // bug: subtraction\n    return 0;\n}}\n',
    ("Cpp", "TimeLimitExceeded"): '#include <iostream>\nusing namespace std;\n// {title} - TLE\nint main() {{\n    int a, b;\n    cin >> a >> b;\n    while(true) a++;  // infinite loop\n    cout << a + b << endl;\n    return 0;\n}}\n',
    ("Cpp", "RuntimeError"): '#include <iostream>\nusing namespace std;\n// {title} - RE\nint main() {{\n    int a[1];\n    a[1000000] = 42;  // segfault\n    return 0;\n}}\n',
    ("Cpp", "MemoryLimitExceeded"): '#include <iostream>\n#include <vector>\nusing namespace std;\n// {title} - MLE\nint main() {{\n    vector<int> v(500000000);  // ~2GB\n    cout << v[0] << endl;\n    return 0;\n}}\n',
    ("Cpp17", "Accepted"): '#include <iostream>\n#include <numeric>\n#include <vector>\nusing namespace std;\n// {title}\nint main() {{\n    int n; cin >> n;\n    vector<int> v(n);\n    for (auto& x : v) cin >> x;\n    cout << reduce(v.begin(), v.end()) << endl;\n}}\n',
    ("Cpp17", "WrongAnswer"): '#include <iostream>\nusing namespace std;\n// {title} - wrong\nint main() {{\n    int n; cin >> n;\n    cout << n - 1 << endl;  // wrong\n}}\n',
    ("C", "Accepted"): '#include <stdio.h>\n// {title}\nint main() {{\n    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("%d\\n", a + b);\n    return 0;\n}}\n',
    ("C", "WrongAnswer"): '#include <stdio.h>\n// {title} - wrong\nint main() {{\n    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("%d\\n", a * b);  // wrong op\n    return 0;\n}}\n',
    ("C", "TimeLimitExceeded"): '#include <stdio.h>\n// {title} - TLE\nint main() {{\n    int a;\n    scanf("%d", &a);\n    while(1) a++;\n    return 0;\n}}\n',
    ("C", "RuntimeError"): '#include <stdio.h>\n#include <stdlib.h>\n// {title} - RE\nint main() {{\n    int *p = NULL;\n    printf("%d\\n", *p);  // null deref\n    return 0;\n}}\n',
    ("C", "MemoryLimitExceeded"): '#include <stdio.h>\n#include <stdlib.h>\n// {title} - MLE\nint main() {{\n    int *p = malloc(2000000000LL);\n    p[0] = 1;\n    printf("%d\\n", p[0]);\n    return 0;\n}}\n',
    ("Java17", "Accepted"): 'import java.util.Scanner;\n// {title}\npublic class Main {{\n    public static void main(String[] args) {{\n        Scanner sc = new Scanner(System.in);\n        int a = sc.nextInt(), b = sc.nextInt();\n        System.out.println(a + b);\n    }}\n}}\n',
    ("Java17", "WrongAnswer"): 'import java.util.Scanner;\n// {title} - wrong\npublic class Main {{\n    public static void main(String[] args) {{\n        Scanner sc = new Scanner(System.in);\n        int a = sc.nextInt();\n        System.out.println(a);  // missing b\n    }}\n}}\n',
    ("Java17", "TimeLimitExceeded"): '// {title} - TLE\npublic class Main {{\n    public static void main(String[] args) {{\n        while(true) {{}}\n    }}\n}}\n',
    ("Java17", "RuntimeError"): '// {title} - RE\npublic class Main {{\n    public static void main(String[] args) {{\n        int[] a = new int[1];\n        System.out.println(a[100]);  // AIOOB\n    }}\n}}\n',
    ("Python3_12", "Accepted"): '# {title}\na, b = map(int, input().split())\nprint(a + b)\n',
    ("Python3_12", "WrongAnswer"): '# {title} - wrong\na, b = map(int, input().split())\nprint(a - b)  # wrong\n',
    ("Python3_12", "TimeLimitExceeded"): '# {title} - TLE\nimport time\na, b = map(int, input().split())\nwhile True:\n    pass\n',
    ("Python3_12", "RuntimeError"): '# {title} - RE\na, b = map(int, input().split())\nprint(1 // 0)  # division by zero\n',
}


def make_source_code(language, verdict, title):
    # 找最接近的模板
    key = (language, verdict)
    if key not in CODE_TEMPLATES:
        # 回退：用同语言 Accepted
        base_lang = language.replace("17", "").replace("3_12", "")
        for fallback_lang in [language, base_lang, "Cpp"]:
            fk = (fallback_lang, verdict)
            if fk in CODE_TEMPLATES:
                key = fk
                break
            fk2 = (fallback_lang, "Accepted")
            if fk2 in CODE_TEMPLATES:
                key = fk2
                break
    template = CODE_TEMPLATES.get(key, f"// {title}\n// {language} {verdict}\n")
    return template.format(title=title)


# ---------------------------------------------------------------------------
# 自检
# ---------------------------------------------------------------------------
def verify_counts():
    from collections import defaultdict
    submit_count = defaultdict(int)
    accept_count = defaultdict(int)
    for s in SUBMISSIONS:
        submit_count[s[3 - 1]] += 1  # problem_id is index 2
        if s[4] == "Accepted":       # verdict is index 4
            accept_count[s[2]] += 1
        submit_count[s[2]] = submit_count.get(s[2], 0)  # ensure exists

    # 重新计算
    sc = defaultdict(int)
    ac = defaultdict(int)
    for sub_id, user_id, problem_id, lang, verdict, ctx_type, ctx_id in SUBMISSIONS:
        sc[problem_id] += 1
        if verdict == "Accepted":
            ac[problem_id] += 1

    ok = True
    for pid, (exp_s, exp_a) in EXPECTED.items():
        if sc[pid] != exp_s:
            print(f"ASSERT FAIL: problem {pid} total_submit expected {exp_s}, got {sc[pid]}")
            ok = False
        if ac[pid] != exp_a:
            print(f"ASSERT FAIL: problem {pid} total_accept expected {exp_a}, got {ac[pid]}")
            ok = False
    if not ok:
        sys.exit(1)
    print(f"Self-check: 57 submissions, counts verified OK")


# ---------------------------------------------------------------------------
# SQL 生成
# ---------------------------------------------------------------------------
def escape_sql_string(s):
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")


def generate_sql():
    lines = []
    lines.append("USE seuoj;")
    lines.append("")
    lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    lines.append("")

    # --- submissions ---
    lines.append("-- 57 条提交记录")
    lines.append("INSERT INTO `submission` (id, submission_no, user_id, problem_id, language, assignment_id, status, verdict, score, submit_time, finish_time, is_del)")
    lines.append("VALUES")

    sub_values = []
    for sub_id, user_id, problem_id, lang, verdict, ctx_type, ctx_id in SUBMISSIONS:
        sno = make_submission_no(sub_id)
        asn_id = ctx_id if ctx_type == "assignment" else None
        st = make_timestamp(sub_id, ctx_type, ctx_id)
        ft = finish_time(st, sub_id)
        rd = make_result_detail(problem_id, verdict, sub_id)
        score = compute_score(rd)
        asn_sql = str(asn_id) if asn_id else "NULL"
        sub_values.append(
            f"       ({sub_id}, '{sno}', {user_id}, {problem_id}, '{lang}', {asn_sql}, "
            f"'Finished', '{verdict}', {score}, '{st}', '{ft}', 0)"
        )
    lines.append(",\n".join(sub_values) + ";")
    lines.append("")

    # --- submission_detail ---
    lines.append("-- 57 条提交详情")
    lines.append("INSERT INTO `submission_detail` (submission_id, result_detail, subtasks, error_detail)")
    lines.append("VALUES")

    detail_values = []
    for sub_id, user_id, problem_id, lang, verdict, ctx_type, ctx_id in SUBMISSIONS:
        rd = make_result_detail(problem_id, verdict, sub_id)
        rd_json = escape_sql_string(json.dumps(rd, ensure_ascii=False))
        error = "NULL"
        if verdict == "RuntimeError":
            error = "'Segmentation fault (core dumped)'"
        detail_values.append(
            f"       ({sub_id}, '{rd_json}', NULL, {error})"
        )
    lines.append(",\n".join(detail_values) + ";")
    lines.append("")

    # --- contest_submission ---
    contest_subs = [(sub_id, ctx_id) for sub_id, _, _, _, _, ctx_type, ctx_id in SUBMISSIONS if ctx_type == "contest"]
    if contest_subs:
        lines.append("-- 比赛提交关联")
        lines.append("INSERT INTO `contest_submission` (id, contest_id, submission_id, is_del)")
        lines.append("VALUES")
        cs_values = []
        for cs_id, (sub_id, contest_id) in enumerate(contest_subs, 1):
            cs_values.append(f"       ({cs_id}, {contest_id}, {sub_id}, 0)")
        lines.append(",\n".join(cs_values) + ";")
        lines.append("")

    lines.append("SET FOREIGN_KEY_CHECKS = 1;")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 源码文件生成
# ---------------------------------------------------------------------------
def generate_code_files():
    CODE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for sub_id, user_id, problem_id, lang, verdict, ctx_type, ctx_id in SUBMISSIONS:
        sno = make_submission_no(sub_id)
        title = PROB_META[problem_id]["title"]
        code = make_source_code(lang, verdict, title)
        filepath = CODE_OUTPUT_DIR / f"{sno}.txt"
        filepath.write_text(code, encoding="utf-8")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    verify_counts()

    # 重置随机种子以保证 result_detail 确定性
    random.seed(42)

    sql = generate_sql()
    SQL_OUTPUT.write_text(sql, encoding="utf-8")
    print(f"Generated: {SQL_OUTPUT}")

    # 再次重置随机种子（result_detail 在 generate_sql 中也用了 random）
    random.seed(42)
    generate_code_files()
    print(f"Generated: {len(SUBMISSIONS)} code files in {CODE_OUTPUT_DIR}")

    print("Done!")


if __name__ == "__main__":
    main()
