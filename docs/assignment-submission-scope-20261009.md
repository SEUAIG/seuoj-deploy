# 生产发布：作业提交记录与统计口径

发布时间：2026-10-09（北京时间）。服务器目录：`/home/user/seuoj-deploy`。

## 问题与发布范围

作业页原先用通用提交接口，只筛选明确关联作业的记录；统计页按班级成员对作业题目的全部历史记录统计，造成数量不一致。

本次生产更新前后端的作业提交查询、范围切换、筛选与统计说明。开发环境的 AI 功能、模型配置、开发标识和隔离部署配置不属于本次生产发布范围。生产数据库不需要迁移；历史提交的关联字段保持原样。

示例入口：<https://www.seuoj.best/class/1/assignment/1>。

- 默认“解题记录（统计口径）”显示本班成员对作业题目的全部历史记录，含未关联与关联其他作业的记录，不限作业时间。
- “本作业入口提交”只显示明确关联本作业的记录。
- 班级管理者可看全班，其他用户仅查看自己；分页及题号、结果、语言、用户名筛选保留。
- 统计页注明历史通过题目不等同于本次作业提交或按时完成。

## 代码提交

- 后端：`1e9546902d72bbc46665bd6a165970a4e1c816c7`，分支 `codex/assignment-submission-scope`。
- 前端：`09cf7cd2ee3d5238107589c11285f84480d42b22`，分支 `codex/assignment-submission-scope`。
- 部署主仓库更新上述两个子模块引用，并记录本说明；主仓库保留原 `main` 分支。

本次 Git 提交在服务器生产仓库完成。没有将既有 `data/init/02-seed.sql` 改动、环境变量文件、证书、历史备份、未跟踪的生产配置文件或运行数据纳入本次提交。

## 构建与正式域名验收

使用生产当前实际的四层 Compose 配置构建，仅更新前后端容器：

```bash
cd /home/user/seuoj-deploy
docker compose -f docker-compose.base.yml -f docker-compose.pro.yml \
  -f docker-compose.proxy.yml -f docker-compose.tls.yml build backend frontend
docker compose -f docker-compose.base.yml -f docker-compose.pro.yml \
  -f docker-compose.proxy.yml -f docker-compose.tls.yml up -d --no-deps backend frontend
```

生产后端构建运行四项新增范围/权限单元测试，全部通过；前端 TypeScript/Vite 构建通过。通过正式 HTTPS 域名完成九项只读检查：站点可用、列表与统计总量一致、分页无重复、班级/题目范围正确、关联作业范围保留、结果/题号/语言/用户名筛选、非管理用户只能查看本人、无效范围与班级不匹配拒绝、匿名拒绝。

验收时作业 1 的默认历史记录为 **666 次、53 人**，明确关联记录为 **69 次**；班级成员为 **54 人**。这是验收快照，后续提交可能使数量变化。检查登录令牌仅在进程内存中生成，短时有效，未写入日志或文件；验收没有增加生产提交或用户。

数据库及判题容器未重启，生产域名、证书、网络、端口和运行数据配置保持原样。

## 回退与记录

发布前代码、镜像及构建/验收记录保存在：

`/home/user/seuoj-deploy/data/maintenance-assignment-scope-20261009T152418/`

其中 `source-before.tar.gz` 为发布前相关代码，`build.log` 为构建记录，`production-check.json` 为只读检查结果，`rollback-images.txt` 为发布前镜像标签。

如需回退运行版本，在生产目录执行下面的镜像回退；它不修改数据库：

```bash
docker image tag seuoj-production-backend:before-assignment-scope-20261009T152418 seuoj-deploy-backend:latest
docker image tag seuoj-production-frontend:before-assignment-scope-20261009T152418 seuoj-deploy-frontend:latest
docker compose -f docker-compose.base.yml -f docker-compose.pro.yml \
  -f docker-compose.proxy.yml -f docker-compose.tls.yml up -d --no-build --no-deps backend frontend
```
