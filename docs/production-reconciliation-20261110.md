# 生产代码整理记录（2026-11-10）

## 范围

以 /home/user/seuoj-deploy 当前生产工作树为依据，仅整理 OJ 生产代码。
隔离工作区：/home/user/seuoj-production-organize-20261110。
生产工作树、运行容器、数据目录及挂载配置没有被切换或覆盖；没有执行线上迁移。
开发与预览环境代码不在此次合并范围，QA 子模块版本保持不变。

## 模块提交

依次整理数据库及迁移、共享接口、账户权限与封禁、比赛名单与临时账户、
资源访问与提交可见性、Hydro 题包导入、Markdown 题面与中文字体、
比赛公告答疑、skip 与统计、重判队列、动态并发、Rust/proconio 和判题计分，
最后提交部署配置及子模块版本。提交使用 Conventional Commits。

旧功能分支已由生产实现覆盖的部分，使用显式保留生产树的合并记录；
判题端 SPJ 权重及 CPU 时间变更进行了实质合并并通过端到端验证。
字体提交先补齐 Markdown 依赖再合并。

## 必要修复

- 初始化 schema 补齐 allow_nickname_change 与 user_capability；
  account_permissions 迁移排在 contest_roster 之后，并说明只执行未应用的迁移。
- 临时令牌兑换由 AuthService 校验，普通接口仍拒绝临时令牌。
- judger 0.6.2 的 Python/General 规则补拦截 clone3，防止绕过线程限制；
  最小本地依赖补丁及 MIT 许可证保存在判题仓库 vendor/。
- 部署构建统一使用完整 Dockerfile，不依赖本机历史缓存镜像。
- 旧测试中的字段、PID 路径、用户信息和权限断言对齐生产接口；
  明确验证逻辑删除保留原始题目与关联关系。判题测试增加合成样例。

## 凭据与数据

.env、证书、密钥、备份、运行时数据和本机维护目录均排除在提交之外。
历史 fix/backend-configuration 分支含已跟踪 .env，未将该分支历史合入主分支；
所需安全配置采用独立提交。此次不会重写或删除远端旧分支历史。
其他虚拟主机原配置保留在未跟踪的 nginx/local-vhosts/shared-services.conf；
将来部署前保留该文件及其证书，详见维护说明。

已备份数据库与应用文件到 /home/user/seuoj-production-backups/git-organize-20261110，
校验压缩归档及 SHA-256；备份不在任何 Git 仓库内。

## 验证

前端完整构建与比赛名单导入检查通过；后端 290 项测试在独立 MySQL 库通过。
全新建库及旧 schema 逐条升级验证通过，均未访问生产数据库。
判题完整镜像构建及 36 项真实端到端检查通过，覆盖八种语言、
Rust 资源与沙箱限制、grader、SPJ CPU 参数、交互题和分组计分。
生产 Compose 配置和 OJ Nginx 语法检查通过；待推送新增历史另做凭据扫描。
详细日志保留在隔离工作区，不提交测试私钥、证书或数据库。

本次是代码归档与合并，不代表修复已发布到线上运行实例；后续发布另行安排。
