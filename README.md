# SEUOJ 部署仓库

本仓库使用 Docker Compose 编排并一键部署 SEUOJ 的完整服务栈：`MySQL` 数据库、`后端`（Spring Boot）、`判题端 Judgend`（Rust）、`前端 + Nginx`。开箱即用，专注于稳定运行与易维护。

---

## 架构概览
- **数据库**: `mysql:8.0`，初始化脚本来自 [data/init](data/init)，数据持久化到 [data/mysql](data/mysql)
- **后端**: Spring Boot 服务，日志落地到 [data/backend](data/backend)，通过环境变量配置数据库与判题端
- **判题端**: `judgend` 服务，资产目录挂载 [services/judgend/assets](services/judgend/assets)（题目、日志）
- **前端 + Nginx**: 构建产物由 Nginx 提供，外部暴露 `80` 端口；Nginx 反向代理后端 API（详见 [nginx/default.conf](nginx/default.conf)）

服务编排见 [docker-compose.yml](docker-compose.yml)，全局环境变量见 [.env](.env)。

---

## 快速开始

### 先决条件
- 已安装 `Docker`（建议 20+）与 `Docker Compose v2`（`docker compose` 命令）

### 启动步骤
1. 编辑 [.env](.env)，至少修改：
   - `DB_ROOT_PASSWORD`：数据库 root 密码
   - `JWT_SECRET`：JWT 签名密钥（务必设置为高强度随机串）
   - `JUDGE_SECRET`：后端与判题端之间的共享密钥（需一致）
2. 启动服务（首次启动会自动初始化数据库与镜像构建）：

```bash
# 后台启动并构建镜像
docker compose up -d --build

# 查看整体日志（可选）
docker compose logs -f
```

3. 访问前端：
   - 打开浏览器访问 `http://localhost:80`

> 说明：后端与判题端无需对外暴露端口，均通过内部网络互通；Nginx 负责对外提供前端并代理后端 API。

---

## 环境变量（.env）
- **`DB_ROOT_PASSWORD`**: MySQL root 密码；后端用该密码连接数据库。
- **`JWT_SECRET`**: 后端 JWT 签名密钥；用于签发与校验令牌。
- **`JUDGE_SECRET`**: 后端与判题端共享密钥；不一致会导致判题请求拒绝。
- **`JUDGEND_MAX_CONCURRENT_REQUESTS`**: 判题端最大并发评测数。
- **`JUDGEND_OUTPUT_TRUNCATE_LENGTH`**: 评测输出截断长度。

后端数据库与 MyBatis、JWT、判题端等配置通过 compose 中的环境变量传入，详见 [docker-compose.yml](docker-compose.yml)。

---

## 数据与持久化
- **数据库数据**: 映射到宿主机 [data/mysql](data/mysql)
- **数据库初始化脚本**: 放置于 [data/init](data/init)，容器首次启动时自动执行（例如 `init.sql`）
- **后端日志**: 输出至 [data/backend](data/backend)
- **判题端资产**: 题目与日志位于 [services/judgend/assets](services/judgend/assets)

> 若需「清空数据库并重建」：先停止服务，再备份或删除 `data/mysql` 目录后重新 `up`。

---

## 常用命令
```bash
# 启动（后台）
docker compose up -d

# 首次或修改 Dockerfile 后建议带构建
docker compose up -d --build

# 停止并移除容器
docker compose down

# 重启某个服务
docker compose restart backend

# 查看指定服务日志
docker compose logs -f backend

docker compose logs -f judgend

# 进入 MySQL 客户端
docker compose exec mysql mysql -uroot -p

# 仅重新构建指定服务
docker compose build frontend
```

---

## 端口与访问
- **前端**: `http://localhost:80`
- **后端**: 仅容器内访问，由 Nginx 或判题端通过 Docker 网络调用
- **判题端**: 不对外暴露端口，内部监听 `9090`

---

## 目录结构速览
- [docker-compose.yml](docker-compose.yml): 服务编排与环境变量注入
- [data/mysql](data/mysql): MySQL 持久化数据目录
- [data/init](data/init): MySQL 初始化脚本目录（如 `init.sql`）
- [data/backend](data/backend): 后端日志输出目录
- [nginx/default.conf](nginx/default.conf): Nginx 站点与反向代理配置
- [services/backend](services/backend): 后端工程与镜像构建上下文
- [services/frontend](services/frontend): 前端工程与镜像构建上下文
- [services/judgend](services/judgend): 判题端工程与镜像构建上下文

---

## 运维与开发建议
- **修改配置**: 优先通过 [.env](.env) 与 [docker-compose.yml](docker-compose.yml) 管理；避免在容器内改动。
- **变更代码后重启**:

```bash
# 变更任一服务代码后
docker compose build backend frontend judgend

docker compose up -d
```

- **题目与日志管理**: 将题面与测试数据放在 [services/judgend/assets](services/judgend/assets) 下；注意容量与备份。
