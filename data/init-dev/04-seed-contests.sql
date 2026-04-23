USE seuoj;

SET FOREIGN_KEY_CHECKS = 0;

-- 3 场比赛：已结束(ACM)、进行中(IOI)、未开始(NOI)
INSERT INTO `contest` (id, title, subtitle, description, start_time, end_time, rule_type, is_public, created_by_user_id, is_del)
VALUES (1, '2026 春季训练赛', '热身赛', '已结束的 ACM 赛制训练赛，可查看历史排名和提交记录。',
        '2026-03-01 09:00:00', '2026-03-01 12:00:00', 'ACM', 1, 1, 0),
       (2, '算法周赛 #5', '第五周', '正在进行的 IOI 赛制周赛，部分分计分。',
        '2026-04-01 09:00:00', '2026-12-31 23:59:59', 'IOI', 1, 3, 0),
       (3, '期末模拟赛', NULL, '尚未开始的 NOI 赛制模拟赛，仅班级内学生可参加。',
        '2026-07-01 09:00:00', '2026-07-01 14:00:00', 'NOI', 0, 3, 0);

-- 比赛题目关联
-- 比赛1: P0001(a+b), P0002(数组求和), P1001(区间求和)
INSERT INTO `contest_problem_rel` (id, contest_id, problem_id, sort_order, is_del)
VALUES (1, 1, 1, 1, 0),
       (2, 1, 2, 2, 0),
       (3, 1, 3, 3, 0),
       -- 比赛2: P1002(最大子段和), P1003(括号序列), P1004(两数之和), P1005(切绳子)
       (4, 2, 4, 1, 0),
       (5, 2, 5, 2, 0),
       (6, 2, 6, 3, 0),
       (7, 2, 7, 4, 0),
       -- 比赛3: P1006(合并果子), P1007(逆序对), P1009(迷宫寻路)
       (8, 3, 8,  1, 0),
       (9, 3, 9,  2, 0),
       (10, 3, 11, 3, 0);

-- 报名：比赛1(已结束)全部学生已报名，比赛2(进行中)部分学生已报名
INSERT INTO `contest_register_rel` (id, contest_id, user_id, joined_at, is_del)
VALUES (1,  1, 5,  '2026-02-28 10:00:00', 0),
       (2,  1, 6,  '2026-02-28 11:00:00', 0),
       (3,  1, 7,  '2026-02-28 14:00:00', 0),
       (4,  1, 8,  '2026-02-28 16:00:00', 0),
       (5,  1, 9,  '2026-03-01 08:00:00', 0),
       (6,  1, 10, '2026-03-01 08:30:00', 0),
       (7,  2, 5,  '2026-04-01 08:00:00', 0),
       (8,  2, 6,  '2026-04-01 08:30:00', 0),
       (9,  2, 7,  '2026-04-01 09:00:00', 0),
       (10, 2, 8,  '2026-04-01 09:15:00', 0);

-- 比赛权限：创建者 WRITE
INSERT INTO `resource_permission` (id, resource_type, resource_id, user_id, permission, granted_by, is_del)
VALUES (1, 'CONTEST', 1, 1, 'WRITE', NULL, 0),
       (2, 'CONTEST', 2, 3, 'WRITE', NULL, 0),
       (3, 'CONTEST', 3, 3, 'WRITE', NULL, 0);

SET FOREIGN_KEY_CHECKS = 1;
