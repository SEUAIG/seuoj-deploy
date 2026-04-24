# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

被指派任务时，在任务全部结束后，必须用中文报告 "所有任务已经完成"

使用 uv 管理 Python 环境。

## Project Overview

SEUOJ is a multi-service Online Judge system for Southeast University. This is the **deployment orchestration repo** — the four services live in Git submodules under `services/`. All inter-service communication is HTTP REST over a Docker bridge network; only Nginx (port 2280) is exposed to the host.

## Common Commands

```bash
# First-time setup
git submodule update --init --recursive
cp .env.example .env   # then edit .env
# also create agent_config.yaml from services/seuoj-qa/config/example.yaml

# Production start (data persists across restarts, uses data/ directory)
make up                     # → http://localhost:2280  (build + start)
make run                    # start only (no build)
make build                  # build only

# Dev/test start (resets ALL data on every run, uses data-dev/ directory)
# - Wipes data-dev/mysql so MySQL init scripts (schema + seed) re-execute
# - Copies seed data fresh into data-dev/judgend and data-dev/agent
# - Completely isolated from production, different ports (2281/8443)
make dev_up                 # → http://localhost:2281  (build + start)
make dev_run                # start only (no build, still resets data)
make dev_build              # build only

# Stop (production)
make down

# Stop (dev)
make dev_down

# Logs
docker compose logs -f backend
docker compose logs -f judgend

# Rebuild a single service
docker compose build backend && docker compose up -d backend

# MySQL shell
docker compose exec mysql mysql -uroot -p

# Clean all data (interactive confirm, uses sudo)
make clean_data
```

### Per-submodule development

**Backend** (Java 21, Spring Boot 3.2, Maven):
```bash
cd services/backend
./mvnw clean package -DskipTests          # build JAR
./mvnw test                                # all tests (needs local MySQL + test config)
./mvnw test -Dtest=AuthzIntegrationTest    # single test class
```
Tests require a local MySQL with the `seuoj` schema loaded. Copy `src/test/resources/application-test.yml.template` to `application-test.yml` and set `TEST_DB_USERNAME`/`TEST_DB_PASSWORD`.

**Frontend** (React 18, TypeScript 5.6, Vite 5):
```bash
cd services/frontend
npm install
npm run dev       # dev server on 0.0.0.0:5173
npm run build     # tsc + vite build
npm run lint      # eslint
```

**Judgend** (Rust, Axum 0.8):
```bash
cd services/judgend
cargo build --release
cargo test                          # all tests
cargo test submission               # single test module
```
Requires `libseccomp-dev` on Linux and the language toolchains (gcc, python3, javac, node, go) to be in PATH.

**Agentend** (Python 3.10, FastAPI):
```bash
cd services/seuoj-qa
pip install -r requirements.txt
uvicorn src.api_server:app --host 0.0.0.0 --port 8002
```

## Architecture

```
Browser :2280 (prod) / :2281 (dev) ──> Nginx (frontend container)
                    ├── /           static SPA files
                    ├── /api/*  ──> backend:8080   (Spring Boot)
                    └── /agent/* ─> agentend:8002  (FastAPI)

backend:8080 ──> mysql:3306      (database)
             ──> judgend:9090     (submit for judging)
judgend:9090 ──> backend:8080     (PUT judge result callback)
```

### Submodule responsibilities

| Submodule | Tech | Role |
|-----------|------|------|
| `services/backend` | Java 21 / Spring Boot / MyBatis-Plus | REST API, auth (JWT Ed25519), business logic, MySQL access |
| `services/frontend` | React / TypeScript / Vite / Tailwind / shadcn/ui / Redux + React Query | SPA with Monaco editor, Markdown+KaTeX rendering, recharts, dnd-kit |
| `services/judgend` | Rust / Axum / Tokio | Async code judging with Seccomp sandbox, supports C/C++/Python/Java/Go/Node |
| `services/seuoj-qa` | Python / FastAPI / FAISS / Camel-AI | RAG-based AI QA, knowledge graph, lesson preparation |

### Key backend patterns

- **Auth**: `JwtAuthInterceptor` extracts JWT → `UserContextHolder` (ThreadLocal). `AuthAspect` (AOP) checks `@RequireRole` / `@AllowAnonymous` annotations on controllers.
- **Roles**: `STUDENT`, `TEACHER`, `ADMIN`, `SUPER_ADMIN` in `RoleType` enum. Role checks in service layer via `UserRoleService.isAdmin()` / `.isTeacher()`.
- **Resource access**: Problem visibility logic is distributed across `ProblemService`, `PermissionService`, and the `ProblemSourceType` enum, covering four contexts (DIRECT / CONTEST / PROBLEM_SET / ASSIGNMENT). Other resources (class, problem_set) have inline access checks in their services.
- **Soft delete**: All tables use `is_del` field. MyBatis-Plus handles this globally. Generated `active_*` columns enforce unique constraints only on non-deleted rows.
- **Entity convention**: External APIs expose `id` (auto-increment) directly. Timestamps: `created_at` / `updated_at`.

### Judging flow

1. Backend receives submission → writes to DB (PENDING) → POST to judgend
2. Judgend returns 202 immediately, judges async (semaphore-limited concurrency)
3. Compile → run each test case in Seccomp sandbox → check output (standard/special/interactive)
4. PUT result back to backend callback endpoint → DB updated to FINISHED

### Database initialization

Schema DDL 唯一来源为后端子模块 `services/backend/sql/database_schema.sql`。docker-compose 通过单文件 volume mount 将其挂载为 `/docker-entrypoint-initdb.d/01-schema.sql`，deploy repo 不维护 schema 副本。

- **Prod seed** (`data/init/02-seed.sql`): 最小必要数据 — 角色定义 + 默认管理员
- **Dev seed** (`data/init-dev/02-seed.sql` ~ `07-*.sql`): 丰富测试数据，按功能分组（用户/题目/比赛/班级/作业/题单），dev compose override 覆盖 prod seed 并追加额外文件

MySQL 首次启动时按文件名字母序执行 `/docker-entrypoint-initdb.d/` 下所有 `.sql`。`make dev_run` 每次清空 `data-dev/mysql` 以触发重新初始化。

### Data storage split

- **MySQL**: users, roles, problems metadata, submissions, contests, classes, tags
- **Judgend filesystem** (`data/judgend/`): problem content (problem.json), test data, checker binaries
- **Agentend** (`data/agent/`): FAISS indexes, knowledge graph JSON, SQLite chat DB

## Submodule Git Branches

| Submodule | Branch |
|-----------|--------|
| services/backend | master |
| services/frontend | main |
| services/judgend | dev |
| services/seuoj-qa | (default) |

## Environment

All service configuration is injected via `.env` → `docker-compose.yml` environment variables. Key secrets: `DB_ROOT_PASSWORD`, `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`, `JUDGE_SECRET`, `MAIL_PASSWORD`. Dev mode has `VERIFICATION_DEV_FIXED_CODE_ENABLED=true` to bypass email verification.
