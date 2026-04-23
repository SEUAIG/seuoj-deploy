USE seuoj;

SET FOREIGN_KEY_CHECKS = 0;

-- 12 道题目，覆盖不同难度和类型
INSERT INTO `problem` (id, pid, title, total_submit, total_accept, is_public, created_by_user_id)
VALUES (1,  'P0001', 'a+b',           10, 8, 1, 1),
       (2,  'P0002', '数组求和',       6,  4, 1, 1),
       (3,  'P1001', '区间求和',       5,  3, 1, 3),
       (4,  'P1002', '最大子段和',     4,  2, 1, 3),
       (5,  'P1003', '括号序列的深度', 3,  1, 1, 3),
       (6,  'P1004', '两数之和',       8,  6, 1, 1),
       (7,  'P1005', '切绳子',         3,  2, 1, 3),
       (8,  'P1006', '合并果子',       4,  2, 1, 4),
       (9,  'P1007', '逆序对',         2,  1, 1, 4),
       (10, 'P1008', '重排回文',       3,  1, 1, 4),
       (11, 'P1009', '迷宫寻路',       5,  2, 1, 3),
       (12, 'P1010', '岛屿计数',       4,  1, 1, 3);

-- 标签分组
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

-- 标签
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

-- 题目-标签关联
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

SET FOREIGN_KEY_CHECKS = 1;
