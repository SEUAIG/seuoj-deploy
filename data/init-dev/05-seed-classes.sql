USE seuoj;

SET FOREIGN_KEY_CHECKS = 0;

-- 3 个班级：公开(teacher1)、非公开(teacher1)、公开(teacher2)
INSERT INTO `class_info` (id, name, description, introduction, is_public, created_by_user_id, is_del)
VALUES (1, '数据结构与算法 2026春', '面向大二学生的数据结构与算法课程班级',
        '## 课程简介\n\n本课程覆盖常见数据结构（链表、栈、队列、树、图）和算法（排序、搜索、动态规划等）。\n\n### 考核方式\n- 平时作业 40%\n- 期末考试 60%',
        1, 3, 0),
       (2, '算法竞赛训练营', '高级算法竞赛训练，非公开，需申请加入',
        '## 训练营说明\n\n面向有一定基础的同学，进行 ACM/ICPC 竞赛准备。\n\n每周安排：\n1. 周三晚专题讲解\n2. 周末虚拟赛',
        0, 3, 0),
       (3, 'C语言程序设计 2026春', '面向大一新生的 C 语言入门课程',
        '## 课程目标\n\n掌握 C 语言基础语法、指针、数组、结构体等核心概念。',
        1, 4, 0);

-- 班级学生：班级1(6个学生)、班级2(3个学生)、班级3(4个学生)
INSERT INTO `class_student_rel` (id, class_id, user_id, joined_at, is_del)
VALUES (1,  1, 5,  '2026-02-20 09:00:00', 0),
       (2,  1, 6,  '2026-02-20 09:00:00', 0),
       (3,  1, 7,  '2026-02-20 09:00:00', 0),
       (4,  1, 8,  '2026-02-20 09:00:00', 0),
       (5,  1, 9,  '2026-02-21 10:00:00', 0),
       (6,  1, 10, '2026-02-21 10:00:00', 0),
       (7,  2, 5,  '2026-03-01 14:00:00', 0),
       (8,  2, 6,  '2026-03-01 14:00:00', 0),
       (9,  2, 7,  '2026-03-05 16:00:00', 0),
       (10, 3, 7,  '2026-02-25 09:00:00', 0),
       (11, 3, 8,  '2026-02-25 09:00:00', 0),
       (12, 3, 9,  '2026-02-25 09:00:00', 0),
       (13, 3, 10, '2026-02-25 09:00:00', 0);

-- 班级-比赛关联：班级1关联比赛1和比赛3，班级2关联比赛2
INSERT INTO `class_contest_rel` (id, class_id, contest_id, is_del)
VALUES (1, 1, 1, 0),
       (2, 1, 3, 0),
       (3, 2, 2, 0);

-- 班级权限：创建者 WRITE
INSERT INTO `resource_permission` (id, resource_type, resource_id, user_id, permission, granted_by, is_del)
VALUES (4, 'CLASS', 1, 3, 'WRITE', NULL, 0),
       (5, 'CLASS', 2, 3, 'WRITE', NULL, 0),
       (6, 'CLASS', 3, 4, 'WRITE', NULL, 0);

SET FOREIGN_KEY_CHECKS = 1;
