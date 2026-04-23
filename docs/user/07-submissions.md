# 评测

## 评测记录列表

访问「练习 > 评测」（`/evaluation`），可以查看提交记录列表。

列表显示以下信息：
- 提交编号（submission_no）
- 提交者
- 题目编号和标题
- 编程语言
- 判题结果（verdict）
- 得分
- 提交时间

支持按用户、题目、判题状态进行筛选。

## 提交详情

点击提交记录进入提交详情页（`/submission/:submissionNo`），可查看：

- 提交的代码
- 每个测试点的判题结果（通过/错误/超时等）
- 每个测试点的运行时间和内存占用
- 编译错误信息（如有）
- 总得分

## 判题流程

提交代码后经历以下阶段：

```
Pending → Running → Finished / Failed
```

| 阶段 | 说明 |
|------|------|
| Pending | 提交已接收，等待判题 |
| Running | 正在编译和运行测试 |
| Finished | 判题完成，有最终结果 |
| Failed | 系统错误导致判题失败 |

## 判题结果说明

| 结果 | 缩写 | 说明 |
|------|------|------|
| Accepted | AC | 所有测试点通过 |
| WrongAnswer | WA | 输出与标准答案不一致 |
| TimeLimitExceeded | TLE | 运行超过时间限制 |
| MemoryLimitExceeded | MLE | 内存使用超过限制 |
| RuntimeError | RE | 运行时错误（段错误、除以零、数组越界等） |
| CompileError | CE | 编译失败，可在详情中查看错误信息 |
| SystemError | SE | 判题系统内部错误 |

## 分数计算

- 每道题满分 100 分
- 部分赛制（IOI/NOI）支持按测试点给予部分分
- ACM 赛制下只有全部通过（100分）或不通过（0分）
