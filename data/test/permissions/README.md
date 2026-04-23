# 权限与访问控制测试

## 前置条件

- dev 环境运行中
- 预置用户角色：admin(SUPER_ADMIN)、manager(ADMIN)、teacher1/2(TEACHER)、student1~6(STUDENT)
- 预置资源权限（比赛/班级/题单的 WRITE 权限归创建者）

## 测试用例

### 角色级别权限

### PM1 — 学生访问管理页

- **角色**：student1（STUDENT）
- **步骤**：
  1. 登录 student1
  2. 直接访问 `/admin/users`
- **预期**：
  - 被重定向到 `/unauthorized`
  - 页面提示权限不足

### PM2 — 教师访问管理页

- **角色**：teacher1（TEACHER）
- **步骤**：
  1. 登录 teacher1
  2. 直接访问 `/admin/users`
- **预期**：
  - 被重定向到 `/unauthorized`
  - 页面提示权限不足

### PM3 — 管理员访问管理页

- **角色**：manager（ADMIN）
- **步骤**：
  1. 登录 manager
  2. 访问 `/admin/users`
- **预期**：
  - 正常显示用户管理页面
  - 可以看到用户列表

### PM4 — 管理员修改用户角色为 TEACHER

- **角色**：manager（ADMIN）
- **步骤**：
  1. 在用户管理页面找到 student1
  2. 将角色改为 TEACHER
- **预期**：
  - 角色变更成功
  - student1 重新登录后角色显示为 TEACHER

> 注意：此操作会改变 student1 的角色，后续测试注意

### PM5 — 管理员尝试设置 ADMIN 角色

- **角色**：manager（ADMIN）
- **步骤**：
  1. 尝试将某学生的角色设置为 ADMIN
- **预期**：
  - 操作被拒绝
  - 提示「仅 SUPER_ADMIN 可授予 ADMIN 角色」

### PM6 — 超级管理员设置 ADMIN 角色

- **角色**：admin（SUPER_ADMIN）
- **步骤**：
  1. 登录 admin
  2. 在用户管理页面将 student2 的角色设置为 ADMIN
- **预期**：
  - 角色变更成功
  - student2 重新登录后角色为 ADMIN
  - student2 可以访问 `/admin/users`

### PM7 — 设置 SUPER_ADMIN 被拒绝

- **角色**：admin（SUPER_ADMIN）
- **步骤**：
  1. 尝试通过界面将某用户设置为 SUPER_ADMIN
- **预期**：
  - 操作被拒绝
  - 提示「SUPER_ADMIN 角色仅可通过数据库操作授予」

---

### 资源级别权限

### PM8 — 资源权限授予

- **角色**：teacher2（题单3 的 WRITE 权限拥有者）
- **步骤**：
  1. 登录 teacher2
  2. 给 student3 授予题单3 的 READ 权限
- **预期**：
  - 授权成功
  - student3 登录后可以查看题单3

### PM9 — 资源权限撤销

- **角色**：teacher2
- **步骤**：
  1. 撤销 student1 对题单3 的 READ 权限
- **预期**：
  - 撤销成功
  - student1 刷新后不能再查看题单3

### PM10 — 非拥有者编辑资源

- **角色**：student1（对 teacher1 创建的题目无 WRITE 权限）
- **步骤**：
  1. 登录 student1
  2. 尝试编辑 teacher1 创建的题目（如 P1001）
- **预期**：
  - 编辑被拒绝或编辑入口不可见

### PM11 — 资源创建者自动获得 WRITE

- **步骤**：
  1. 用 teacher1 创建一个新题单
  2. 查看 resource_permission 表
- **预期**：
  - 自动创建 WRITE 权限记录
  - teacher1 可以编辑该题单

---

### 批量导入用户

### PM12 — 批量导入用户（正常）

- **角色**：admin（SUPER_ADMIN）
- **步骤**：
  1. 登录 admin
  2. 在用户管理页面点击「批量导入」
  3. 上传 `data/test/batch-import/uimport-success.xlsx`
- **预期**：
  - 用户创建成功
  - 导入报告显示创建数量
  - 新用户出现在用户列表中

### PM13 — 批量导入用户（重复）

- **角色**：admin
- **步骤**：
  1. 再次上传 `data/test/batch-import/uimport-reuse.xlsx`
- **预期**：
  - 已存在的用户被跳过
  - 报告显示跳过数量

### PM14 — 查看资源权限列表

- **角色**：teacher1
- **步骤**：
  1. 查看某个资源（如题单2）的权限列表
- **预期**：
  - 显示拥有权限的用户及其权限类型（READ/WRITE）
