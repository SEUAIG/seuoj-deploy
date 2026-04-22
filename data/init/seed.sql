USE seuoj;

SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO `problem` (id, pid, title, total_submit, total_accept, is_public)
VALUES (1,  'P0001', 'a+b',           0, 0, 1),
       (2,  'P0002', '数组求和',       0, 0, 1),
       (3,  'P1001', '区间求和',       0, 0, 1),
       (4,  'P1002', '最大子段和',     0, 0, 1),
       (5,  'P1003', '括号序列的深度', 0, 0, 1),
       (6,  'P1004', '两数之和',       0, 0, 1),
       (7,  'P1005', '切绳子',         0, 0, 1),
       (8,  'P1006', '合并果子',       0, 0, 1),
       (9,  'P1007', '逆序对',         0, 0, 1),
       (10, 'P1008', '重排回文',       0, 0, 1),
       (11, 'P1009', '迷宫寻路',       0, 0, 1),
       (12, 'P1010', '岛屿计数',       0, 0, 1);

INSERT INTO `tag_group` (id, type, name, created_at, updated_at, is_del)
VALUES (1, 'algorithm', NULL, NOW(), NOW(), 0),
       (2, 'algorithm', '基础算法', NOW(), NOW(), 0),
       (3, 'algorithm', '高级算法', NOW(), NOW(), 0),
       (4, 'source', 'NOI系列赛事', NOW(), NOW(), 0),
       (5, 'source', '经典套题', NOW(), NOW(), 0),
       (6, 'source', '国际知名赛事', NOW(), NOW(), 0),
       (7, 'source', '大学竞赛', NOW(), NOW(), 0),
       (8, 'time', NULL, NOW(), NOW(), 0),
       (9, 'special', NULL, NOW(), NOW(), 0);

INSERT INTO `tag` (id, tag_name, group_id, created_at, updated_at, is_del)
VALUES (1, '贪心', 2, NOW(), NOW(), 0),
       (2, '动态规划', 2, NOW(), NOW(), 0),
       (3, '图论', 3, NOW(), NOW(), 0),
       (4, '前缀和', 2, NOW(), NOW(), 0),
       (5, '栈', 2, NOW(), NOW(), 0),
       (6, '双指针', 2, NOW(), NOW(), 0),
       (7, '二分', 2, NOW(), NOW(), 0),
       (8, '分治', 2, NOW(), NOW(), 0),
       (9, '字符串', 2, NOW(), NOW(), 0),
       (10, '搜索', 2, NOW(), NOW(), 0),
       (11, 'NOI', 4, NOW(), NOW(), 0),
       (12, 'NOIP', 4, NOW(), NOW(), 0),
       (13, 'NOI Online', 4, NOW(), NOW(), 0),
       (14, '经典套题一', 5, NOW(), NOW(), 0),
       (15, '经典套题二', 5, NOW(), NOW(), 0),
       (16, '经典套题三', 5, NOW(), NOW(), 0),
       (17, 'ICPC', 6, NOW(), NOW(), 0),
       (18, 'IOI', 6, NOW(), NOW(), 0),
       (19, 'Google Code Jam', 6, NOW(), NOW(), 0),
       (20, '校内赛', 7, NOW(), NOW(), 0),
       (21, '校级选拔赛', 7, NOW(), NOW(), 0),
       (22, '省赛', 7, NOW(), NOW(), 0),
       (23, '2000', 8, NOW(), NOW(), 0),
       (24, '2001', 8, NOW(), NOW(), 0),
       (25, '2002', 8, NOW(), NOW(), 0),
       (26, '2003', 8, NOW(), NOW(), 0),
       (27, '交互题', 9, NOW(), NOW(), 0),
       (28, '提交答案', 9, NOW(), NOW(), 0),
       (29, 'O2优化', 9, NOW(), NOW(), 0);

-- problem_id 对应: 1=P0001, 2=P0002, 3=P1001, ..., 12=P1010
INSERT INTO `problem_tag_rel` (id, problem_id, tag_id)
VALUES (1,  3,  4),   -- P1001 区间求和 → 前缀和
       (2,  4,  2),   -- P1002 最大子段和 → 动态规划
       (3,  5,  5),   -- P1003 括号序列 → 栈
       (4,  6,  6),   -- P1004 两数之和 → 双指针
       (5,  7,  7),   -- P1005 切绳子 → 二分
       (6,  8,  1),   -- P1006 合并果子 → 贪心
       (7,  9,  8),   -- P1007 逆序对 → 分治
       (8,  10, 9),   -- P1008 重排回文 → 字符串
       (9,  11, 10),  -- P1009 迷宫寻路 → 搜索
       (10, 11, 3),   -- P1009 迷宫寻路 → 图论
       (11, 12, 10),  -- P1010 岛屿计数 → 搜索
       (12, 12, 3);   -- P1010 岛屿计数 → 图论

INSERT INTO `user_info` (id, username, email, password)
VALUES (1, '123', '1234567891@qq.com', '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (2, 'test', 'test@test.com', '$2b$12$ieCFljnNZGJRUNhio1N/s.U8/8R35p74FXKIv/s/1G3pXuEMa1KrK'),
       (3, 'testu', 'testu@test.com', '$2a$10$LSfRC3/lPblawhSjqFUbdOq/kh5zAZGJe5Dwlofs/e8ydUlozesyu');

INSERT INTO `user_role` (id, role_code, role_name, is_del)
VALUES (1, 'STUDENT', '学生', 0),
       (2, 'TEACHER', '教师', 0),
       (3, 'ADMIN', '管理员', 0),
       (4, 'SUPER_ADMIN', '超级管理员', 0);

-- 用户角色关联：user_id=1(123) → SUPER_ADMIN, user_id=2(test) → ADMIN, user_id=3(testu) → TEACHER
INSERT INTO `user_role_rel` (id, user_id, role_id, is_del)
VALUES (1, 1, 4, 0),
       (2, 2, 3, 0),
       (3, 3, 2, 0);

INSERT INTO `contest` (
    `id`, `title`, `subtitle`, `description`, `start_time`, `end_time`, `rule_type`, `is_public`, `created_by_user_id`, `is_del`
)
VALUES (
           1,
           '春季训练赛',
           '热身赛',
           '用于集成测试的最小化预置比赛',
           '2026-03-01 09:00:00',
           '2026-03-01 12:00:00',
           'ACM',
           0,
           1,
           0
       );

INSERT INTO `class_info` (`id`, `name`, `description`, `is_public`, `created_by_user_id`, `is_del`)
VALUES (1, '班级一', '用于测试的最小化预置班级', 1, 3, 0);

INSERT INTO `problem_set` (`id`, `title`, `description`, `created_by_user_id`, `is_public`, `is_del`)
VALUES (1, '基础题单', '用于测试的最小化预置题单', 1, 1, 0);

INSERT INTO `contest_problem_rel` (`id`, `contest_id`, `problem_id`, `sort_order`, `is_del`)
VALUES (1, 1, 1, 1, 0),
       (2, 1, 2, 2, 0);

-- 创建者自动获得 WRITE 权限（替代原 contest_manager_rel）
-- contest id=1 → user_id=1 WRITE, problem_set id=1 → user_id=1 WRITE, class id=1 → user_id=3 WRITE
INSERT INTO `resource_permission` (`id`, `resource_type`, `resource_id`, `user_id`, `permission`, `granted_by`, `is_del`)
VALUES (1, 'CONTEST', 1, 1, 'WRITE', NULL, 0),
       (2, 'PROBLEM_SET', 1, 1, 'WRITE', NULL, 0),
       (3, 'CLASS', 1, 3, 'WRITE', NULL, 0);

INSERT INTO `contest_register_rel` (`id`, `contest_id`, `user_id`, `joined_at`, `is_del`)
VALUES (1, 1, 1, NOW(), 0);

INSERT INTO `problem_set_problem_rel` (`id`, `problem_set_id`, `problem_id`, `sort_order`, `is_del`)
VALUES (1, 1, 1, 1, 0),
       (2, 1, 2, 2, 0);

-- 作业（替代原 class_problem_set_rel）
INSERT INTO `assignment` (`id`, `class_id`, `problem_set_id`, `title`, `status`, `created_by_user_id`, `is_del`)
VALUES (1, 1, 1, '基础练习作业', 'PUBLISHED', 3, 0);

INSERT INTO `class_contest_rel` (`id`, `class_id`, `contest_id`, `is_del`)
VALUES (1, 1, 1, 0);

SET FOREIGN_KEY_CHECKS = 1;

