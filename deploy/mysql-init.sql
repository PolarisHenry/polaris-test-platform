-- MySQL 数据库初始化脚本
-- 为 Polaris Test Platform 项目创建数据库和用户权限

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS fastapi_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户并授权（如果不存在）
CREATE USER IF NOT EXISTS 'fastapi_admin'@'%' IDENTIFIED BY 'fastapi_admin_password';
GRANT ALL PRIVILEGES ON fastapi_admin.* TO 'fastapi_admin'@'%';
FLUSH PRIVILEGES;

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;