/*
 Navicat Premium Dump SQL

 Source Server         : blessing_skin
 Source Server Type    : MariaDB
 Source Server Version : 101114 (10.11.14-MariaDB-0+deb12u2)
 Source Host           : 192.168.95.55:3307
 Source Schema         : stupid_db

 Target Server Type    : MariaDB
 Target Server Version : 101114 (10.11.14-MariaDB-0+deb12u2)
 File Encoding         : 65001

 Date: 05/04/2026 16:40:16
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for ai_messages
-- ----------------------------
DROP TABLE IF EXISTS `ai_messages`;
CREATE TABLE `ai_messages`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '消息编号',
  `uid` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'hash_UID(与users表对应)',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '身份ai/user',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '聊天具体文本内容',
  `created_at` datetime NULL DEFAULT current_timestamp() COMMENT '消息产生时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `uid`(`uid` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'LLM对话记忆表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `uid` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'hash_UID',
  `nickname` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '昵称',
  `score` int(11) NULL DEFAULT 0 COMMENT '积分',
  `last_sign_at` datetime NULL DEFAULT NULL COMMENT '上次签到',
  PRIMARY KEY (`uid`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '用户信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Event structure for auto_clean_ai_messages
-- ----------------------------
DROP EVENT IF EXISTS `auto_clean_ai_messages`;
delimiter ;;
CREATE EVENT `auto_clean_ai_messages`
ON SCHEDULE
EVERY '1' DAY STARTS '2026-04-04 16:39:44'
DO -- 这里就是具体的清扫动作，和方法一的代码一模一样
    DELETE FROM `ai_messages` 
    WHERE `created_at` < DATE_SUB(NOW(), INTERVAL 7 DAY)
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
