# 开发模式指南

## 快速启动

```bash
# 首次：初始化子模块 + 准备环境变量
git submodule update --init --recursive
cp .env.example .env   # 按需编辑

# 启动开发环境（构建并启动，每次重置所有数据）
make dev_up             # → http://localhost:2281

# 停止
make dev_down
```

## 开发模式与生产模式的区别

| | 生产模式 (`make up`) | 开发模式 (`make dev_up`) |
|---|---|---|
| 数据目录 | `data/` | `data-dev/` |
| 前端端口 | 2280 | 2281 (HTTP) / 8443 (HTTPS) |
| MySQL 数据 | 持久化，跨重启保留 | **每次启动清空重建** |
| 种子数据 | 最小数据（1 个管理员） | 丰富测试数据（多角色用户、题目、比赛等） |
| judgend/agentend 数据 | 持久化 | 每次从 `data/*-seed/` 重新拷贝 |
| Compose 文件 | `base.yml` + `pro.yml` | `base.yml` + `dev.yml` |

## 常用命令

```bash
# 构建并启动（每次重置数据）
make dev_up

# 仅启动（不构建，仍重置数据）
make dev_run

# 仅构建镜像
make dev_build

# 停止
make dev_down

# 查看日志
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml logs -f
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml logs -f backend
```

## 每次 `make dev_up` / `make dev_run` 的执行流程

1. **`ensure_dirs`** — 检查 `.env`、`agent_config.yaml` 是否存在，创建数据子目录
2. **`copy_dev_assets`**（`scripts/copy_dev_assets.sh`）：
   - 清空 `data-dev/mysql/`，使 MySQL 下次启动时重新执行初始化脚本
   - 从 `data/judgend-seed/` 拷贝题目测试数据到 `data-dev/judgend/`
   - 从 `data/agent-seed/` 拷贝 Agent 数据到 `data-dev/agent/`
   - 从 `data/backend-seed/user-code/` 拷贝提交代码到 `data-dev/backend/data/user-code/`
3. **构建镜像**（仅 `dev_up`）
4. **启动容器**（`docker compose ... up -d`）
   - MySQL 首次启动时按文件名顺序执行 `/docker-entrypoint-initdb.d/` 下的 SQL

## 数据库初始化

MySQL 初始化脚本按文件名字母序执行：

| 文件 | 来源 | 内容 |
|------|------|------|
| `01-schema.sql` | `services/backend/sql/database_schema.sql` | 表结构（DDL） |
| `02-seed.sql` | `data/init-dev/` | 用户与角色 |
| `03-seed-problems.sql` | `data/init-dev/` | 12 道题目 |
| `04-seed-contests.sql` | `data/init-dev/` | 3 场比赛（已结束/进行中/未开始） |
| `05-seed-classes.sql` | `data/init-dev/` | 3 个班级 |
| `06-seed-assignments.sql` | `data/init-dev/` | 4 个作业（不同状态） |
| `07-seed-problem-sets.sql` | `data/init-dev/` | 3 个题单 |
| `08-seed-submissions.sql` | `data/init-dev/` | 57 条提交记录 |

## 测试账号

所有账号密码统一为 `password123`。

| 用户名 | 昵称 | 角色 |
|--------|------|------|
| `admin` | 超级管理员 | SUPER_ADMIN |
| `manager` | 管理员 | ADMIN |
| `teacher1` | 张老师 | TEACHER |
| `teacher2` | 李老师 | TEACHER |
| `student1` ~ `student6` | 王/赵/孙/周/吴/郑同学 | STUDENT |

开发环境默认启用 `VERIFICATION_DEV_FIXED_CODE_ENABLED=true`，注册时可使用固定验证码（见 `.env` 中的 `VERIFICATION_DEV_FIXED_CODE`）跳过邮件验证。
