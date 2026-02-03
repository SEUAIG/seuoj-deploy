CREATE DATABASE IF NOT EXISTS seuoj
-- 字符集 排序规则等等
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE seuoj;

-- SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for problem
-- ----------------------------
DROP TABLE IF EXISTS `problem`;
CREATE TABLE `problem`  (
                            `id` bigint NOT NULL AUTO_INCREMENT,
                            `pid` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '题目编号',
                            `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '题目标题',
                            `total_submit` int NOT NULL DEFAULT 0,
                            `total_accept` int NOT NULL DEFAULT 0,
                            `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            `is_del` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除，0-未删除，1-已删除',
                            PRIMARY KEY (`id`) USING BTREE,
                            UNIQUE INDEX `pid`(`pid` ASC) USING BTREE,
                            FULLTEXT INDEX `idx_problem_title_ft`(`title`) WITH PARSER ngram
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '题目表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for problem_tag_rel
-- ----------------------------
DROP TABLE IF EXISTS `problem_tag_rel`;
CREATE TABLE `problem_tag_rel`  (
                                    `id` bigint NOT NULL AUTO_INCREMENT,
                                    `problem_id` bigint NOT NULL,
                                    `tag_id` bigint NOT NULL,
                                    `is_del` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除，0-未删除，1-已删除',
                                    PRIMARY KEY (`id`) USING BTREE,
                                    UNIQUE INDEX `uk_problem_tag_rel`(`problem_id` ASC, `tag_id` ASC) USING BTREE,
                                    INDEX `idx_problem_tag_rel_problem_id`(`problem_id` ASC) USING BTREE,
                                    INDEX `idx_problem_tag_rel_tag_id`(`tag_id` ASC) USING BTREE,
                                    CONSTRAINT `fk_problem_tag_rel_problem` FOREIGN KEY (`problem_id`) REFERENCES `problem` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
                                    CONSTRAINT `fk_problem_tag_rel_tag` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '题目标签关联表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for submission
-- ----------------------------
DROP TABLE IF EXISTS `submission`;
CREATE TABLE `submission`  (
                               `id` bigint NOT NULL AUTO_INCREMENT,
                               `submission_no` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT (uuid()) COMMENT 'Business identifier for external reference',
                               `user_id` bigint NOT NULL,
                               `problem_id` bigint NOT NULL,
                               `language` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                               `status` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生命周期状态：Pending/Running/Finished/Failed',
                               `verdict` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '最终判定状态：Accepted/WA/TLE/...',
                               `result_detail` json NULL COMMENT '评测详细信息',
                               `error_detail` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '编译/判题错误详情',
                               `submit_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               `finish_time` datetime NULL DEFAULT NULL COMMENT '评测完成时间',
                               `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                               `is_del` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除，0-未删除，1-已删除',
                               PRIMARY KEY (`id`) USING BTREE,
                               UNIQUE INDEX `uk_submission_no`(`submission_no` ASC) USING BTREE,
                               INDEX `idx_user`(`user_id` ASC) USING BTREE,
                               INDEX `idx_problem`(`problem_id` ASC) USING BTREE,
                               INDEX `idx_status`(`status` ASC) USING BTREE,
                               INDEX `idx_user_time`(`user_id` ASC, `submit_time` DESC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户提交与评测结果表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for tag_group
-- ----------------------------
DROP TABLE IF EXISTS `tag_group`;
CREATE TABLE `tag_group`  (
                          `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                          `type` varchar(32) NOT NULL COMMENT '分组类型，algorithm/source/time/special',
                          `name` varchar(64) NULL DEFAULT NULL COMMENT '分组名称，NULL 表示默认分组',
                          `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                          `is_del` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除，0-未删除，1-已删除',
                          PRIMARY KEY (`id`) USING BTREE,
                          UNIQUE KEY `uk_type_name_del` (`type`, `name`, `is_del`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '标签分组表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for tag
-- ----------------------------
DROP TABLE IF EXISTS `tag`;
CREATE TABLE `tag`  (
                        `id` bigint NOT NULL AUTO_INCREMENT,
                        `tag_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                        `group_id` bigint NOT NULL COMMENT '分组ID，关联 tag_group 表',
                        `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        `is_del` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除，0-未删除，1-已删除',
                        PRIMARY KEY (`id`) USING BTREE,
                        UNIQUE INDEX `uk_tag_name_del`(`tag_name` ASC, `is_del` ASC) USING BTREE,
                        INDEX `idx_tag_group_id`(`group_id` ASC) USING BTREE,
                        CONSTRAINT `fk_tag_group_id` FOREIGN KEY (`group_id`) REFERENCES `tag_group` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '题目标签表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for user_info
-- ----------------------------
DROP TABLE IF EXISTS `user_info`;
CREATE TABLE `user_info`  (
                              `id` bigint NOT NULL AUTO_INCREMENT,
                              `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '登录名',
                              `email` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱',
                              `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '加密密码',
                              `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                              `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                              `is_del` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除，0-未删除，1-已删除',
                              PRIMARY KEY (`id`) USING BTREE,
                              UNIQUE INDEX `uk_email_del`(`email` ASC, `is_del` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户基础表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for user_role
-- ----------------------------
DROP TABLE IF EXISTS `user_role`;
CREATE TABLE `user_role`  (
                              `id` int NOT NULL AUTO_INCREMENT,
                              `role_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ADMIN/USER/STUDENT/TEACHER',
                              `role_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                              `is_del` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除，0-未删除，1-已删除',
                              PRIMARY KEY (`id`) USING BTREE,
                              UNIQUE INDEX `role_code`(`role_code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户角色表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for user_role_rel
-- ----------------------------
DROP TABLE IF EXISTS `user_role_rel`;
CREATE TABLE `user_role_rel`  (
                                  `id` bigint NOT NULL AUTO_INCREMENT,
                                  `user_id` bigint NOT NULL,
                                  `role_id` int NOT NULL,
                                  `is_del` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除，0-未删除，1-已删除',
                                  `active_key` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci GENERATED ALWAYS AS ((case when (`is_del` = 0) then concat(`user_id`,_utf8mb4'#',`role_id`) else NULL end)) STORED NULL,
                                  PRIMARY KEY (`id`) USING BTREE,
                                  UNIQUE INDEX `uk_user_role_rel_active`(`active_key` ASC) USING BTREE,
                                  INDEX `idx_user_role_rel_user_id`(`user_id` ASC) USING BTREE,
                                  INDEX `idx_user_role_rel_role_id`(`role_id` ASC) USING BTREE,
                                  CONSTRAINT `fk_user_role_rel_role` FOREIGN KEY (`role_id`) REFERENCES `user_role` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
                                  CONSTRAINT `fk_user_role_rel_user` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户角色关联表' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;



SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO `problem` (id, pid, title, total_submit, total_accept)
VALUES (1, 'p01', 'a+b', 0, 0),
       (2, 'p02', '数组求和', 0, 0),
       (3, 'p03', '最大子数组和', 0, 0),
       (4, 'p04', '两数之和', 0, 0),
       (5, 'p05', '二分查找', 0, 0),
       (6, 'p06', '合并区间', 0, 0),
       (7, 'p07', '前K大', 0, 0),
       (8, 'p08', '迷宫最短路', 0, 0),
       (9, 'p09', '树的深度优先遍历', 0, 0),
       (10, 'p10', '迪杰斯特拉', 0, 0),
       (11, 'p11', 'Floyd最短路', 0, 0),
       (12, 'p12', '最长公共子序列', 0, 0),
       (13, 'p13', '01背包', 0, 0),
       (14, 'p14', '线段树', 0, 0),
       (15, 'p15', '树状数组', 0, 0),
       (16, 'p16', '并查集', 0, 0),
       (17, 'p17', '拓扑排序', 0, 0),
       (18, 'p18', '强连通分量', 0, 0),
       (19, 'p19', '最短路径', 0, 0),
       (20, 'p20', '字符串匹配', 0, 0),
       (21, 'p21', '回文判断', 0, 0);

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
       (4, '冷门标签', 1, NOW(), NOW(), 0),
       (5, 'NOI', 4, NOW(), NOW(), 0),
       (6, 'NOIP', 4, NOW(), NOW(), 0),
       (7, 'NOI Online', 4, NOW(), NOW(), 0),
       (8, '经典套题一', 5, NOW(), NOW(), 0),
       (9, '经典套题二', 5, NOW(), NOW(), 0),
       (10, '经典套题三', 5, NOW(), NOW(), 0),
       (11, 'ICPC', 6, NOW(), NOW(), 0),
       (12, 'IOI', 6, NOW(), NOW(), 0),
       (13, 'Google Code Jam', 6, NOW(), NOW(), 0),
       (14, '校内赛', 7, NOW(), NOW(), 0),
       (15, '校级选拔赛', 7, NOW(), NOW(), 0),
       (16, '省赛', 7, NOW(), NOW(), 0),
       (17, '2000', 8, NOW(), NOW(), 0),
       (18, '2001', 8, NOW(), NOW(), 0),
       (19, '2002', 8, NOW(), NOW(), 0),
       (20, '2003', 8, NOW(), NOW(), 0),
       (21, '交互题', 9, NOW(), NOW(), 0),
       (22, '提交答案', 9, NOW(), NOW(), 0),
       (23, 'O2优化', 9, NOW(), NOW(), 0);

INSERT INTO `problem_tag_rel` (id, problem_id, tag_id)
VALUES (1, 1, 1),
       (2, 1, 2),
       (3, 2, 1),
       (4, 2, 4),
       (5, 3, 2),
       (6, 3, 4),
       (7, 4, 1),
       (8, 4, 2),
       (9, 5, 1),
       (10, 5, 4),
       (11, 6, 1),
       (12, 6, 3),
       (13, 7, 3),
       (14, 7, 4),
       (15, 8, 3),
       (16, 8, 4),
       (17, 9, 2),
       (18, 9, 4),
       (19, 10, 3),
       (20, 10, 4),
       (21, 11, 3),
       (22, 11, 4),
       (23, 12, 2),
       (24, 12, 4),
       (25, 13, 2),
       (26, 13, 4),
       (27, 14, 3),
       (28, 14, 4),
       (29, 15, 3),
       (30, 15, 4),
       (31, 16, 1),
       (32, 16, 4),
       (33, 17, 3),
       (34, 17, 4),
       (35, 18, 3),
       (36, 18, 4),
       (37, 19, 3),
       (38, 19, 4),
       (39, 20, 1),
       (40, 20, 4),
       (41, 21, 1),
       (42, 21, 4);

INSERT INTO `user_info` (id, username, email, password)
VALUES (1, '123', '1234567891@qq.com', '$2a$10$JOD0yzajuN.zC5a2mUaw6uq05DHOeDka9VFM4UWj4xodHAtlvE1O.');

INSERT INTO `user_role` (id, role_code, role_name, is_del)
VALUES (1, 'USER', 'USER', 0),
       (2, 'ADMIN', 'ADMIN', 0),
       (3, 'SUPER_ADMIN', 'SUPER_ADMIN', 0);

INSERT INTO `user_role_rel` (id, user_id, role_id, is_del)
VALUES (1, 1, 1, 0),
       (2, 1, 2, 0),
       (3, 1, 3, 0);

SET FOREIGN_KEY_CHECKS = 1;
