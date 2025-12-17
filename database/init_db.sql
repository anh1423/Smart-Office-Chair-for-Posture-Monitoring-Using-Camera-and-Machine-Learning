-- Database initialization script for Posture Monitoring System
-- Compatible with MariaDB on Raspberry Pi 5

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS posture_monitor
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE posture_monitor;

-- Table: posture_logs
-- Stores all posture detection logs
CREATE TABLE IF NOT EXISTS posture_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    posture VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    mode VARCHAR(20) NOT NULL,
    warning_flag BOOLEAN NOT NULL DEFAULT FALSE,
    sensor_values JSON,
    INDEX idx_timestamp (timestamp),
    INDEX idx_posture (posture),
    INDEX idx_warning (warning_flag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: system_config
-- Stores system configuration
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default configuration
INSERT INTO system_config (config_key, config_value) VALUES
    ('mode', 'auto'),
    ('auto_threshold', '0.70'),
    ('fusion_weights', '{"sensor": 0.4, "camera": 0.6}'),
    ('warning_threshold', '3'),
    ('warning_time_limit', '300')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- Table: daily_statistics
-- Pre-aggregated daily statistics for faster queries
CREATE TABLE IF NOT EXISTS daily_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    total_detections INT NOT NULL DEFAULT 0,
    total_warnings INT NOT NULL DEFAULT 0,
    correct_posture_count INT NOT NULL DEFAULT 0,
    bad_posture_count INT NOT NULL DEFAULT 0,
    posture_distribution JSON,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create user for application (optional, adjust as needed)
-- CREATE USER IF NOT EXISTS 'posture_app'@'localhost' IDENTIFIED BY 'your_password_here';
-- GRANT ALL PRIVILEGES ON posture_monitor.* TO 'posture_app'@'localhost';
-- FLUSH PRIVILEGES;

-- Show tables
SHOW TABLES;
