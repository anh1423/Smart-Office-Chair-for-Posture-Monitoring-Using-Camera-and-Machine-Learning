#!/bin/bash
#
# Setup script for Posture Monitoring Webserver on Raspberry Pi 5
# This script installs dependencies and configures the system
#

set -e  # Exit on error

echo "=========================================="
echo "Posture Monitoring Webserver Setup"
echo "Raspberry Pi 5 Installation Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Please do not run as root. Run as regular user with sudo privileges."
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    mariadb-server \
    libmariadb-dev \
    libopencv-dev \
    python3-opencv \
    git \
    curl

# Install MariaDB if not already installed
echo "🗄️  Configuring MariaDB..."
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Secure MariaDB installation (optional - uncomment if needed)
# sudo mysql_secure_installation

# Create database and user
echo "🗄️  Setting up database..."
sudo mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS posture_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY 'admin';
GRANT ALL PRIVILEGES ON posture_monitor.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;
EOF

# Initialize database schema
echo "🗄️  Initializing database schema..."
mysql -u admin -padmin posture_monitor < database/init_db.sql

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "🐍 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✅ Please edit .env file with your configuration"
fi

# Create logs directory
mkdir -p logs

# Copy systemd service file
echo "⚙️  Installing systemd service..."
sudo cp posture_monitor.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable service (but don't start yet)
sudo systemctl enable posture_monitor.service

echo ""
echo "=========================================="
echo "✅ Installation completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Ensure models are in place:"
echo "   - TrainSensor/9posture_recognition_model.pkl"
echo "   - TrainCamera/yolo_pipeline/posture_model_yolo_randomforest.pkl"
echo "   - TrainCamera/yolo_pipeline/yolov8n-pose.pt"
echo "3. Start the service:"
echo "   sudo systemctl start posture_monitor"
echo "4. Check status:"
echo "   sudo systemctl status posture_monitor"
echo "5. View logs:"
echo "   sudo journalctl -u posture_monitor -f"
echo ""
echo "Web dashboard will be available at:"
echo "http://$(hostname -I | awk '{print $1}'):5000"
echo ""
