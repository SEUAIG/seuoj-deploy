# 测试手册

本目录包含 SEUOJ 系统各模块的手动测试用例，用于功能验证和回归测试。

## 测试环境

- 使用 dev 环境：`make dev_run`，访问 `http://localhost:2281`
- dev 环境每次启动会重置所有数据（清空 `data-dev/mysql`，重新执行 seed SQL）
- 邮箱验证码开发模式：`VERIFICATION_DEV_FIXED_CODE_ENABLED=true`，使用固定验证码即可

## 预置测试数据

### 用户账号

所有账号密码均为 `password123`。

| 用户名 | 昵称 | 角色 |
|--------|------|------|
| admin | 超级管理员 | SUPER_ADMIN |
| manager | 管理员 | ADMIN |
| teacher1 | 张老师 | TEACHER |
| teacher2 | 李老师 | TEACHER |
| student1 | 王同学 | STUDENT |
| student2 | 赵同学 | STUDENT |
| student3 | 孙同学 | STUDENT |
| student4 | 周同学 | STUDENT |
| student5 | 吴同学 | STUDENT |
| student6 | 郑同学 | STUDENT |

### 预置题目

12 道公开题目：P0001(a+b)、P0002(数组求和)、P1001~P1010（各类算法题）

### 预置比赛

| ID | 标题 | 赛制 | 状态 | 公开 |
|----|------|------|------|------|
| 1 | 2026 春季训练赛 | ACM | 已结束 | 是 |
| 2 | 算法周赛 #5 | IOI | 进行中 | 是 |
| 3 | 期末模拟赛 | NOI | 未开始 | 否 |

### 预置班级

| ID | 名称 | 公开 | 创建者 |
|----|------|------|--------|
| 1 | 数据结构与算法 2026春 | 是 | teacher1 |
| 2 | 算法竞赛训练营 | 否 | teacher1 |
| 3 | C语言程序设计 2026春 | 是 | teacher2 |

### 预置作业（班级1内）

| ID | 标题 | 状态 | 截止时间 |
|----|------|------|---------|
| 1 | 第一周练习：基础算法 | PUBLISHED | 2026-04-30 |
| 2 | 第二周练习：进阶算法 | PUBLISHED | 无 |
| 3 | 第三周练习：图论入门 | DRAFT | 2026-05-15 |
| 4 | 寒假预习作业 | CLOSED | 2026-02-15 |

### 预置题单

| ID | 标题 | 公开 | 创建者 |
|----|------|------|--------|
| 1 | 新手入门题单 | 是 | admin |
| 2 | 动态规划专题 | 是 | teacher1 |
| 3 | 竞赛选拔题集 | 否 | teacher2 |

题单3的 READ 权限已授予 student1 和 student2。

## 测试模块

| 模块 | 说明 |
|------|------|
| [认证流程](auth/README.md) | 注册、登录、密码重置 |
| [题目](problems/README.md) | 题目 CRUD、搜索、标签 |
| [比赛](contests/README.md) | 比赛全流程 |
| [班级](classes/README.md) | 班级管理、成员、公告 |
| [作业](assignments/README.md) | 作业流程 |
| [题单](problem-sets/README.md) | 题单 CRUD、权限 |
| [提交与判题](submissions/README.md) | 各语言提交、各种判题结果 |
| [权限](permissions/README.md) | 角色和资源权限控制 |
| [批量导入](batch-import/README.md) | 用户和学生批量导入（已有） |
