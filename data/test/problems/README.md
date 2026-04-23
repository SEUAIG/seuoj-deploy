# 题目测试

## 前置条件

- dev 环境运行中
- 预置 12 道公开题目（P0001~P1010）
- 预置标签（贪心、动态规划、图论等）

## 测试用例

### P1 — 浏览题库（游客）

- **步骤**：
  1. 不登录，访问 `/problemsLibrary`
- **预期**：
  - 题目列表显示 12 道公开题目
  - 能看到题目编号、标题、通过率
  - 支持分页

### P2 — 搜索题目

- **步骤**：
  1. 在题库页面搜索框输入「区间」
- **预期**：
  - 搜索结果包含 P1001「区间求和」
  - 不包含无关题目

### P3 — 标签筛选

- **步骤**：
  1. 在题库页面选择标签「动态规划」
- **预期**：
  - 筛选结果包含 P1002「最大子段和」
  - 其他无此标签的题目不显示

### P4 — 查看题面（游客）

- **步骤**：
  1. 不登录，点击 P0001「a+b」进入详情页
- **预期**：
  - 显示题目标题、描述、输入输出格式、样例
  - 代码编辑器可见但提交需要登录

### P5 — 提交代码并 AC

- **角色**：student1
- **步骤**：
  1. 登录 student1
  2. 进入 P0001「a+b」详情页
  3. 选择语言 C++
  4. 输入正确代码（见下方示例代码）
  5. 点击提交
- **预期**：
  - 跳转到提交详情页
  - 状态从 Pending → Running → Finished
  - 判定结果为 Accepted，得分 100

### P6 — 提交错误代码（WA）

- **角色**：student1
- **步骤**：
  1. 进入 P0001 详情页
  2. 选择 C++，输入输出固定值的代码（如 `cout << 0;`）
  3. 提交
- **预期**：
  - 判定结果为 WrongAnswer

### P7 — 提交编译错误代码（CE）

- **角色**：student1
- **步骤**：
  1. 进入 P0001 详情页
  2. 选择 C++，输入语法错误代码（如缺少分号）
  3. 提交
- **预期**：
  - 判定结果为 CompileError
  - 提交详情中显示编译错误信息

### P8 — 创建题目

- **角色**：teacher1
- **步骤**：
  1. 登录 teacher1
  2. 访问 `/problemsLibrary/create`
  3. 填写题目编号 `P9999`，标题「测试题目」
  4. 设置为公开
  5. 提交创建
- **预期**：
  - 创建成功
  - 在题库列表中可以找到 P9999

### P9 — 上传测试数据

- **角色**：teacher1
- **步骤**：
  1. 进入 P9999 的测试数据页面（`/problemsLibrary/:id/testfile`）
  2. 上传测试输入文件 `1.in`（内容：`1 2`）
  3. 上传测试输出文件 `1.out`（内容：`3`）
- **预期**：
  - 文件上传成功
  - 文件列表中显示 `1.in` 和 `1.out`

### P10 — 配置判题参数

- **角色**：teacher1
- **步骤**：
  1. 进入 P9999 的判题配置页面（`/problemsLibrary/:id/judgeConfig`）
  2. 设置时间限制 1000ms，内存限制 256MB
  3. 保存
- **预期**：
  - 配置保存成功
  - 刷新页面后配置值保持

### P11 — 编辑题目

- **角色**：teacher1
- **步骤**：
  1. 进入 P9999 的编辑页面
  2. 修改标题为「测试题目（已修改）」
  3. 保存
- **预期**：
  - 标题更新为「测试题目（已修改）」
  - 题库列表中同步更新

### P12 — 删除题目

- **角色**：teacher1
- **步骤**：
  1. 在 P9999 详情页点击删除
  2. 确认删除
- **预期**：
  - 题目被软删除
  - 题库列表中不再显示 P9999

---

## 附录：A+B 示例代码

### C++

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

### Java

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

### Python

```python
a, b = map(int, input().split())
print(a + b)
```

### C

```c
#include <stdio.h>
int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d\n", a + b);
    return 0;
}
```

### Go

```go
package main
import "fmt"
func main() {
    var a, b int
    fmt.Scan(&a, &b)
    fmt.Println(a + b)
}
```

### Node.js

```javascript
const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });
rl.on('line', (line) => {
    const [a, b] = line.trim().split(' ').map(Number);
    console.log(a + b);
    rl.close();
});
```
