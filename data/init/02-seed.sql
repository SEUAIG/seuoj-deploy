USE seuoj;

SET FOREIGN_KEY_CHECKS = 0;

-- 默认超级管理员，密码: password
INSERT INTO `user_info` (id, username, nickname, email, password)
VALUES (1, 'superadmin', '超级管理员', 'superadmin@seuoj.com', '$2b$10$VmLiZ79E7flaf//Gmy7gFOMDnMDlV/IVIaexzZHcuCBYrrkPLvDci');

INSERT INTO `user_role` (id, role_code, role_name, is_del)
VALUES (1, 'STUDENT', '学生', 0),
       (2, 'TEACHER', '教师', 0),
       (3, 'ADMIN', '管理员', 0),
       (4, 'SUPER_ADMIN', '超级管理员', 0);

INSERT INTO `user_role_rel` (id, user_id, role_id, is_del)
VALUES (1, 1, 4, 0);

SET FOREIGN_KEY_CHECKS = 1;
