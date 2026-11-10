# 生产环境维护说明

本文件描述 2026-11-10 整理后的生产配置。代码整理不会自动部署、重启容器或执行数据库迁移。
学校服务器工作目录为 /home/user/seuoj-deploy，公网入口为 https://seuoj.best/，
校园内网 HTTP 维护入口为 http://10.201.3.94:2280。公网转发及 WireGuard 由服务器管理员维护。

## 配置与数据

- 核心服务为 mysql、backend、judgend、frontend；AI 服务仅在 ai profile 显式启用。
- 数据位于 data/mysql、data/backend、data/judgend；证书位于 data/certs。
- .env、证书私钥、Cloudflare 令牌和备份均不进入 Git。保留原文件及权限。
- 生产覆盖层使用 prod profile，并强制关闭固定验证码。配置实际 SMTP 后才能邮件注册。
- 构建下载代理由环境变量指定；正常提供 OJ 服务不依赖构建代理。

## 生产配置组合

使用 Docker Compose v2（需要支持 !override）。检查配置时只运行 config --quiet，
不要把展开后的含密钥配置粘贴到日志或仓库。

```sh
cd /home/user/seuoj-deploy
docker compose -f docker-compose.base.yml -f docker-compose.pro.yml -f docker-compose.proxy.yml -f docker-compose.security.yml -f docker-compose.tls.yml config --quiet
```

计划发布时先备份，确认迁移记录、镜像和挂载目录，再使用同一组合构建并安排服务切换。
不要在服务运行期间直接切换子模块、覆盖 bind mount 配置或使用 compose down -v。
判题端使用公开基础镜像的 Dockerfile；homework-build 覆盖层仅为兼容旧命令，
不再依赖本机 before-homework 或 security 缓存镜像。

## 本机共用的其他虚拟主机

OJ 的 nginx/core-tls.conf 仅包含 OJ 入口，并 include /etc/nginx/local-vhosts/*.conf。
nginx/local-vhosts/ 被 Git 忽略，通过 TLS 覆盖层只读挂载。
原服务器同一配置中的其他虚拟主机已原样保存在整理副本的
nginx/local-vhosts/shared-services.conf（未提交）。将来部署前必须保留该文件、
其上游及引用的证书，才能继续提供服务器共用入口。此次没有修改线上 Nginx 配置。

## HTTPS

保留 seuoj.best 和 www.seuoj.best 的有效证书，放入 data/certs/fullchain.pem 和 privkey.pem。
DNS API 凭据保留在主机受限权限文件中，由 acme.sh 续期；不需要放入应用源码或镜像。
域名 HTTP 跳转 HTTPS，IP:2280 保留 HTTP 维护入口；账户操作使用 HTTPS。

## 数据库

全新数据库使用 services/backend/sql/database_schema.sql。
已有数据库仅按 sql/migrations/README.md 检查尚未执行的增量迁移；
不能对已有数据库运行包含 DROP TABLE 的全量初始化脚本。
迁移、构建与部署不会由 Git 提交自动执行。

## 本次整理备份

备份目录：/home/user/seuoj-production-backups/git-organize-20261110。
包含数据库逻辑备份、应用文件和证书归档、校验值、初始行数和容器基线。
目录仅管理员可读；备份、源代码快照均不提交仓库。
历史恢复记录见 MIGRATION-20260921.md，该文档中的数量和网络状态仅表示当时情况。
