USE seuoj;

SET FOREIGN_KEY_CHECKS = 0;

-- 3 个题单：公开(admin)、公开(teacher1)、非公开(teacher2)
INSERT INTO `problem_set` (id, title, description, created_by_user_id, is_public, is_del)
VALUES (1, '新手入门题单', '适合初学者的基础题目集合，从简单到中等难度。', 1, 1, 0),
       (2, '动态规划专题', '涵盖常见 DP 模型：线性 DP、区间 DP、树形 DP。', 3, 1, 0),
       (3, '竞赛选拔题集', '校内选拔赛备选题目（非公开）。', 4, 0, 0);

-- 题单题目关联
-- 题单1(新手入门): P0001, P0002, P1001, P1004
INSERT INTO `problem_set_problem_rel` (id, problem_set_id, problem_id, sort_order, is_del)
VALUES (1, 1, 1, 1, 0),
       (2, 1, 2, 2, 0),
       (3, 1, 3, 3, 0),
       (4, 1, 6, 4, 0),
       -- 题单2(DP专题): P1002, P1005, P1006
       (5, 2, 4, 1, 0),
       (6, 2, 7, 2, 0),
       (7, 2, 8, 3, 0),
       -- 题单3(选拔题集): P1007, P1009, P1010
       (8, 3, 9,  1, 0),
       (9, 3, 11, 2, 0),
       (10, 3, 12, 3, 0);

-- 题单权限：创建者 WRITE + 非公开题单给部分用户 READ
INSERT INTO `resource_permission` (id, resource_type, resource_id, user_id, permission, granted_by, is_del)
VALUES (7,  'PROBLEM_SET', 1, 1, 'WRITE', NULL, 0),
       (8,  'PROBLEM_SET', 2, 3, 'WRITE', NULL, 0),
       (9,  'PROBLEM_SET', 3, 4, 'WRITE', NULL, 0),
       (10, 'PROBLEM_SET', 3, 5, 'READ',  4,    0),
       (11, 'PROBLEM_SET', 3, 6, 'READ',  4,    0);

SET FOREIGN_KEY_CHECKS = 1;
