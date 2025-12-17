#!/bin/bash
#
# Script chạy trên Pi5 để setup database cho remote access
# Chạy: ssh pi@192.168.101.192 'bash -s' < setup_db_on_pi5.sh
#

echo "=========================================="
echo "Setting up MariaDB on Pi5"
echo "=========================================="
echo ""

# Create database and grant permissions
echo "Creating database and user..."
sudo mysql -u root <<EOF
-- Create database
CREATE DATABASE IF NOT EXISTS posture_monitor 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Create or update user with remote access
CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED BY 'admin';
CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY 'admin';
CREATE USER IF NOT EXISTS 'admin'@'192.168.101.%' IDENTIFIED BY 'admin';

-- Grant all privileges
GRANT ALL PRIVILEGES ON posture_monitor.* TO 'admin'@'%';
GRANT ALL PRIVILEGES ON posture_monitor.* TO 'admin'@'localhost';
GRANT ALL PRIVILEGES ON posture_monitor.* TO 'admin'@'192.168.101.%';

-- Flush privileges
FLUSH PRIVILEGES;

-- Show users
SELECT User, Host FROM mysql.user WHERE User='admin';

-- Show databases
SHOW DATABASES;

EXIT
EOF

echo ""
echo "✅ Database and user created"
echo ""

# Configure bind-address
echo "Configuring MariaDB for remote access..."
sudo sed -i 's/^bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mariadb.conf.d/50-server.cnf

echo "✅ bind-address configured"
echo ""

# Restart MariaDB
echo "Restarting MariaDB..."
sudo systemctl restart mariadb

echo "✅ MariaDB restarted"
echo ""

# Check status
echo "Checking MariaDB status..."
sudo systemctl status mariadb --no-pager | head -10

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "MariaDB is now configured for remote access"
echo "Database: posture_monitor"
echo "User: admin@% (from any host)"
echo "Password: admin"
echo ""
