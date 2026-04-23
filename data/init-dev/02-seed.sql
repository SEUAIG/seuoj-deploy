USE seuoj;

SET FOREIGN_KEY_CHECKS = 0;

-- 用户：10 个，覆盖各角色
-- 密码统一为 password123 的 bcrypt hash
INSERT INTO `user_info` (id, username, nickname, email, password)
VALUES (1,  'admin',    '超级管理员',  'admin@seuoj.local',     '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (2,  'manager',  '管理员',      'manager@seuoj.local',   '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (3,  'teacher1', '张老师',      'teacher1@seuoj.local',  '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (4,  'teacher2', '李老师',      'teacher2@seuoj.local',  '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (5,  'student1', '王同学',      'student1@seuoj.local',  '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (6,  'student2', '赵同学',      'student2@seuoj.local',  '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (7,  'student3', '孙同学',      'student3@seuoj.local',  '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (8,  'student4', '周同学',      'student4@seuoj.local',  '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (9,  'student5', '吴同学',      'student5@seuoj.local',  '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.'),
       (10, 'student6', '郑同学',      'student6@seuoj.local',  '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.');

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

SET FOREIGN_KEY_CHECKS = 1;
