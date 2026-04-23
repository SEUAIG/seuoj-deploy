# 提交与判题测试

## 前置条件

- dev 环境运行中
- judgend 判题服务运行中
- 预置题目 P0001（a+b），已有测试数据
- 使用 student1 账号提交

## 测试用例

### S1 — C++ 提交 AC

- **步骤**：
  1. 登录 student1
  2. 进入 P0001 详情页
  3. 选择语言 `cpp`
  4. 输入代码：
     ```cpp
     #include <iostream>
     using namespace std;
     int main() {
         int a, b;
         cin >> a >> b;
         cout << a + b << endl;
         return 0;
     }
     ```
  5. 提交
- **预期**：Accepted，score = 100

### S2 — Java 提交 AC

- **步骤**：
  1. 选择语言 `java`
  2. 输入代码：
     ```java
     import java.util.Scanner;
     public class Main {
         public static void main(String[] args) {
             Scanner sc = new Scanner(System.in);
             int a = sc.nextInt(), b = sc.nextInt();
             System.out.println(a + b);
         }
     }
     ```
  3. 提交
- **预期**：Accepted，score = 100

### S3 — Python 提交 AC

- **步骤**：
  1. 选择语言 `python`
  2. 输入代码：
     ```python
     a, b = map(int, input().split())
     print(a + b)
     ```
  3. 提交
- **预期**：Accepted，score = 100

### S4 — C 提交 AC

- **步骤**：
  1. 选择语言 `c`
  2. 输入代码：
     ```c
     #include <stdio.h>
     int main() {
         int a, b;
         scanf("%d %d", &a, &b);
         printf("%d\n", a + b);
         return 0;
     }
     ```
  3. 提交
- **预期**：Accepted，score = 100

### S5 — Go 提交 AC

- **步骤**：
  1. 选择语言 `go`
  2. 输入代码：
     ```go
     package main
     import "fmt"
     func main() {
         var a, b int
         fmt.Scan(&a, &b)
         fmt.Println(a + b)
     }
     ```
  3. 提交
- **预期**：Accepted，score = 100

### S6 — Node.js 提交 AC

- **步骤**：
  1. 选择语言 `nodejs`
  2. 输入代码：
     ```javascript
     const readline = require('readline');
     const rl = readline.createInterface({ input: process.stdin });
     rl.on('line', (line) => {
         const [a, b] = line.trim().split(' ').map(Number);
         console.log(a + b);
         rl.close();
     });
     ```
  3. 提交
- **预期**：Accepted，score = 100

### S7 — WrongAnswer

- **步骤**：
  1. 选择 C++，输入输出固定值的代码：
     ```cpp
     #include <iostream>
     int main() { std::cout << 0; return 0; }
     ```
  2. 提交
- **预期**：verdict = WrongAnswer，score = 0

### S8 — TimeLimitExceeded

- **步骤**：
  1. 选择 C++，输入死循环代码：
     ```cpp
     int main() { while(true); return 0; }
     ```
  2. 提交
- **预期**：verdict = TimeLimitExceeded

### S9 — RuntimeError

- **步骤**：
  1. 选择 C++，输入会段错误的代码：
     ```cpp
     int main() { int *p = nullptr; *p = 1; return 0; }
     ```
  2. 提交
- **预期**：verdict = RuntimeError

### S10 — CompileError

- **步骤**：
  1. 选择 C++，输入语法错误代码：
     ```cpp
     int main() { this is not valid c++ }
     ```
  2. 提交
- **预期**：
  - verdict = CompileError
  - 提交详情中 error_detail 包含编译错误信息

### S11 — MemoryLimitExceeded

- **步骤**：
  1. 选择 C++，输入大量内存分配代码：
     ```cpp
     #include <cstdlib>
     int main() {
         while(true) malloc(1024 * 1024);
         return 0;
     }
     ```
  2. 提交
- **预期**：verdict = MemoryLimitExceeded 或 RuntimeError（取决于 seccomp 限制）

### S12 — 查看提交详情

- **步骤**：
  1. 提交成功后点击提交记录进入详情页
- **预期**：
  - 显示提交的源代码
  - 显示每个测试点的状态（AC/WA/TLE/RE 等）
  - 显示每个测试点的运行时间和内存占用
  - 显示总得分

### S13 — 评测列表筛选

- **步骤**：
  1. 访问评测页面 `/evaluation`
  2. 筛选特定题目（如 P0001）
  3. 筛选特定状态（如 Accepted）
- **预期**：
  - 列表根据筛选条件更新
  - 显示匹配的提交记录

### S14 — 判题流程状态变化

- **步骤**：
  1. 提交代码后立即观察状态变化
- **预期**：
  - 初始状态为 Pending
  - 进入判题后变为 Running
  - 判题完成后变为 Finished（有 verdict 和 score）
  - 如系统异常则为 Failed
