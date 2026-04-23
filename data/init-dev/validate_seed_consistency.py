#!/usr/bin/env python3
"""
验证 dev seed 数据一致性。
直接解析 SQL 文件，检查 submission 与 problem 计数、外键、详情完整性等。
"""
import re
import os
import sys
from pathlib import Path
from collections import defaultdict

SEED_DIR = Path(__file__).parent
REPO_ROOT = SEED_DIR.parent.parent
BACKEND_SEED_CODE_DIR = REPO_ROOT / "data" / "backend-seed" / "user-code"

VALID_LANGUAGES = {"C", "Cpp", "Cpp11", "Cpp17", "Cpp20", "Python3_12", "Nodejs22", "Go1_22", "Java17"}

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def extract_inserts_with_columns(sql_text, table_name):
    """从 SQL 文本中提取指定表的 INSERT 语句，返回 (column_list, rows) 列表。"""
    pattern = re.compile(
        rf"INSERT\s+INTO\s+`?{table_name}`?\s*\(([^)]+)\)\s*VALUES\s*(.*?);",
        re.IGNORECASE | re.DOTALL,
    )
    results = []
    for m in pattern.finditer(sql_text):
        col_str = m.group(1)
        columns = [c.strip().strip("`") for c in col_str.split(",")]
        values_block = m.group(2)
        rows = []
        i = 0
        while i < len(values_block):
            if values_block[i] == "(":
                depth = 1
                start = i + 1
                i += 1
                in_q = False
                q_ch = None
                while i < len(values_block) and depth > 0:
                    ch = values_block[i]
                    if in_q:
                        if ch == q_ch and (i + 1 >= len(values_block) or values_block[i + 1] != q_ch):
                            in_q = False
                        elif ch == q_ch:
                            i += 1
                    else:
                        if ch in ("'", '"'):
                            in_q = True
                            q_ch = ch
                        elif ch == "(":
                            depth += 1
                        elif ch == ")":
                            depth -= 1
                    i += 1
                rows.append(values_block[start : i - 1])
            else:
                i += 1
        results.append((columns, rows))
    return results


def parse_csv_row(row_str):
    """简单解析 SQL VALUES 行为字段列表（处理引号字符串、NULL 和函数调用如 UUID()）"""
    fields = []
    current = ""
    in_quote = False
    quote_char = None
    paren_depth = 0
    i = 0
    while i < len(row_str):
        ch = row_str[i]
        if in_quote:
            if ch == quote_char and (i + 1 >= len(row_str) or row_str[i + 1] != quote_char):
                in_quote = False
                current += ch
            elif ch == quote_char and i + 1 < len(row_str) and row_str[i + 1] == quote_char:
                current += ch + ch
                i += 1
            else:
                current += ch
        else:
            if ch in ("'", '"'):
                in_quote = True
                quote_char = ch
                current += ch
            elif ch == "(":
                paren_depth += 1
                current += ch
            elif ch == ")":
                paren_depth -= 1
                current += ch
            elif ch == "," and paren_depth == 0:
                fields.append(current.strip())
                current = ""
            else:
                current += ch
        i += 1
    if current.strip():
        fields.append(current.strip())
    return fields


def parse_rows_as_dicts(sql_text, table_name):
    """解析 INSERT 语句，返回 list of dict（列名 → 值字符串）"""
    results = []
    for columns, rows in extract_inserts_with_columns(sql_text, table_name):
        for row_str in rows:
            fields = parse_csv_row(row_str)
            d = {}
            for i, col in enumerate(columns):
                if i < len(fields):
                    d[col] = fields[i].strip()
                else:
                    d[col] = "NULL"
            results.append(d)
    return results


def get_val(d, key, as_int=False):
    """从 dict 获取值，去引号，处理 NULL"""
    raw = d.get(key, "NULL")
    if raw.upper() == "NULL":
        return None
    val = strip_quotes(raw)
    if as_int:
        return int(val)
    return val


def strip_quotes(val):
    """去掉字符串两端的单引号/双引号"""
    val = val.strip()
    if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
        return val[1:-1]
    return val


def read_all_sql():
    """读取所有 seed SQL 文件并合并"""
    sql_files = sorted(SEED_DIR.glob("*.sql"))
    combined = {}
    for f in sql_files:
        combined[f.name] = f.read_text(encoding="utf-8")
    return combined


def main():
    print("=" * 60)
    print("SEUOJ Dev Seed 数据一致性验证")
    print("=" * 60)

    sql_files = read_all_sql()
    all_sql = "\n".join(sql_files.values())

    # --- 解析 problem 表 ---
    problem_dicts = parse_rows_as_dicts(all_sql, "problem")
    problems = {}
    for d in problem_dicts:
        pid_id = get_val(d, "id", as_int=True)
        if pid_id is None:
            continue
        problems[pid_id] = {
            "pid": get_val(d, "pid"),
            "total_submit": get_val(d, "total_submit", as_int=True) or 0,
            "total_accept": get_val(d, "total_accept", as_int=True) or 0,
        }
    print(f"\n[INFO] 解析到 {len(problems)} 个题目")

    # --- 解析 user_info 表 ---
    user_dicts = parse_rows_as_dicts(all_sql, "user_info")
    user_ids = {get_val(d, "id", as_int=True) for d in user_dicts if get_val(d, "id")}
    print(f"[INFO] 解析到 {len(user_ids)} 个用户")

    # --- 解析 submission 表 ---
    submission_dicts = parse_rows_as_dicts(all_sql, "submission")
    submissions = {}
    uses_uuid_func = False

    for d in submission_dicts:
        sub_id = get_val(d, "id", as_int=True)
        if sub_id is None:
            continue

        sub_no_raw = d.get("submission_no", "NULL")
        if "UUID()" in sub_no_raw.upper():
            uses_uuid_func = True
            sub_no = f"UUID-{sub_id}"
        else:
            sub_no = strip_quotes(sub_no_raw)

        submissions[sub_id] = {
            "submission_no": sub_no,
            "user_id": get_val(d, "user_id", as_int=True),
            "problem_id": get_val(d, "problem_id", as_int=True),
            "language": get_val(d, "language"),
            "assignment_id": get_val(d, "assignment_id", as_int=True),
            "status": get_val(d, "status"),
            "verdict": get_val(d, "verdict"),
        }

    print(f"[INFO] 解析到 {len(submissions)} 条提交")

    # --- 解析 submission_detail 表 ---
    detail_dicts = parse_rows_as_dicts(all_sql, "submission_detail")
    detail_sub_ids = {get_val(d, "submission_id", as_int=True) for d in detail_dicts}
    detail_sub_ids.discard(None)
    print(f"[INFO] 解析到 {len(detail_sub_ids)} 条提交详情")

    # --- 解析 contest_submission 表 ---
    cs_dicts = parse_rows_as_dicts(all_sql, "contest_submission")
    contest_submissions = []
    for d in cs_dicts:
        cid = get_val(d, "contest_id", as_int=True)
        sid = get_val(d, "submission_id", as_int=True)
        if cid and sid:
            contest_submissions.append((cid, sid))

    # --- 解析 contest_problem_rel 表 ---
    cpr_dicts = parse_rows_as_dicts(all_sql, "contest_problem_rel")
    contest_problems = defaultdict(set)
    for d in cpr_dicts:
        cid = get_val(d, "contest_id", as_int=True)
        pid = get_val(d, "problem_id", as_int=True)
        if cid and pid:
            contest_problems[cid].add(pid)

    # --- 解析 contest_register_rel 表 ---
    crr_dicts = parse_rows_as_dicts(all_sql, "contest_register_rel")
    contest_users = defaultdict(set)
    for d in crr_dicts:
        cid = get_val(d, "contest_id", as_int=True)
        uid = get_val(d, "user_id", as_int=True)
        if cid and uid:
            contest_users[cid].add(uid)

    # --- 解析 assignment 表 ---
    asn_dicts = parse_rows_as_dicts(all_sql, "assignment")
    assignment_ids = {get_val(d, "id", as_int=True) for d in asn_dicts}
    assignment_ids.discard(None)

    # --- 解析 assignment_problem_rel 表 ---
    apr_dicts = parse_rows_as_dicts(all_sql, "assignment_problem_rel")
    assignment_problems = defaultdict(set)
    for d in apr_dicts:
        asn_id = get_val(d, "assignment_id", as_int=True)
        prob_id = get_val(d, "problem_id", as_int=True)
        if asn_id and prob_id:
            assignment_problems[asn_id].add(prob_id)

    # ============================================================
    # 验证检查
    # ============================================================

    print("\n" + "=" * 60)
    print("开始验证")
    print("=" * 60)

    # CHECK 1: submission_no 确定性（不使用 UUID()）
    print("\n[CHECK 1] submission_no 确定性")
    if uses_uuid_func:
        err("submission 使用了 UUID() 函数，每次运行结果不同，不满足幂等要求")
    else:
        print("  PASS: 未使用 UUID() 函数")

    # CHECK 2: 提交计数一致性
    print("\n[CHECK 2] 提交计数一致性 (problem.total_submit/total_accept vs 实际)")
    actual_submit = defaultdict(int)
    actual_accept = defaultdict(int)
    for sub in submissions.values():
        actual_submit[sub["problem_id"]] += 1
        if sub["verdict"] == "Accepted":
            actual_accept[sub["problem_id"]] += 1

    count_ok = True
    for pid_id, pdata in sorted(problems.items()):
        a_submit = actual_submit.get(pid_id, 0)
        a_accept = actual_accept.get(pid_id, 0)
        if a_submit != pdata["total_submit"]:
            err(f"  {pdata['pid']}: total_submit 声明 {pdata['total_submit']}，实际 {a_submit}")
            count_ok = False
        if a_accept != pdata["total_accept"]:
            err(f"  {pdata['pid']}: total_accept 声明 {pdata['total_accept']}，实际 {a_accept}")
            count_ok = False
    if count_ok:
        print("  PASS: 所有题目计数一致")

    # CHECK 3: submission_detail 完整性
    print("\n[CHECK 3] submission_detail 完整性")
    missing_details = set(submissions.keys()) - detail_sub_ids
    if missing_details:
        err(f"  {len(missing_details)} 条提交缺少 submission_detail: IDs {sorted(missing_details)}")
    else:
        print("  PASS: 所有提交都有 submission_detail")

    # CHECK 4: 源码文件完整性
    print("\n[CHECK 4] 源码文件完整性")
    if not BACKEND_SEED_CODE_DIR.exists():
        err(f"  源码种子目录不存在: {BACKEND_SEED_CODE_DIR}")
    else:
        existing_files = {f.stem for f in BACKEND_SEED_CODE_DIR.glob("*.txt")}
        missing_code = set()
        for sub in submissions.values():
            sno = sub["submission_no"]
            if sno.startswith("UUID-"):
                continue  # UUID() 的无法检查
            if sno not in existing_files:
                missing_code.add(sno)
        if missing_code:
            err(f"  {len(missing_code)} 条提交缺少源码文件")
            for sno in sorted(missing_code)[:5]:
                err(f"    缺失: {sno}.txt")
            if len(missing_code) > 5:
                err(f"    ... 及其他 {len(missing_code) - 5} 个")
        else:
            print("  PASS: 所有提交都有源码文件")

    # CHECK 5: 外键 — user_id
    print("\n[CHECK 5] 外键 — submission.user_id")
    bad_users = {s_id: s["user_id"] for s_id, s in submissions.items() if s["user_id"] not in user_ids}
    if bad_users:
        err(f"  {len(bad_users)} 条提交 user_id 无效: {bad_users}")
    else:
        print("  PASS: 所有 user_id 合法")

    # CHECK 6: 外键 — problem_id
    print("\n[CHECK 6] 外键 — submission.problem_id")
    bad_problems = {s_id: s["problem_id"] for s_id, s in submissions.items() if s["problem_id"] not in problems}
    if bad_problems:
        err(f"  {len(bad_problems)} 条提交 problem_id 无效: {bad_problems}")
    else:
        print("  PASS: 所有 problem_id 合法")

    # CHECK 7: 外键 — assignment_id
    print("\n[CHECK 7] 外键 — submission.assignment_id")
    bad_asn = {}
    for s_id, s in submissions.items():
        if s["assignment_id"] is not None and s["assignment_id"] not in assignment_ids:
            bad_asn[s_id] = s["assignment_id"]
    if bad_asn:
        err(f"  {len(bad_asn)} 条提交 assignment_id 无效: {bad_asn}")
    else:
        print("  PASS: 所有 assignment_id 合法")

    # CHECK 8: contest_submission 关联合法性
    print("\n[CHECK 8] contest_submission 关联合法性")
    cs_ok = True
    for contest_id, sub_id in contest_submissions:
        if sub_id not in submissions:
            err(f"  contest_submission 引用不存在的 submission_id={sub_id}")
            cs_ok = False
            continue
        sub = submissions[sub_id]
        if sub["problem_id"] not in contest_problems.get(contest_id, set()):
            err(f"  contest_submission: 比赛 {contest_id} 不包含题目 {sub['problem_id']}（submission_id={sub_id}）")
            cs_ok = False
        if sub["user_id"] not in contest_users.get(contest_id, set()):
            err(f"  contest_submission: 用户 {sub['user_id']} 未报名比赛 {contest_id}（submission_id={sub_id}）")
            cs_ok = False
    if cs_ok:
        print("  PASS: 所有 contest_submission 关联合法")

    # CHECK 9: assignment 提交关联合法性
    print("\n[CHECK 9] assignment 提交关联合法性")
    asn_ok = True
    for s_id, s in submissions.items():
        if s["assignment_id"] is not None:
            if s["problem_id"] not in assignment_problems.get(s["assignment_id"], set()):
                err(f"  submission {s_id}: 作业 {s['assignment_id']} 不包含题目 {s['problem_id']}")
                asn_ok = False
    if asn_ok:
        print("  PASS: 所有 assignment 提交关联合法")

    # CHECK 10: language 格式
    print("\n[CHECK 10] language 格式")
    bad_langs = {}
    for s_id, s in submissions.items():
        if s["language"] not in VALID_LANGUAGES:
            bad_langs[s_id] = s["language"]
    if bad_langs:
        err(f"  {len(bad_langs)} 条提交 language 格式不正确:")
        for s_id, lang in sorted(bad_langs.items()):
            err(f"    submission {s_id}: '{lang}' (应为 {VALID_LANGUAGES} 之一)")
    else:
        print("  PASS: 所有 language 格式正确")

    # ============================================================
    # 结果汇总
    # ============================================================

    print("\n" + "=" * 60)
    if errors:
        print(f"FAILED: 发现 {len(errors)} 个错误")
        print("=" * 60)
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("ALL CHECKS PASSED")
        print("=" * 60)

    if warnings:
        print(f"\n警告 ({len(warnings)}):")
        for w in warnings:
            print(f"  WARN: {w}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
