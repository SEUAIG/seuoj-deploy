#!/usr/bin/env python3
"""Generate 10 seed problems for SEUOJ judgend."""
import os, random, sys
from collections import deque, Counter
from heapq import heappush, heappop

random.seed(42)
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "problems")


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not content.endswith('\n'):
        content += '\n'
    with open(path, 'w', newline='\n') as f:
        f.write(content)


def make_info_toml(problem_type, checker_type, n_cases, time_ms=1000, mem_kb=262144,
                   custom_modules=None):
    lines = ['[problem_info]',
             f'problem_type = "{problem_type}"',
             f'checker_type = "{checker_type}"',
             f'time_limit_ms = {time_ms}',
             f'memory_limit_kb = {mem_kb}', '']
    for i in range(1, n_cases + 1):
        lines += [f'[[testcases]]', f'id = {i}', f'in_path = "{i}.in"',
                  f'ans_path = "{i}.ans"', f'weight = 1', '']
    lines += [f'[[subtasks]]', f'id = 1',
              f'cases = [{", ".join(str(i) for i in range(1, n_cases + 1))}]',
              f'pre_subtasks = []', f'score = 100', f'type = "min"']
    if custom_modules:
        lines.append('')
        lines.append('[custom_modules]')
        for k, v in custom_modules.items():
            lines.append(f'{k} = "{v}"')
    return '\n'.join(lines)


def make_problem_md(problem):
    lines = []
    lines.append('---')
    lines.append(f'pid: {problem["pid"]}')
    lines.append('---')
    lines.append('')
    lines.append('## 题目描述')
    lines.append('')
    lines.append(problem.get('description', ''))
    lines.append('')
    lines.append('## 输入格式')
    lines.append('')
    lines.append(problem.get('input', ''))
    lines.append('')
    lines.append('## 输出格式')
    lines.append('')
    lines.append(problem.get('output', ''))
    lines.append('')
    examples = problem.get('example', [])
    if examples:
        lines.append('## 样例')
        lines.append('')
        for i, ex in enumerate(examples, 1):
            lines.append(f'### 样例 {i}')
            lines.append('')
            lines.append('#### 输入')
            lines.append('')
            lines.append('```')
            lines.append(ex.get('in', ''))
            lines.append('```')
            lines.append('')
            lines.append('#### 输出')
            lines.append('')
            lines.append('```')
            lines.append(ex.get('ans', ''))
            lines.append('```')
            desc = ex.get('description', '')
            if desc:
                lines.append('')
                lines.append(desc)
            lines.append('')
    lines.append('## 提示')
    lines.append('')
    hint = problem.get('hint', '')
    if hint:
        lines.append(hint)
    return '\n'.join(lines)


def write_problem(pid, problem, info_toml, std_cpp, test_cases, checker_cpp=None):
    d = os.path.join(BASE, pid)
    write_file(os.path.join(d, "problem.md"), make_problem_md(problem))
    write_file(os.path.join(d, "info.toml"), info_toml)
    write_file(os.path.join(d, "data", "std.cpp"), std_cpp)
    if checker_cpp:
        write_file(os.path.join(d, "data", "checker.cpp"), checker_cpp)
    for i, (inp, ans) in enumerate(test_cases, 1):
        write_file(os.path.join(d, "data", f"{i}.in"), inp)
        write_file(os.path.join(d, "data", f"{i}.ans"), ans)
    print(f"  {pid}: {len(test_cases)} test cases written")


# =====================================================================
# P1001 - 区间求和 (Prefix Sum Range Query)
# =====================================================================
def gen_p1001():
    problem = {
        "pid": "P1001",
        "description": "小明刚学会了数组，老师给了他 $n$ 个整数，然后问了他 $q$ 个问题。每个问题给出两个整数 $l$ 和 $r$，小明需要快速回答数组中第 $l$ 个到第 $r$ 个数的和。\n\n问题的数量可能很多，小明来不及一个一个地暴力计算。你能帮帮他吗？",
        "input": "第一行两个正整数 $n, q$ ($1 \\le n, q \\le 2 \\times 10^5$)。\n\n第二行 $n$ 个整数 $a_1, a_2, \\dots, a_n$ ($|a_i| \\le 10^9$)。\n\n接下来 $q$ 行，每行两个正整数 $l, r$ ($1 \\le l \\le r \\le n$)。",
        "output": "共 $q$ 行，每行一个整数，表示对应查询的答案。",
        "hint": "注意答案可能超过 32 位整数的范围。",
        "example": [
            {"in": "5 3\n1 2 3 4 5\n1 3\n2 5\n3 3", "ans": "6\n14\n3", "description": ""},
            {"in": "3 2\n-1 2 -3\n1 3\n1 2", "ans": "-2\n1", "description": ""}
        ]
    }

    std_cpp = r"""#include <cstdio>
using namespace std;
int main() {
    int n, q;
    scanf("%d%d", &n, &q);
    long long pre[200001];
    pre[0] = 0;
    for (int i = 1; i <= n; i++) {
        long long x; scanf("%lld", &x);
        pre[i] = pre[i - 1] + x;
    }
    while (q--) {
        int l, r;
        scanf("%d%d", &l, &r);
        printf("%lld\n", pre[r] - pre[l - 1]);
    }
}
"""

    def solve(inp):
        lines = inp.strip().split('\n')
        n, q = map(int, lines[0].split())
        a = list(map(int, lines[1].split()))
        pre = [0] * (n + 1)
        for i in range(n):
            pre[i + 1] = pre[i] + a[i]
        results = []
        for i in range(2, 2 + q):
            l, r = map(int, lines[i].split())
            results.append(str(pre[r] - pre[l - 1]))
        return '\n'.join(results)

    def gen_case(n, q, max_val=10**9):
        a = [random.randint(-max_val, max_val) for _ in range(n)]
        queries = []
        for _ in range(q):
            l = random.randint(1, n)
            r = random.randint(l, n)
            queries.append((l, r))
        lines = [f"{n} {q}", ' '.join(map(str, a))]
        for l, r in queries:
            lines.append(f"{l} {r}")
        return '\n'.join(lines)

    cases = []
    # Edge cases
    cases.append("1 1\n1000000000\n1 1")
    cases.append("3 3\n-1000000000 1000000000 -1000000000\n1 3\n1 2\n2 3")
    cases.append("5 5\n1 2 3 4 5\n1 1\n1 5\n3 3\n2 4\n5 5")
    # Small random
    for _ in range(2):
        cases.append(gen_case(random.randint(5, 20), random.randint(5, 20), 100))
    # Medium
    for _ in range(2):
        cases.append(gen_case(1000, 1000, 10**6))
    # Large
    for _ in range(3):
        cases.append(gen_case(200000, 200000, 10**9))

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1001", problem,
                  make_info_toml("Standard", "Standard", len(test_cases)),
                  std_cpp, test_cases)


# =====================================================================
# P1002 - 最大子段和 (Maximum Subarray Sum)
# =====================================================================
def gen_p1002():
    problem = {
        "pid": "P1002",
        "description": "给定一个长度为 $n$ 的整数序列 $a_1, a_2, \\dots, a_n$，请找到一个**连续的非空子段** $a_l, a_{l+1}, \\dots, a_r$，使得这个子段的和尽可能大。\n\n输出这个最大的子段和。",
        "input": "第一行一个正整数 $n$ ($1 \\le n \\le 2 \\times 10^5$)。\n\n第二行 $n$ 个整数 $a_1, a_2, \\dots, a_n$ ($|a_i| \\le 10^9$)。",
        "output": "一行一个整数，表示最大子段和。",
        "hint": "子段不能为空，至少包含一个元素。当所有元素均为负数时，最大子段和就是最大的那个元素。",
        "example": [
            {"in": "6\n-2 1 -3 4 -1 2", "ans": "5", "description": "选取子段 $[4, -1, 2]$，和为 $5$。"},
            {"in": "3\n-1 -2 -3", "ans": "-1", "description": "所有元素为负，选最大的 $-1$。"}
        ]
    }

    std_cpp = r"""#include <cstdio>
#include <algorithm>
using namespace std;
int main() {
    int n; scanf("%d", &n);
    long long cur, best;
    long long x; scanf("%lld", &x);
    cur = best = x;
    for (int i = 1; i < n; i++) {
        scanf("%lld", &x);
        cur = max(x, cur + x);
        best = max(best, cur);
    }
    printf("%lld\n", best);
}
"""

    def solve(inp):
        lines = inp.strip().split('\n')
        a = list(map(int, lines[1].split()))
        cur = best = a[0]
        for x in a[1:]:
            cur = max(x, cur + x)
            best = max(best, cur)
        return str(best)

    def gen_case(n, max_val=10**9, mode='random'):
        if mode == 'all_neg':
            a = [random.randint(-max_val, -1) for _ in range(n)]
        elif mode == 'all_pos':
            a = [random.randint(1, max_val) for _ in range(n)]
        else:
            a = [random.randint(-max_val, max_val) for _ in range(n)]
        return f"{n}\n{' '.join(map(str, a))}"

    cases = []
    cases.append("1\n-5")
    cases.append("1\n1000000000")
    cases.append("5\n-3 -2 -1 -4 -5")
    cases.append("5\n1 2 3 4 5")
    cases.append(gen_case(10, 100))
    cases.append(gen_case(1000, 10**6))
    cases.append(gen_case(1000, 10**6, 'all_neg'))
    cases.append(gen_case(200000, 10**9))
    cases.append(gen_case(200000, 10**9, 'all_neg'))
    cases.append(gen_case(200000, 10**9))

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1002", problem,
                  make_info_toml("Standard", "Standard", len(test_cases)),
                  std_cpp, test_cases)


# =====================================================================
# P1003 - 括号序列的深度 (Bracket Sequence Depth)
# =====================================================================
def gen_p1003():
    problem = {
        "pid": "P1003",
        "description": "给定一个只包含 `(` 和 `)` 的字符串 $S$，请判断它是否是一个**合法的括号序列**。\n\n- 如果是合法的括号序列，输出它的**最大嵌套深度**。\n- 如果不是合法的括号序列，输出 $-1$。\n\n例如，`(()())` 是合法的，最大嵌套深度为 $2$；而 `(()` 不合法。",
        "input": "一行一个字符串 $S$，仅包含 `(` 和 `)` ($1 \\le |S| \\le 2 \\times 10^5$)。",
        "output": "一个整数。如果 $S$ 是合法括号序列，输出最大嵌套深度；否则输出 $-1$。",
        "hint": "",
        "example": [
            {"in": "(()())", "ans": "2", "description": ""},
            {"in": "((()))", "ans": "3", "description": ""},
            {"in": ")(", "ans": "-1", "description": ""},
            {"in": "(", "ans": "-1", "description": ""}
        ]
    }

    std_cpp = r"""#include <cstdio>
#include <algorithm>
using namespace std;
int main() {
    char s[200002];
    scanf("%s", s);
    int depth = 0, maxd = 0;
    for (int i = 0; s[i]; i++) {
        if (s[i] == '(') { depth++; maxd = max(maxd, depth); }
        else { depth--; if (depth < 0) { puts("-1"); return 0; } }
    }
    printf("%d\n", depth == 0 ? maxd : -1);
}
"""

    def solve(inp):
        s = inp.strip()
        depth = maxd = 0
        for c in s:
            if c == '(':
                depth += 1
                maxd = max(maxd, depth)
            else:
                depth -= 1
                if depth < 0:
                    return "-1"
        return str(maxd) if depth == 0 else "-1"

    def gen_valid(n):
        """Generate a valid bracket sequence of length 2*n."""
        seq = []
        open_count = 0
        close_count = 0
        total = 2 * n
        for _ in range(total):
            can_open = open_count < n
            can_close = close_count < open_count
            if can_open and can_close:
                if random.random() < 0.5:
                    seq.append('(')
                    open_count += 1
                else:
                    seq.append(')')
                    close_count += 1
            elif can_open:
                seq.append('(')
                open_count += 1
            else:
                seq.append(')')
                close_count += 1
        return ''.join(seq)

    def gen_invalid(length):
        chars = [random.choice('()') for _ in range(length)]
        s = ''.join(chars)
        # Make sure it's actually invalid
        depth = 0
        valid = True
        for c in s:
            depth += 1 if c == '(' else -1
            if depth < 0:
                valid = False
                break
        if valid and depth != 0:
            valid = False
        if valid:
            # Force invalid by swapping
            s = ')' + s[1:]
        return s

    cases = []
    cases.append("()")
    cases.append(")(")
    cases.append("(")
    cases.append(gen_valid(5))
    cases.append(gen_invalid(10))
    cases.append(gen_valid(50))
    cases.append(gen_invalid(500))
    cases.append(gen_valid(500))
    # Deep nesting
    cases.append('(' * 100000 + ')' * 100000)
    # Large random valid
    cases.append(gen_valid(100000))

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1003", problem,
                  make_info_toml("Standard", "Standard", len(test_cases)),
                  std_cpp, test_cases)


# =====================================================================
# P1004 - 两数之和 (Two Sum Sorted) [SPJ]
# =====================================================================
def gen_p1004():
    problem = {
        "pid": "P1004",
        "description": "给定一个**升序排列**的整数数组 $a_1, a_2, \\dots, a_n$ 和一个目标值 $\\text{target}$，请找到两个不同的下标 $i, j$ ($1 \\le i < j \\le n$)，使得 $a_i + a_j = \\text{target}$。\n\n保证至少存在一组解。如果有多组解，输出任意一组即可。",
        "input": "第一行两个整数 $n$ 和 $\\text{target}$ ($2 \\le n \\le 2 \\times 10^5$, $|\\text{target}| \\le 2 \\times 10^9$)。\n\n第二行 $n$ 个整数 $a_1, a_2, \\dots, a_n$ ($|a_i| \\le 10^9$)，保证 $a_1 \\le a_2 \\le \\dots \\le a_n$。",
        "output": "一行两个整数 $i, j$ ($i < j$)，表示满足条件的一对下标。",
        "hint": "尝试使用双指针从两端向中间逼近。",
        "example": [
            {"in": "5 9\n1 2 4 5 7", "ans": "2 5", "description": "$a_2 + a_5 = 2 + 7 = 9$"},
            {"in": "3 6\n1 3 5", "ans": "1 3", "description": "$a_1 + a_3 = 1 + 5 = 6$"}
        ]
    }

    std_cpp = r"""#include <cstdio>
int main() {
    int n; long long target;
    scanf("%d%lld", &n, &target);
    long long a[200001];
    for (int i = 1; i <= n; i++) scanf("%lld", &a[i]);
    int l = 1, r = n;
    while (l < r) {
        long long s = a[l] + a[r];
        if (s == target) { printf("%d %d\n", l, r); return 0; }
        else if (s < target) l++;
        else r--;
    }
}
"""

    checker_cpp = r"""#include "testlib.h"
#include <vector>
int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    int n = inf.readInt();
    long long target = inf.readLong();
    std::vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) a[i] = inf.readLong();
    int pi = ouf.readInt(), pj = ouf.readInt();
    if (pi < 1 || pi > n || pj < 1 || pj > n)
        quitf(_wa, "Index out of range: %d %d", pi, pj);
    if (pi >= pj)
        quitf(_wa, "Need i < j, got %d %d", pi, pj);
    if (a[pi] + a[pj] != target)
        quitf(_wa, "a[%d]+a[%d]=%lld, expected %lld", pi, pj, a[pi] + a[pj], target);
    quitf(_ok, "");
}
"""

    def solve(inp):
        lines = inp.strip().split('\n')
        parts = lines[0].split()
        n = int(parts[0])
        target = int(parts[1])
        a = [0] + list(map(int, lines[1].split()))
        l, r = 1, n
        while l < r:
            s = a[l] + a[r]
            if s == target:
                return f"{l} {r}"
            elif s < target:
                l += 1
            else:
                r -= 1
        return "1 2"  # should not happen

    def gen_case(n, max_val=10**9):
        a = sorted(random.randint(-max_val, max_val) for _ in range(n))
        # Pick a valid pair
        i, j = sorted(random.sample(range(n), 2))
        target = a[i] + a[j]
        arr_str = ' '.join(map(str, a))
        return f"{n} {target}\n{arr_str}"

    cases = []
    cases.append("2 0\n-5 5")
    cases.append("4 10\n1 3 5 7")
    cases.append("5 0\n-3 -2 -1 1 2")
    cases.append(gen_case(10, 100))
    cases.append(gen_case(100, 10000))
    cases.append(gen_case(1000, 10**6))
    cases.append(gen_case(1000, 10**6))
    cases.append(gen_case(200000, 10**9))
    cases.append(gen_case(200000, 10**9))
    cases.append(gen_case(200000, 10**9))

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1004", problem,
                  make_info_toml("Special", "Special", len(test_cases),
                                 custom_modules={"checker_path": "checker.cpp"}),
                  std_cpp, test_cases, checker_cpp=checker_cpp)


# =====================================================================
# P1005 - 切绳子 (Cut Rope - Binary Search on Answer)
# =====================================================================
def gen_p1005():
    problem = {
        "pid": "P1005",
        "description": "有 $n$ 条绳子，长度分别为 $L_1, L_2, \\dots, L_n$（均为正整数）。现在需要从这些绳子中切出 $k$ 条**等长**的绳子段，每条绳子段的长度必须为正整数。\n\n问切出的绳子段最长能有多长？如果无法切出 $k$ 条绳子段，输出 $0$。\n\n**注意**：每条绳子只能从中切割，不能将不同的绳子拼接在一起。",
        "input": "第一行两个正整数 $n, k$ ($1 \\le n \\le 10^5$, $1 \\le k \\le 10^9$)。\n\n第二行 $n$ 个正整数 $L_1, L_2, \\dots, L_n$ ($1 \\le L_i \\le 10^9$)。",
        "output": "一个整数，表示切出的绳子段的最大长度。如果无法切出 $k$ 条，输出 $0$。",
        "hint": "尝试二分答案：如果每段长度为 $x$，能否切出至少 $k$ 条？",
        "example": [
            {"in": "4 11\n802 743 457 539", "ans": "200", "description": "每段长 $200$，第一条切 $4$ 段，第二条 $3$ 段，第三条 $2$ 段，第四条 $2$ 段，共 $11$ 段。"},
            {"in": "2 5\n1 1", "ans": "0", "description": "两条长度为 $1$ 的绳子最多切 $2$ 条长度为 $1$ 的段，无法得到 $5$ 条。"}
        ]
    }

    std_cpp = r"""#include <cstdio>
#include <algorithm>
using namespace std;
int main() {
    int n; long long k;
    scanf("%d%lld", &n, &k);
    long long a[100001], hi = 0;
    for (int i = 0; i < n; i++) {
        scanf("%lld", &a[i]);
        hi = max(hi, a[i]);
    }
    long long lo = 0;
    while (lo < hi) {
        long long mid = lo + (hi - lo + 1) / 2;
        long long cnt = 0;
        for (int i = 0; i < n; i++) cnt += a[i] / mid;
        if (cnt >= k) lo = mid;
        else hi = mid - 1;
    }
    printf("%lld\n", lo);
}
"""

    def solve(inp):
        lines = inp.strip().split('\n')
        parts = lines[0].split()
        n = int(parts[0])
        k = int(parts[1])
        a = list(map(int, lines[1].split()))
        lo, hi = 0, max(a)
        while lo < hi:
            mid = lo + (hi - lo + 1) // 2
            cnt = sum(x // mid for x in a)
            if cnt >= k:
                lo = mid
            else:
                hi = mid - 1
        return str(lo)

    def gen_case(n, k, max_len=10**9):
        a = [random.randint(1, max_len) for _ in range(n)]
        return f"{n} {k}\n{' '.join(map(str, a))}"

    cases = []
    cases.append("1 1\n1")
    cases.append("1 2\n1")
    cases.append("4 11\n802 743 457 539")
    cases.append(gen_case(10, 5, 1000))
    cases.append(gen_case(100, 1000, 10**6))
    cases.append(gen_case(1000, 100000, 10**9))
    cases.append(gen_case(100000, 10**9, 10**9))
    cases.append(gen_case(100000, 1, 10**9))
    # All same length
    cases.append(f"5 10\n{'100 ' * 5}".strip())
    cases.append(gen_case(100000, 10**9, 10**9))

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1005", problem,
                  make_info_toml("Standard", "Standard", len(test_cases)),
                  std_cpp, test_cases)


# =====================================================================
# P1006 - 合并果子 (Merge Fruits - Priority Queue)
# =====================================================================
def gen_p1006():
    problem = {
        "pid": "P1006",
        "description": "在一片果园里有 $n$ 堆果子，第 $i$ 堆有 $a_i$ 个果子。\n\n每次可以选择**两堆**果子合并成一堆，合并的体力消耗等于这两堆果子的数量之和。\n\n经过 $n-1$ 次合并后，所有果子会合为一堆。请问：最少需要消耗多少体力？",
        "input": "第一行一个正整数 $n$ ($2 \\le n \\le 10^5$)。\n\n第二行 $n$ 个正整数 $a_1, a_2, \\dots, a_n$ ($1 \\le a_i \\le 10^5$)。",
        "output": "一个整数，表示最小体力消耗。",
        "hint": "每次选择最小的两堆合并，贪心策略的正确性可以类比 Huffman 编码。",
        "example": [
            {"in": "3\n1 2 9", "ans": "15", "description": "先合并 $1$ 和 $2$，消耗 $3$；再合并 $3$ 和 $9$，消耗 $12$。总计 $15$。"},
            {"in": "4\n1 1 1 1", "ans": "8", "description": ""}
        ]
    }

    std_cpp = r"""#include <cstdio>
#include <queue>
using namespace std;
int main() {
    int n; scanf("%d", &n);
    priority_queue<long long, vector<long long>, greater<>> pq;
    for (int i = 0; i < n; i++) {
        long long x; scanf("%lld", &x);
        pq.push(x);
    }
    long long ans = 0;
    while (pq.size() > 1) {
        long long a = pq.top(); pq.pop();
        long long b = pq.top(); pq.pop();
        ans += a + b;
        pq.push(a + b);
    }
    printf("%lld\n", ans);
}
"""

    def solve(inp):
        lines = inp.strip().split('\n')
        n = int(lines[0])
        a = list(map(int, lines[1].split()))
        heap = a[:]
        import heapq
        heapq.heapify(heap)
        ans = 0
        while len(heap) > 1:
            x = heapq.heappop(heap)
            y = heapq.heappop(heap)
            ans += x + y
            heapq.heappush(heap, x + y)
        return str(ans)

    def gen_case(n, max_val=100000):
        a = [random.randint(1, max_val) for _ in range(n)]
        return f"{n}\n{' '.join(map(str, a))}"

    cases = []
    cases.append("2\n1 1")
    cases.append("3\n1 2 9")
    cases.append("5\n1 1 1 1 1")
    cases.append(gen_case(10, 100))
    cases.append(gen_case(100, 1000))
    cases.append(gen_case(1000, 10000))
    cases.append(gen_case(10000, 100000))
    cases.append(gen_case(100000, 100000))
    cases.append(gen_case(100000, 1))  # all 1s
    cases.append(gen_case(100000, 100000))

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1006", problem,
                  make_info_toml("Standard", "Standard", len(test_cases)),
                  std_cpp, test_cases)


# =====================================================================
# P1007 - 逆序对 (Count Inversions - Merge Sort)
# =====================================================================
def gen_p1007():
    problem = {
        "pid": "P1007",
        "description": "给定一个长度为 $n$ 的整数序列 $a_1, a_2, \\dots, a_n$。\n\n如果存在 $i < j$ 且 $a_i > a_j$，则称 $(i, j)$ 为一个**逆序对**。\n\n请计算序列中逆序对的总数。",
        "input": "第一行一个正整数 $n$ ($1 \\le n \\le 2 \\times 10^5$)。\n\n第二行 $n$ 个整数 $a_1, a_2, \\dots, a_n$ ($1 \\le a_i \\le 10^9$)。",
        "output": "一个整数，表示逆序对的数量。",
        "hint": "暴力枚举是 $O(n^2)$ 的，试试归并排序的思想。",
        "example": [
            {"in": "5\n2 3 8 6 1", "ans": "5", "description": "逆序对为 $(1,5),(2,5),(3,4),(3,5),(4,5)$。"},
            {"in": "3\n1 2 3", "ans": "0", "description": "已经有序，没有逆序对。"}
        ]
    }

    std_cpp = r"""#include <cstdio>
#include <vector>
using namespace std;
long long cnt;
void merge_sort(vector<int>& a, int l, int r) {
    if (r - l <= 1) return;
    int m = (l + r) / 2;
    merge_sort(a, l, m);
    merge_sort(a, m, r);
    vector<int> tmp;
    int i = l, j = m;
    while (i < m && j < r) {
        if (a[i] <= a[j]) tmp.push_back(a[i++]);
        else { tmp.push_back(a[j++]); cnt += m - i; }
    }
    while (i < m) tmp.push_back(a[i++]);
    while (j < r) tmp.push_back(a[j++]);
    for (int k = l; k < r; k++) a[k] = tmp[k - l];
}
int main() {
    int n; scanf("%d", &n);
    vector<int> a(n);
    for (int i = 0; i < n; i++) scanf("%d", &a[i]);
    cnt = 0;
    merge_sort(a, 0, n);
    printf("%lld\n", cnt);
}
"""

    def solve(inp):
        lines = inp.strip().split('\n')
        a = list(map(int, lines[1].split()))
        # Merge sort inversion count
        def merge_count(arr):
            if len(arr) <= 1:
                return arr, 0
            mid = len(arr) // 2
            left, lc = merge_count(arr[:mid])
            right, rc = merge_count(arr[mid:])
            merged = []
            count = lc + rc
            i = j = 0
            while i < len(left) and j < len(right):
                if left[i] <= right[j]:
                    merged.append(left[i])
                    i += 1
                else:
                    merged.append(right[j])
                    count += len(left) - i
                    j += 1
            merged.extend(left[i:])
            merged.extend(right[j:])
            return merged, count

        sys.setrecursionlimit(500000)
        _, count = merge_count(a)
        return str(count)

    def gen_case(n, max_val=10**9, mode='random'):
        if mode == 'sorted':
            a = sorted(random.randint(1, max_val) for _ in range(n))
        elif mode == 'reversed':
            a = sorted((random.randint(1, max_val) for _ in range(n)), reverse=True)
        else:
            a = [random.randint(1, max_val) for _ in range(n)]
        return f"{n}\n{' '.join(map(str, a))}"

    cases = []
    cases.append("1\n1")
    cases.append("2\n2 1")
    cases.append("5\n5 4 3 2 1")
    cases.append("5\n1 2 3 4 5")
    cases.append(gen_case(20, 100))
    cases.append(gen_case(1000, 10**6))
    cases.append(gen_case(1000, 10**6, 'reversed'))
    cases.append(gen_case(200000, 10**9))
    cases.append(gen_case(200000, 10**9, 'reversed'))
    cases.append(gen_case(200000, 10**9))

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1007", problem,
                  make_info_toml("Standard", "Standard", len(test_cases)),
                  std_cpp, test_cases)


# =====================================================================
# P1008 - 重排回文 (Rearrange to Palindrome) [SPJ]
# =====================================================================
def gen_p1008():
    problem = {
        "pid": "P1008",
        "description": "给定一个由小写字母组成的字符串 $S$，请重新排列其中的字符，使其成为一个**回文串**。\n\n- 如果可以，输出任意一个合法的回文串。\n- 如果不可以，输出 `impossible`。\n\n回文串是指正着读和反着读都一样的字符串，例如 `abcba` 和 `abba`。",
        "input": "一行一个字符串 $S$，仅包含小写字母 ($1 \\le |S| \\le 10^5$)。",
        "output": "一行，一个回文串或 `impossible`。",
        "hint": "想想什么条件下才能构成回文串？与字符出现次数的奇偶性有关。",
        "example": [
            {"in": "aabb", "ans": "abba", "description": "其他合法答案如 `baab` 也可以。"},
            {"in": "abc", "ans": "impossible", "description": "三个不同字符，无法构成回文。"},
            {"in": "aaabb", "ans": "ababa", "description": ""}
        ]
    }

    std_cpp = r"""#include <cstdio>
#include <cstring>
#include <algorithm>
using namespace std;
int main() {
    char s[100002];
    scanf("%s", s);
    int n = strlen(s);
    int cnt[26] = {};
    for (int i = 0; i < n; i++) cnt[s[i] - 'a']++;
    int odd = 0;
    char mid_ch = 0;
    for (int i = 0; i < 26; i++) {
        if (cnt[i] % 2) { odd++; mid_ch = 'a' + i; }
    }
    if (odd > 1) { puts("impossible"); return 0; }
    char left[50001];
    int pos = 0;
    for (int i = 0; i < 26; i++)
        for (int j = 0; j < cnt[i] / 2; j++)
            left[pos++] = 'a' + i;
    for (int i = 0; i < pos; i++) putchar(left[i]);
    if (odd) putchar(mid_ch);
    for (int i = pos - 1; i >= 0; i--) putchar(left[i]);
    putchar('\n');
}
"""

    checker_cpp = r"""#include "testlib.h"
#include <string>
#include <algorithm>
int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    std::string input = inf.readWord();
    std::string output = ouf.readWord();
    std::string expected = ans.readWord();
    if (expected == "impossible") {
        if (output != "impossible")
            quitf(_wa, "Expected impossible, got '%s'", output.substr(0, 50).c_str());
        quitf(_ok, "");
    }
    std::string rev = output;
    std::reverse(rev.begin(), rev.end());
    if (output != rev)
        quitf(_wa, "Not a palindrome");
    std::string si = input, so = output;
    std::sort(si.begin(), si.end());
    std::sort(so.begin(), so.end());
    if (si != so)
        quitf(_wa, "Character frequencies don't match");
    quitf(_ok, "");
}
"""

    def solve(inp):
        s = inp.strip()
        cnt = Counter(s)
        odd = sum(1 for v in cnt.values() if v % 2)
        if odd > 1:
            return "impossible"
        left = []
        mid = ''
        for c in sorted(cnt.keys()):
            left.append(c * (cnt[c] // 2))
            if cnt[c] % 2:
                mid = c
        left_str = ''.join(left)
        return left_str + mid + left_str[::-1]

    def gen_possible(length):
        """Generate a string that can form a palindrome."""
        chars = []
        remaining = length
        for i in range(25):
            c = chr(ord('a') + i)
            if remaining <= 0:
                break
            count = random.randint(0, remaining) // 2 * 2
            chars.extend([c] * count)
            remaining -= count
        if remaining > 0:
            c = chr(ord('a') + random.randint(0, 25))
            chars.extend([c] * remaining)
        random.shuffle(chars)
        return ''.join(chars[:length])

    def gen_impossible(length):
        """Generate a string that cannot form a palindrome."""
        # Use at least 3 chars with odd count
        chars = list('abcde'[:min(5, length)])
        while len(chars) < length:
            chars.append(random.choice('abcde'))
        random.shuffle(chars)
        s = ''.join(chars[:length])
        # Verify it's actually impossible
        cnt = Counter(s)
        odd = sum(1 for v in cnt.values() if v % 2)
        if odd <= 1:
            # Force impossible
            s = 'abc' + s[3:]
            cnt2 = Counter(s)
            odd2 = sum(1 for v in cnt2.values() if v % 2)
            if odd2 <= 1 and length >= 4:
                s = 'abcd' + s[4:]
        return s

    cases = []
    cases.append("a")
    cases.append("ab")
    cases.append("aabb")
    cases.append("aaabb")
    cases.append("abcde")
    cases.append(gen_possible(100))
    cases.append(gen_impossible(100))
    cases.append(gen_possible(100000))
    cases.append(gen_impossible(99999))
    # All same character
    cases.append("a" * 100000)

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1008", problem,
                  make_info_toml("Special", "Special", len(test_cases),
                                 custom_modules={"checker_path": "checker.cpp"}),
                  std_cpp, test_cases, checker_cpp=checker_cpp)


# =====================================================================
# P1009 - 迷宫寻路 (Maze Shortest Path - BFS)
# =====================================================================
def gen_p1009():
    problem = {
        "pid": "P1009",
        "description": "给定一个 $n \\times m$ 的网格迷宫，其中 `.` 表示空地（可通行），`#` 表示障碍（不可通行）。\n\n从左上角 $(1,1)$ 出发，每步可以向**上、下、左、右**移动一格（不能走出网格边界，也不能走到障碍上），目标是到达右下角 $(n,m)$。\n\n请求出从起点到终点的最少步数。如果无法到达，输出 $-1$。",
        "input": "第一行两个正整数 $n, m$ ($1 \\le n, m \\le 1000$)。\n\n接下来 $n$ 行，每行一个长度为 $m$ 的字符串，仅包含 `.` 和 `#`。",
        "output": "一个整数，表示最少步数。如果无法到达，输出 $-1$。",
        "hint": "",
        "example": [
            {"in": "3 3\n...\n.#.\n...", "ans": "4", "description": ""},
            {"in": "3 3\n..#\n.#.\n#..", "ans": "-1", "description": "右下角被障碍包围，无法到达。"},
            {"in": "1 1\n.", "ans": "0", "description": "起点即终点。"}
        ]
    }

    std_cpp = r"""#include <cstdio>
#include <queue>
using namespace std;
char grid[1001][1002];
int dist[1001][1001];
int dx[] = {0, 0, 1, -1}, dy[] = {1, -1, 0, 0};
int main() {
    int n, m;
    scanf("%d%d", &n, &m);
    for (int i = 0; i < n; i++) scanf("%s", grid[i]);
    if (grid[0][0] == '#' || grid[n-1][m-1] == '#') { puts("-1"); return 0; }
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) dist[i][j] = -1;
    queue<pair<int,int>> q;
    q.push({0, 0}); dist[0][0] = 0;
    while (!q.empty()) {
        auto [x, y] = q.front(); q.pop();
        for (int d = 0; d < 4; d++) {
            int nx = x + dx[d], ny = y + dy[d];
            if (nx >= 0 && nx < n && ny >= 0 && ny < m &&
                grid[nx][ny] == '.' && dist[nx][ny] == -1) {
                dist[nx][ny] = dist[x][y] + 1;
                q.push({nx, ny});
            }
        }
    }
    printf("%d\n", dist[n-1][m-1]);
}
"""

    def solve(inp):
        lines = inp.strip().split('\n')
        n, m = map(int, lines[0].split())
        grid = [lines[i + 1] for i in range(n)]
        if grid[0][0] == '#' or grid[n-1][m-1] == '#':
            return "-1"
        dist = [[-1] * m for _ in range(n)]
        dist[0][0] = 0
        q = deque([(0, 0)])
        while q:
            x, y = q.popleft()
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == '.' and dist[nx][ny] == -1:
                    dist[nx][ny] = dist[x][y] + 1
                    q.append((nx, ny))
        return str(dist[n-1][m-1])

    def gen_maze(n, m, wall_prob=0.3, ensure_path=True):
        grid = [['.' for _ in range(m)] for _ in range(n)]
        for i in range(n):
            for j in range(m):
                if (i, j) != (0, 0) and (i, j) != (n-1, m-1):
                    if random.random() < wall_prob:
                        grid[i][j] = '#'
        if ensure_path:
            # Carve a random path from (0,0) to (n-1,m-1)
            x, y = 0, 0
            while x < n - 1 or y < m - 1:
                grid[x][y] = '.'
                if x == n - 1:
                    y += 1
                elif y == m - 1:
                    x += 1
                elif random.random() < 0.5:
                    x += 1
                else:
                    y += 1
            grid[n-1][m-1] = '.'
        rows = [''.join(row) for row in grid]
        return f"{n} {m}\n" + '\n'.join(rows)

    def gen_no_path(n, m):
        grid = [['.' for _ in range(m)] for _ in range(n)]
        # Block all neighbors of (n-1, m-1)
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = n-1+dx, m-1+dy
            if 0 <= nx < n and 0 <= ny < m and (nx, ny) != (0, 0):
                grid[nx][ny] = '#'
        if n > 1 or m > 1:
            rows = [''.join(row) for row in grid]
            return f"{n} {m}\n" + '\n'.join(rows)
        else:
            return f"1 1\n."

    cases = []
    cases.append("1 1\n.")
    cases.append("2 2\n.#\n..")
    cases.append(gen_no_path(5, 5))
    cases.append(gen_maze(10, 10, 0.2))
    cases.append(gen_maze(10, 10, 0.4))
    cases.append(gen_maze(50, 50, 0.3))
    cases.append(gen_maze(100, 100, 0.25))
    cases.append(gen_maze(500, 500, 0.3))
    cases.append(gen_no_path(1000, 1000))
    cases.append(gen_maze(1000, 1000, 0.3))

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1009", problem,
                  make_info_toml("Standard", "Standard", len(test_cases)),
                  std_cpp, test_cases)


# =====================================================================
# P1010 - 岛屿计数 (Count Islands - DFS/BFS)
# =====================================================================
def gen_p1010():
    problem = {
        "pid": "P1010",
        "description": "给定一个 $n \\times m$ 的网格地图，其中 `1` 表示陆地，`0` 表示水域。\n\n相邻（上下左右方向）的陆地格子构成同一个**岛屿**。请计算地图中岛屿的数量。",
        "input": "第一行两个正整数 $n, m$ ($1 \\le n, m \\le 1000$)。\n\n接下来 $n$ 行，每行一个长度为 $m$ 的字符串，仅包含 `0` 和 `1`。",
        "output": "一个整数，表示岛屿数量。",
        "hint": "对每个未访问的陆地格子执行搜索（DFS 或 BFS），标记整个连通块。",
        "example": [
            {"in": "4 5\n11110\n11010\n11000\n00000", "ans": "1", "description": ""},
            {"in": "4 5\n11000\n11000\n00100\n00011", "ans": "3", "description": ""},
            {"in": "1 1\n0", "ans": "0", "description": ""}
        ]
    }

    std_cpp = r"""#include <cstdio>
#include <queue>
using namespace std;
int n, m;
char grid[1001][1002];
int dx[] = {0, 0, 1, -1}, dy[] = {1, -1, 0, 0};
void bfs(int sx, int sy) {
    queue<pair<int,int>> q;
    q.push({sx, sy}); grid[sx][sy] = '0';
    while (!q.empty()) {
        auto [x, y] = q.front(); q.pop();
        for (int d = 0; d < 4; d++) {
            int nx = x + dx[d], ny = y + dy[d];
            if (nx >= 0 && nx < n && ny >= 0 && ny < m && grid[nx][ny] == '1') {
                grid[nx][ny] = '0';
                q.push({nx, ny});
            }
        }
    }
}
int main() {
    scanf("%d%d", &n, &m);
    for (int i = 0; i < n; i++) scanf("%s", grid[i]);
    int ans = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (grid[i][j] == '1') { bfs(i, j); ans++; }
    printf("%d\n", ans);
}
"""

    def solve(inp):
        lines = inp.strip().split('\n')
        n, m = map(int, lines[0].split())
        grid = [list(lines[i + 1]) for i in range(n)]
        count = 0
        for i in range(n):
            for j in range(m):
                if grid[i][j] == '1':
                    count += 1
                    q = deque([(i, j)])
                    grid[i][j] = '0'
                    while q:
                        x, y = q.popleft()
                        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == '1':
                                grid[nx][ny] = '0'
                                q.append((nx, ny))
        return str(count)

    def gen_grid(n, m, land_prob=0.4):
        rows = []
        for _ in range(n):
            row = ''.join('1' if random.random() < land_prob else '0' for _ in range(m))
            rows.append(row)
        return f"{n} {m}\n" + '\n'.join(rows)

    cases = []
    cases.append("1 1\n0")
    cases.append("1 1\n1")
    cases.append("3 3\n111\n111\n111")  # all land = 1 island
    cases.append("3 3\n101\n010\n101")  # checkerboard
    cases.append(gen_grid(10, 10, 0.5))
    cases.append(gen_grid(50, 50, 0.3))
    cases.append(gen_grid(100, 100, 0.4))
    cases.append(gen_grid(500, 500, 0.3))
    cases.append(gen_grid(1000, 1000, 0.0))  # all water
    cases.append(gen_grid(1000, 1000, 0.4))

    test_cases = [(c, solve(c)) for c in cases]
    write_problem("P1010", problem,
                  make_info_toml("Standard", "Standard", len(test_cases)),
                  std_cpp, test_cases)


# =====================================================================
# Main
# =====================================================================
if __name__ == '__main__':
    sys.setrecursionlimit(500000)
    print("Generating 10 problems...")
    gen_p1001()
    gen_p1002()
    gen_p1003()
    gen_p1004()
    gen_p1005()
    gen_p1006()
    gen_p1007()
    gen_p1008()
    gen_p1009()
    gen_p1010()
    print("Done!")
