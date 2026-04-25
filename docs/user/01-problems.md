# SEUOJ 题目创建与上传指南

本文档说明如何为 SEUOJ 创建符合评测系统要求的题目数据，以及如何通过 Web 界面或脚本上传题目。

---

## 通过 Web 界面创建题目

> 需要 ADMIN 或 SUPER_ADMIN 角色

### 步骤 1：创建题目

<!-- [图片占位：创建题目页面截图] -->

1. 在侧边栏进入 **题目管理**
2. 点击 **创建题目**
3. 填写题目 ID 和基本信息（标题、是否公开等）
4. 点击确认创建

### 步骤 2：编辑题面

<!-- [图片占位：编辑题面页面截图] -->

1. 在题目列表中点击对应题目的 **编辑** 按钮，或访问 `/problemsLibrary/{pid}/edit`
2. 在编辑器中填写：
   - 题目描述（支持 Markdown + LaTeX）
   - 输入格式
   - 输出格式
   - 样例（输入/输出对）
   - 提示/说明
3. 保存

### 步骤 3：上传测试数据

<!-- [图片占位：上传测试数据页面截图] -->
<!-- [TODO: 写一下推荐的文件结构]-->

1. 进入题目的 **测试文件** 页面（`/problemsLibrary/{pid}/testfile`）
2. 准备一个 ZIP 压缩包，包含所有 `.in` 和 `.ans` 文件，推荐以下的组织方式
测试数据通过 **ZIP 压缩包** 上传。ZIP 内应直接包含数据文件（不要有额外的子目录层级）：

```
data.zip
├── 1.in
├── 1.ans
├── 2.in
├── 2.ans
├── ...
└── checker.cpp    # （仅 SPJ 题需要）
```

上传时会自动解压到题目的 `data/` 目录，**覆盖**之前的所有数据。
3. 上传 ZIP 文件，**这会覆盖之前已有的文件**
4. 上传成功后可以在文件树中查看所有已上传的文件


### 步骤 4：配置评测参数

<!-- [图片占位：评测配置页面截图] -->

系统会尽力自动识别上传的压缩包中的数据格式，通常无需手动指定每个测试点的输入输出文件路径。

1. 进入题目的 **评测配置** 页面（`/problemsLibrary/{pid}/judgeConfig`）
2. 配置：
   - 题目类型（Standard / Special / Interactive）
   - 时间限制、内存限制
   - 测试点列表（指定每个测试点的输入/输出文件路径和权重）
   - Subtask 配置（可选）
   - SPJ/交互器路径（如需要）
3. 保存配置

### 步骤 5：验证

提交一份正确的代码进行测试，确认所有测试点能正常评测。

---

下面的部分用于内部参考，会介绍题目在系统中实际被存储的方式

## 题目数据结构概览

每道题目在评测端（judgend）以一个目录存储，结构如下：

```
P1001/
├── problem.md          # 题面描述（Markdown + YAML frontmatter）
├── info.toml           # 评测配置（测试点、时间/内存限制、Judge 类型等）
└── data/               # 测试数据文件
    ├── 1.in            # 第 1 个测试点输入
    ├── 1.ans           # 第 1 个测试点期望输出
    ├── 2.in
    ├── 2.ans
    ├── ...
    ├── checker.cpp     # （可选）Special Judge 源码
    └── interactor.cpp  # （可选）交互题交互器源码
```

**关键规则：**
- 题目 ID（pid）为目录名，如 `P1001`
- 测试数据文件放在 `data/` 子目录中
- 文件名只允许 `[a-zA-Z0-9_-]` 和 `.`，不允许中文、空格等特殊字符
- `problem.md` 和 `info.toml` 放在题目根目录

---

## problem.md 题面文件

`problem.md` 使用 YAML frontmatter + Markdown 格式。评测系统通过 `##` 二级标题识别各部分。

### 格式模板

````markdown
---
pid: P1001
---

## 题目描述

在这里写题目描述，支持 Markdown 和 LaTeX 数学公式（$...$）。

## 输入格式

描述输入的格式要求。

## 输出格式

描述输出的格式要求。

## 样例

### 样例 1

#### 输入

```
1 2
```

#### 输出

```
3
```

### 样例 2

#### 输入

```
10 20
```

#### 输出

```
30
```

样例解释文字（可选，放在输出代码块之后）。

## 提示

补充说明、数据范围、算法提示等。
````

### 格式要点

| 项目 | 说明 |
|------|------|
| frontmatter | 必须以 `---` 开头和结尾，包含 `pid` 字段 |
| 二级标题 | 支持中文（`题目描述`/`输入格式`/`输出格式`/`样例`/`提示`）或英文（`Description`/`Input`/`Output`/`Examples`/`Hint`） |
| 样例 | 在 `## 样例` 下用 `### 样例 N` 分组，每组包含 `#### 输入` 和 `#### 输出`，代码块用 `` ``` `` 包裹 |
| 样例说明 | 放在 `#### 输出` 代码块之后，作为该样例的补充解释 |
| 数学公式 | 支持 LaTeX：行内 `$...$`，独立 `$$...$$` |
| 图片 | 可以在题面中引用图片（需另行上传到题目文件中） |

---

## info.toml 评测配置文件

`info.toml` 定义了题目的评测参数，使用 TOML 格式。

### 最小配置（标准题）

```toml
[problem_info]
problem_type = "Standard"       # 题目类型：Standard / Special / Interactive
checker_type = "Standard"       # 判定类型：Standard / Special / Interactor
time_limit_ms = 1000            # 时间限制（毫秒），默认 1000
memory_limit_kb = 262144        # 内存限制（KB），默认 256MB

[[testcases]]
id = 1
in_path = "1.in"                # 输入文件路径（相对于 data/ 目录）
ans_path = "1.ans"              # 期望输出文件路径（相对于 data/ 目录）
weight = 1                    # 权重（所有测试点按权重比例计分）

[[testcases]]
id = 2
in_path = "2.in"
ans_path = "2.ans"
weight = 1
```

### 带 Subtask 的配置

Subtask 用于分组评测，每个 subtask 包含若干测试点，subtask 之间可以有依赖关系。

```toml
[problem_info]
problem_type = "Standard"
checker_type = "Standard"
time_limit_ms = 2000
memory_limit_kb = 524288

[[testcases]]
id = 1
in_path = "1.in"
ans_path = "1.ans"
weight = 1

[[testcases]]
id = 2
in_path = "2.in"
ans_path = "2.ans"
weight = 1

[[testcases]]
id = 3
in_path = "3.in"
ans_path = "3.ans"
weight = 1

[[testcases]]
id = 4
in_path = "4.in"
ans_path = "4.ans"
weight = 1

# Subtask 1: 小数据（30分）
[[subtasks]]
id = 1
cases = [1, 2]           # 包含的测试点 ID 列表
pre_subtasks = []         # 前置依赖的 subtask ID 列表
score = 30                # 本 subtask 分数
type = "min"              # 评分方式："min"（最低分）或 "sum"（平均分）

# Subtask 2: 大数据（70分），依赖 Subtask 1
[[subtasks]]
id = 2
cases = [3, 4]
pre_subtasks = [1]        # 需要 Subtask 1 全部通过才评测
score = 70
type = "min"
```

**Subtask 规则：**
- 所有 subtask 的 `score` 之和必须为 **100**
- subtask 之间的依赖关系不能有循环
- `type = "min"`：subtask 得分 = 最低测试点得分比例 x subtask 分数
- `type = "sum"`：subtask 得分 = 平均测试点得分比例 x subtask 分数

### 单测试点限制覆盖

每个测试点可以覆盖全局的时间/内存限制：

```toml
[[testcases]]
id = 5
in_path = "5.in"
ans_path = "5.ans"
weight = 1
time_limit_ms = 3000     # 覆盖全局时限
memory_limit_kb = 524288  # 覆盖全局内存限制
```

---

## data/ 测试数据目录

### 文件命名

- 文件名只允许字母、数字、下划线、短横线和 `.`
- 推荐命名：`1.in` / `1.ans`、`2.in` / `2.ans`、...
- 也支持其他合法命名如 `sample1.in` / `big_data.ans`，只要与 `info.toml` 中的路径对应即可

### 数据格式

- 输入文件（`.in`）和输出文件（`.ans`）均为纯文本
- 确保行末没有多余空格（除非题目要求）
- 确保文件末尾有换行符

---

## 三种题目类型

### 1. 标准题（Standard）

最常见的题型。程序从标准输入读取数据，输出到标准输出，系统逐行比较输出与期望答案。

```toml
[problem_info]
problem_type = "Standard"
checker_type = "Standard"
```

### 2. Special Judge 题（Special）

答案不唯一时使用。需要提供一个自定义 checker 程序来判断输出的正确性。

```toml
[problem_info]
problem_type = "Special"
checker_type = "Special"

[custom_modules]
checker_path = "checker.cpp"   # checker 源码放在 data/ 目录中
```

Checker 程序接收三个参数：
1. 输入文件路径
2. 用户输出文件路径
3. 期望答案文件路径

退出码 0 表示 AC，非 0 表示 WA。推荐使用 testlib.h 编写 checker。

### 3. 交互题（Interactive）

程序与交互器（interactor）通过标准输入输出进行通信。

```toml
[problem_info]
problem_type = "Interactive"
checker_type = "Interactor"

[custom_modules]
interactor_path = "interactor.cpp"   # 交互器源码放在 data/ 目录中
```

交互器读取输入文件，通过管道与用户程序通信，判断交互过程是否正确。

---


