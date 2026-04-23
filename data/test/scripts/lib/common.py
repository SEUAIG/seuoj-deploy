"""SEUOJ API test helpers."""

import json
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

BASE_URL = "http://localhost:2281/api"
POLL_INTERVAL = 2
POLL_TIMEOUT = 30

PASS_COUNT = 0
FAIL_COUNT = 0
SKIP_COUNT = 0

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
CYAN = "\033[0;36m"
NC = "\033[0m"


# ─── HTTP helpers ───

def _request(method: str, path: str, data=None, token: str | None = None) -> tuple[int, dict | str]:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = Request(url, data=body, headers=headers, method=method)
    try:
        resp = urlopen(req)
        raw = resp.read().decode()
        try:
            return resp.status, json.loads(raw)
        except json.JSONDecodeError:
            return resp.status, raw
    except HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def api_get(path: str, token: str | None = None, params: dict | None = None):
    if params:
        qs = urlencode({k: v for k, v in params.items() if v is not None})
        if qs:
            path = f"{path}?{qs}"
    return _request("GET", path, token=token)


def api_post(path: str, data=None, token: str | None = None):
    return _request("POST", path, data=data, token=token)


def api_put(path: str, data=None, token: str | None = None):
    return _request("PUT", path, data=data, token=token)


def api_patch(path: str, data=None, token: str | None = None):
    return _request("PATCH", path, data=data, token=token)


def api_delete(path: str, token: str | None = None, data=None):
    return _request("DELETE", path, data=data, token=token)


# ─── Service readiness ───

def wait_for_service(max_wait: int = 120):
    print(f"{CYAN}等待服务就绪 (最长 {max_wait}s)...{NC}")
    elapsed = 0
    while elapsed < max_wait:
        try:
            code, _ = api_get("/problem/page")
            if code == 200:
                print(f"{GREEN}服务已就绪{NC}")
                return True
        except Exception:
            pass
        time.sleep(2)
        elapsed += 2
    print(f"{RED}服务未就绪，超时退出{NC}")
    return False


# ─── Auth helpers ───

def login(email: str, password: str = "password123") -> str | None:
    code, body = api_post("/auth/login", {"email": email, "password": password})
    if code != 200:
        return None
    return body.get("data", {}).get("jwt")


def register_user(username: str, email: str, password: str) -> tuple[bool, dict]:
    code, body = api_post("/auth/register/send-code", {"email": email})
    if code != 200:
        return False, body
    vid = body.get("data", {}).get("verification_id")
    code2, body2 = api_post("/auth/register", {
        "username": username,
        "email": email,
        "password": password,
        "verification_id": vid,
        "code": "123456",
    })
    return code2 == 200, body2


# ─── Submit and poll ───

def submit_and_poll(pid: str, language: str, code_text: str, token: str,
                    assignment_id: int | None = None,
                    timeout: int = POLL_TIMEOUT) -> tuple[bool, dict]:
    payload = {"pid": pid, "language": language, "code": code_text}
    if assignment_id is not None:
        payload["assignment_id"] = assignment_id
    status, body = api_post("/submission", payload, token)
    if status != 200:
        return False, {"error": "SUBMIT_FAIL", "status": status, "body": body}
    sub_no = extract(body, "data.submissionNo") or extract(body, "data.submission_no")
    if not sub_no:
        return False, {"error": "NO_SUBMISSION_NO", "body": body}
    elapsed = 0
    while elapsed < timeout:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        s, b = api_get(f"/submission/{sub_no}", token)
        if s != 200:
            continue
        st = extract(b, "data.status")
        if st in ("Finished", "Failed"):
            return True, b.get("data", b)
        if st not in ("Pending", "Running", "Judging"):
            return False, {"error": "UNKNOWN_STATUS", "status": st, "body": b}
    return False, {"error": "TIMEOUT"}


def contest_submit_and_poll(contest_id: int, pid: str, language: str, code_text: str,
                            token: str, timeout: int = POLL_TIMEOUT) -> tuple[bool, dict]:
    payload = {"pid": pid, "language": language, "code": code_text}
    status, body = api_post(f"/contest/{contest_id}/submission", payload, token)
    if status != 200:
        return False, {"error": "SUBMIT_FAIL", "status": status, "body": body}
    sub_no = extract(body, "data.submissionNo") or extract(body, "data.submission_no")
    if not sub_no:
        return False, {"error": "NO_SUBMISSION_NO", "body": body}
    elapsed = 0
    while elapsed < timeout:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        s, b = api_get(f"/contest/{contest_id}/submission/{sub_no}", token)
        if s != 200:
            continue
        st = extract(b, "data.status")
        if st in ("Finished", "Failed"):
            return True, b.get("data", b)
        if st not in ("Pending", "Running", "Judging"):
            return False, {"error": "UNKNOWN_STATUS", "status": st, "body": b}
    return False, {"error": "TIMEOUT"}


def extract(obj, path: str):
    for key in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(key)
        else:
            return None
    return obj


# ─── Test reporting ───

def test_start(test_id: str, desc: str):
    print(f"{CYAN}[TEST] {test_id} — {desc}{NC}")


def test_pass(test_id: str, detail: str = ""):
    global PASS_COUNT
    PASS_COUNT += 1
    suffix = f" — {detail}" if detail else ""
    print(f"{GREEN}[PASS] {test_id}{suffix}{NC}")


def test_fail(test_id: str, reason: str):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"{RED}[FAIL] {test_id} — {reason}{NC}")


def test_skip(test_id: str, reason: str):
    global SKIP_COUNT
    SKIP_COUNT += 1
    print(f"{YELLOW}[SKIP] {test_id} — {reason}{NC}")


# ─── Assertions (return True on success) ───

def assert_status(test_id: str, expected: int, actual: int, detail: str = "") -> bool:
    if expected == actual:
        test_pass(test_id, f"HTTP {actual}" + (f" — {detail}" if detail else ""))
        return True
    test_fail(test_id, f"期望 HTTP {expected}，实际 {actual}" + (f" — {detail}" if detail else ""))
    return False


def assert_json(test_id: str, data, jq_expr: str, expected) -> bool:
    actual = extract(data, jq_expr)
    if str(actual) == str(expected):
        test_pass(test_id, f"{jq_expr} = {expected}")
        return True
    test_fail(test_id, f"{jq_expr}: 期望 '{expected}'，实际 '{actual}'")
    return False


def assert_json_not_empty(test_id: str, data, jq_expr: str) -> bool:
    actual = extract(data, jq_expr)
    if actual is not None and actual != "" and actual != []:
        test_pass(test_id, f"{jq_expr} 非空")
        return True
    test_fail(test_id, f"{jq_expr} 为空或 null")
    return False


def assert_json_gt(test_id: str, data, jq_expr: str, min_val: int) -> bool:
    actual = extract(data, jq_expr)
    try:
        if int(actual) > min_val:
            test_pass(test_id, f"{jq_expr} = {actual} > {min_val}")
            return True
    except (TypeError, ValueError):
        pass
    test_fail(test_id, f"{jq_expr}: 期望 > {min_val}，实际 '{actual}'")
    return False


def assert_json_contains(test_id: str, data, jq_expr: str, substring: str) -> bool:
    actual = extract(data, jq_expr)
    if actual is not None and substring in str(actual):
        test_pass(test_id, f"{jq_expr} 包含 '{substring}'")
        return True
    test_fail(test_id, f"{jq_expr}: 不包含 '{substring}'，实际 '{actual}'")
    return False


def assert_true(test_id: str, condition: bool, pass_msg: str = "", fail_msg: str = "") -> bool:
    if condition:
        test_pass(test_id, pass_msg)
        return True
    test_fail(test_id, fail_msg)
    return False


def report_summary() -> bool:
    total = PASS_COUNT + FAIL_COUNT + SKIP_COUNT
    print()
    print("=" * 40)
    print(f"  {GREEN}PASS: {PASS_COUNT}{NC}  {RED}FAIL: {FAIL_COUNT}{NC}  {YELLOW}SKIP: {SKIP_COUNT}{NC}  TOTAL: {total}")
    print("=" * 40)
    return FAIL_COUNT == 0


def reset_counts():
    global PASS_COUNT, FAIL_COUNT, SKIP_COUNT
    PASS_COUNT = FAIL_COUNT = SKIP_COUNT = 0


# ─── Predefined data ───

USERS = {
    "admin":    {"email": "admin@seuoj.local",    "role": "SUPER_ADMIN", "id": 1},
    "manager":  {"email": "manager@seuoj.local",  "role": "ADMIN",       "id": 2},
    "teacher1": {"email": "teacher1@seuoj.local", "role": "TEACHER",     "id": 3},
    "teacher2": {"email": "teacher2@seuoj.local", "role": "TEACHER",     "id": 4},
    "student1": {"email": "student1@seuoj.local", "role": "STUDENT",     "id": 5},
    "student2": {"email": "student2@seuoj.local", "role": "STUDENT",     "id": 6},
    "student3": {"email": "student3@seuoj.local", "role": "STUDENT",     "id": 7},
    "student4": {"email": "student4@seuoj.local", "role": "STUDENT",     "id": 8},
    "student5": {"email": "student5@seuoj.local", "role": "STUDENT",     "id": 9},
    "student6": {"email": "student6@seuoj.local", "role": "STUDENT",     "id": 10},
}

SAMPLE_CODE = {
    "Cpp": '#include <iostream>\nusing namespace std;\nint main() {\n    int a, b;\n    cin >> a >> b;\n    cout << a + b << endl;\n    return 0;\n}',
    "Java17": 'import java.util.Scanner;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int a = sc.nextInt(), b = sc.nextInt();\n        System.out.println(a + b);\n    }\n}',
    "Python3_12": 'a, b = map(int, input().split())\nprint(a + b)',
    "C": '#include <stdio.h>\nint main() {\n    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("%d\\n", a + b);\n    return 0;\n}',
    "Go1_22": 'package main\nimport "fmt"\nfunc main() {\n    var a, b int\n    fmt.Scan(&a, &b)\n    fmt.Println(a + b)\n}',
    "Nodejs22": 'const readline = require("readline");\nconst rl = readline.createInterface({ input: process.stdin });\nrl.on("line", (line) => {\n    const [a, b] = line.trim().split(" ").map(Number);\n    console.log(a + b);\n    rl.close();\n});',
}

WA_CODE = '#include <iostream>\nint main() { std::cout << 0; return 0; }'
TLE_CODE = 'int main() { while(true); return 0; }'
RE_CODE = 'int main() { int *p = nullptr; *p = 1; return 0; }'
CE_CODE = 'int main() { this is not valid c++ }'
MLE_CODE = '#include <cstdlib>\nint main() {\n    while(true) malloc(1024 * 1024);\n    return 0;\n}'
