USE seuoj;

SET FOREIGN_KEY_CHECKS = 0;

-- 用户：10 个，覆盖各角色
-- 密码统一为 password123 的 bcrypt hash
INSERT INTO `user_info` (id, username, nickname, email, password)
VALUES (1,  'admin',    '超级管理员',  'admin@seuoj.local',     '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO'),
       (2,  'manager',  '管理员',      'manager@seuoj.local',   '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO'),
       (3,  'teacher1', '张老师',      'teacher1@seuoj.local',  '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO'),
       (4,  'teacher2', '李老师',      'teacher2@seuoj.local',  '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO'),
       (5,  'student1', '王同学',      'student1@seuoj.local',  '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO'),
       (6,  'student2', '赵同学',      'student2@seuoj.local',  '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO'),
       (7,  'student3', '孙同学',      'student3@seuoj.local',  '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO'),
       (8,  'student4', '周同学',      'student4@seuoj.local',  '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO'),
       (9,  'student5', '吴同学',      'student5@seuoj.local',  '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO'),
       (10, 'student6', '郑同学',      'student6@seuoj.local',  '$2a$10$gGuRkoWkCkHUaNAWoGCZ7uNRIB40CzwpNX6incj/dj8cXH8DhklIO');

INSERT INTO `user_role` (id, role_code, role_name, is_del)
VALUES (1, 'STUDENT', '学生', 0),
       (2, 'TEACHER', '教师', 0),
       (3, 'ADMIN', '管理员', 0),
       (4, 'SUPER_ADMIN', '超级管理员', 0);

-- admin=SUPER_ADMIN, manager=ADMIN, teacher1/2=TEACHER, student1-6=STUDENT
INSERT INTO `user_role_rel` (id, user_id, role_id, is_del)
VALUES (1,  1,  4, 0),
       (2,  2,  3, 0),
       (3,  3,  2, 0),
       (4,  4,  2, 0),
       (5,  5,  1, 0),
       (6,  6,  1, 0),
       (7,  7,  1, 0),
       (8,  8,  1, 0),
       (9,  9,  1, 0),
       (10, 10, 1, 0);


INSERT INTO `tag_group` (id, type) VALUES (1, 'algorithm'), (2, 'source'), (3, 'time'), (4, 'special');

INSERT INTO `tag` (id, tag_name, group_id) VALUES 
(1, '动态规划', 1), (2, '贪心算法', 1), (3, '回溯算法', 1), (4, '树', 1), (5, '图', 1),
(6, '字符串', 1), (7, '数组', 1), (8, '链表', 1), (9, '哈希表', 1), (10, '堆', 1),
(11, '排序', 1), (12, '搜索', 1), (13, '数学', 1), (14, '位运算', 1), (15, '双指针', 1),
(16, '滑动窗口', 1), (17, '分治算法', 1), (18, '回文串', 1), (19, '并查集', 1), (20, '线段树', 1),
(21, '字符串匹配算法', 1), (22, '拓扑排序', 1), (23, '动态规划优化技巧', 1), (24, '树形DP', 1), (25, '状态压缩DP', 1),
(26, '单调栈/队列', 1), (27, '位运算技巧', 1), (28, '数学问题技巧', 1), (29, '图论算法技巧', 1), (30, '其他算法技巧', 1),
(31, '洛谷', 2), (32, '牛客网', 2), (33, '力扣', 2), (34, 'Codeforces', 2), (35, 'AtCoder', 2), (38, '其他平台', 2),
(39, '2029年', 3), (40, '2028年', 3), (41, '2027年', 3), (42, '2026年', 3), (43, '2025年及以前', 3),
(44, '交互', 4), (45, 'SPJ', 4), (46, '其他', 4);

SET FOREIGN_KEY_CHECKS = 1;
