# SEUOJ 部署仓库

本仓库使用 Docker Compose 编排并部署 SEUOJ 的完整服务栈：`MySQL`、`backend`（Spring Boot）、`judgend`（Rust 判题端）、`agentend`（QA/Agent 服务）、`frontend`（Vite 构建 + Nginx 托管）。

## 服务架构
- `mysql`：`mysql:8.0`，初始化脚本来自 `data/init`
- `backend`：Spring Boot 服务（容器内 `8080`），依赖 `mysql` 与 `judgend`
- `judgend`：评测服务（容器内 `9090`），仅内部网络访问
- `agentend`：智能问答/Agent 服务，读取 `agent_config.yaml` 和 `data/agent`
- `frontend`：Nginx 提供静态资源并反代 `/api` 到 `backend`

服务定义见 `docker-compose.yml`，Nginx 配置见 `nginx/default.conf`。

## 快速开始

### 1) 准备子模块
本仓库的 `services/*` 是 Git Submodule，首次拉取后需初始化：

```bash
git submodule update --init --recursive
```

### 2) 准备环境变量
复制模板并按需修改：

```bash
cp .env.example .env
```

至少确认以下变量：
- `DB_ROOT_PASSWORD`
- `JWT_PRIVATE_KEY`
- `JWT_PUBLIC_KEY`
- `JWT_ACCESS_EXPIRATION`
- `JWT_TEMP_EXPIRATION`
- `JUDGE_SECRET`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `JUDGEND_MAX_CONCURRENT_REQUESTS`
- `JUDGEND_OUTPUT_TRUNCATE_LENGTH`
- `VERIFICATION_DEV_FIXED_CODE_ENABLED`
- `VERIFICATION_DEV_FIXED_CODE`

并确保根目录存在：
- `agent_config.yaml`

### 3) 启动

推荐使用：

```bash
make run
```

等价命令：

```bash
docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f
```

### 4) 访问
- 前端入口：`http://localhost:2280`
- API 入口：`http://localhost:2280/api/*`

说明：`backend` 与 `judgend` 默认不对宿主机暴露端口，通过 Docker 内部网络通信。

## 数据与挂载目录
- Agent 数据：`data/agent`
- 数据库数据：`data/mysql`
- 数据库初始化脚本：`data/init`
- 后端日志：`data/backend/log`
- 后端数据（如提交代码存储）：`data/backend/data`
- 判题资源目录（题目、测试数据、日志等）：`data/judgend`

## 常用命令

```bash
# 初始化目录与依赖（检查 .env / agent_config.yaml，准备 data 目录，拉取 aijlib）
make ensure_dirs

# 启动（默认）
make run

# 开发启动（会先拷贝 services/judgend/assets 到 data/judgend）
make dev_run

# 停止
make down

# 清理数据目录（交互确认后删除 data/agent data/backend data/judgend data/mysql）
make clean_data

# 以下为原生 docker compose 命令

# 重建并启动
docker compose up -d --build

# 停止并移除容器
docker compose down

# 仅看某个服务日志
docker compose logs -f backend
docker compose logs -f judgend
docker compose logs -f frontend

# 重启某个服务
docker compose restart backend

# 进入 MySQL 客户端
docker compose exec mysql mysql -uroot -p

# 单独重建某个服务
docker compose build frontend
```

## 目录结构
- `docker-compose.yml`：服务编排与环境变量注入
- `nginx/default.conf`：Nginx 静态托管与反向代理配置
- `Makefile`：常用运维命令封装（`run`/`dev_run`/`down`/`clean_data`）
- `scripts/ensure_dirs.sh`：检查配置并初始化 `data` 目录与 `aijlib`
- `scripts/copy_dev_assets.sh`：开发环境题目资源拷贝
- `scripts/clean_data.sh`：交互式清理数据目录
- `data/init`：MySQL 初始化脚本和配置
- `data/mysql`：MySQL 持久化数据
- `data/backend`：后端日志与业务数据
- `data/agent`：Agent 运行数据
- `data/judgend`：判题资源与 `aijlib`
- `services/backend`：后端源码与镜像构建上下文
- `services/frontend`：前端源码与镜像构建上下文
- `services/judgend`：判题端源码与镜像构建上下文
- `services/seuoj-qa`：Agent 服务源码与镜像构建上下文

## 运维提示
- 修改配置优先更新 `.env` 与 `docker-compose.yml`，避免在容器内手改。
- 代码更新后建议重新构建对应服务镜像。
- 如需重建数据库，先备份后清理 `data/mysql` 再执行 `docker compose up -d --build`。
