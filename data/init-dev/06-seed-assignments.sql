USE seuoj;

SET FOREIGN_KEY_CHECKS = 0;

-- 4 个作业：PUBLISHED(有截止时间)、PUBLISHED(无截止时间)、DRAFT、PUBLISHED(已过关闭时间)
INSERT INTO `assignment` (id, class_id, title, description, introduction, status, deadline, visible_from, visible_to, created_by_user_id, is_del)
VALUES (1, 1, '第一周练习：基础算法', '涵盖前缀和、栈、双指针等基础算法题目',
        '## 作业说明\n\n请在截止日期前完成以下题目，注意代码规范。',
        'PUBLISHED', '2026-04-30 23:59:59', '2026-03-01 00:00:00', NULL, 3, 0),
       (2, 1, '第二周练习：进阶算法', '涵盖分治、二分、贪心等进阶算法题目',
        '## 作业说明\n\n进阶难度作业，可参考课件资料。',
        'PUBLISHED', NULL, '2026-03-08 00:00:00', NULL, 3, 0),
       (3, 1, '第三周练习：图论入门', '图论基础题目（草稿状态，未发布）',
        NULL,
        'DRAFT', '2026-05-15 23:59:59', NULL, NULL, 3, 0),
       (4, 1, '寒假预习作业', '寒假期间的预习练习（已关闭）',
        '## 注意\n\n该作业已截止，不再接受提交。',
        'PUBLISHED', '2026-02-15 23:59:59', '2026-01-15 00:00:00', '2026-02-15 23:59:59', 3, 0);

-- 作业题目关联
-- 作业1: P1001(区间求和), P1003(括号序列), P1004(两数之和)
INSERT INTO `assignment_problem_rel` (id, assignment_id, problem_id, sort_order, weight, is_del)
VALUES (1, 1, 3, 1, 1, 0),
       (2, 1, 5, 2, 1, 0),
       (3, 1, 6, 3, 2, 0),
       -- 作业2: P1005(切绳子), P1006(合并果子), P1007(逆序对)
       (4, 2, 7,  1, 1, 0),
       (5, 2, 8,  2, 1, 0),
       (6, 2, 9,  3, 2, 0),
       -- 作业3(草稿): P1009(迷宫寻路), P1010(岛屿计数)
       (7, 3, 11, 1, 1, 0),
       (8, 3, 12, 2, 1, 0),
       -- 作业4(已过关闭时间): P0001(a+b), P0002(数组求和)
       (9,  4, 1, 1, 1, 0),
       (10, 4, 2, 2, 1, 0);

-- 公告
INSERT INTO `announcement` (id, target_type, target_id, title, content, is_pinned, created_by_user_id, is_del)
VALUES (1, 'CLASS', 1, '欢迎加入数据结构与算法课程',
        '## 欢迎\n\n请同学们及时完成每周作业，有问题可在课上讨论。\n\n**课程群号：123456**',
        1, 3, 0),
       (2, 'CLASS', 1, '第二周课程延期通知',
        '由于清明节放假，第二周课程延期至下周三。',
        0, 3, 0),
       (3, 'ASSIGNMENT', 1, '第一周作业补充说明',
        '第三题（两数之和）请注意时间复杂度要求 O(n)。',
        0, 3, 0),
       (4, 'CLASS', 2, '训练营安排',
        '本周六下午 2 点进行虚拟赛，请提前注册。',
        1, 3, 0);

SET FOREIGN_KEY_CHECKS = 1;
