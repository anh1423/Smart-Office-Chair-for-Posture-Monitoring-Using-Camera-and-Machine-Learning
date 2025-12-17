# 🚀 Raspberry Pi 5 Deployment Guide

Complete step-by-step guide for deploying the Posture Monitoring System on Raspberry Pi 5.

**Tested on:** Raspberry Pi OS (64-bit) Bookworm, Python 3.12/3.13

---

## 📋 Table of Contents

1. [System Requirements](#-system-requirements)
2. [Pre-Deployment Preparation](#-pre-deployment-preparation)
3. [Installation Steps](#-installation-steps)
4. [Configuration](#-configuration)
5. [Auto-Start Setup](#-auto-start-setup)
6. [Troubleshooting](#-troubleshooting)
7. [Performance Optimization](#-performance-optimization)

---

## 💻 System Requirements

### Hardware
- **Raspberry Pi 5** (4GB RAM minimum, 8GB recommended)
- **MicroSD Card**: 32GB+ (Class 10 or UHS-I)
- **Camera**: Raspberry Pi Camera Module V2/V3 or USB Webcam
- **Power Supply**: Official Pi 5 27W USB-C power adapter
- **Network**: Ethernet (recommended) or WiFi
- **Cooling**: Active cooling recommended for sustained AI workloads

### Software
- **OS**: Raspberry Pi OS (64-bit) Bookworm or later
- **Python**: 3.12 or 3.13 (pre-installed on Bookworm)
- **MariaDB**: 10.5+
- **Node-RED**: Latest (optional, for MQTT/IoT features)

### Network Requirements
- Static IP recommended for production
- Ports: 5000 (web server), 3306 (MariaDB), 1880 (Node-RED)

---

## 📦 Pre-Deployment Preparation

### On Development Machine

#### 1. Create Deployment Package

```bash
cd /path/to/webserver
./prepare_pi5_deploy.sh
```

This creates: `/path/to/DATN/posture-monitor-pi5.tar.gz` (~10MB)

#### 2. Verify Package Contents

```bash
tar -tzf posture-monitor-pi5.tar.gz | head -20
```

Should include:
- `webserver/app.py`
- `webserver/requirements-pi5.txt`
- `webserver/install-pi5.sh`
- `webserver/database/`, `webserver/routes/`, etc.

---

## 🔧 Installation Steps

### Step 1: Prepare Raspberry Pi 5

#### 1.1 Flash OS

```bash
# Use Raspberry Pi Imager
# Select: Raspberry Pi OS (64-bit) - Bookworm
# Configure: hostname, SSH, WiFi (if needed)
```

#### 1.2 First Boot Setup

```bash
# SSH into Pi5
ssh pi@raspberrypi-5.local
# or
ssh pi@<PI_IP_ADDRESS>

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y git vim htop
```

#### 1.3 Set Static IP (Recommended)

```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4
```

Reboot: `sudo reboot`

---

### Step 2: Transfer Deployment Package

#### Option A: SCP (Recommended)

```bash
# From development machine
scp posture-monitor-pi5.tar.gz pi@<PI_IP>:~/
```

#### Option B: USB Drive

```bash
# On Pi5
sudo mkdir /mnt/usb
sudo mount /dev/sda1 /mnt/usb
cp /mnt/usb/posture-monitor-pi5.tar.gz ~/
sudo umount /mnt/usb
```

---

### Step 3: Extract and Install

```bash
# Extract package
cd ~
tar -xzf posture-monitor-pi5.tar.gz
cd webserver

# Run automated installation
./install-pi5.sh
```

**Installation Process** (~15-20 minutes):
1. ✅ Creates virtual environment
2. ✅ Upgrades pip
3. ✅ Installs numpy & OpenCV
4. ✅ Installs PyTorch (CPU-only, ~10 min)
5. ✅ Installs Flask & dependencies
6. ✅ Installs Ultralytics YOLOv8
7. ✅ Installs ML libraries (scikit-learn, joblib, scipy)

**Expected Output:**
```
==========================================
  ✓ Installation Complete!
==========================================

Installed packages:
torch                2.9.1+cpu
torchvision          0.24.1
ultralytics          8.3.x
opencv-python        4.10.0.84
Flask                3.0.0
```

---

### Step 4: Database Setup

#### 4.1 Install MariaDB

```bash
sudo apt install -y mariadb-server mariadb-client
```

#### 4.2 Secure Installation

```bash
sudo mysql_secure_installation
```

Answer prompts:
- Switch to unix_socket authentication? **N**
- Change root password? **Y** (set strong password)
- Remove anonymous users? **Y**
- Disallow root login remotely? **Y**
- Remove test database? **Y**
- Reload privilege tables? **Y**

#### 4.3 Create Database

```bash
sudo mysql -u root -p
```

Execute SQL:
```sql
-- Create database
CREATE DATABASE posture_monitor 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'posture_user'@'localhost' 
  IDENTIFIED BY 'YourSecurePassword123!';

-- Grant privileges
GRANT ALL PRIVILEGES ON posture_monitor.* 
  TO 'posture_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User='posture_user';

EXIT;
```

#### 4.4 Test Connection

```bash
mysql -u posture_user -p posture_monitor
# Enter password
# Should connect successfully
EXIT;
```

---

### Step 5: Application Configuration

#### 5.1 Create Environment File

```bash
cd ~/webserver
nano .env
```

#### 5.2 Add Configuration

```env
# ==================== DATABASE ====================
DB_HOST=localhost
DB_PORT=3306
DB_NAME=posture_monitor
DB_USER=posture_user
DB_PASSWORD=YourSecurePassword123!

# ==================== FLASK ====================
SECRET_KEY=your-random-secret-key-change-this-in-production
FLASK_ENV=production
DEBUG=False

# ==================== SERVER ====================
HOST=0.0.0.0
PORT=5000

# ==================== CAMERA ====================
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=30

# ==================== AI MODEL ====================
MODEL_PATH=models/yolov8n-pose.pt
CONFIDENCE_THRESHOLD=0.5

# ==================== LOGGING ====================
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

**Generate Secret Key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### 5.3 Set Permissions

```bash
chmod 600 .env
```

---

### Step 6: Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database tables
python3 -c "from database import DBManager; db = DBManager(); print('✓ Database initialized')"
```

**Expected Output:**
```
✓ Database initialized
```

---

### Step 7: Test Run

```bash
# Ensure venv is activated
source venv/bin/activate

# Start application
python3 app.py
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.100:5000
```

#### 7.1 Access Web Interface

Open browser: `http://<PI_IP>:5000`

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT**: Change password immediately after first login!

#### 7.2 Verify Features

- [ ] Dashboard loads
- [ ] Camera feed works (if camera connected)
- [ ] Analytics page displays
- [ ] System Management shows metrics
- [ ] Can create new user

---

## 🔄 Auto-Start Setup

### Create Systemd Service

#### 1. Create Service File

```bash
sudo nano /etc/systemd/system/posture-monitor.service
```

#### 2. Add Configuration

```ini
[Unit]
Description=Posture Monitoring System
Documentation=https://github.com/your-repo
After=network-online.target mariadb.service
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/webserver
Environment="PATH=/home/pi/webserver/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/pi/webserver/venv/bin/python3 /home/pi/webserver/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=posture-monitor

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

#### 3. Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable posture-monitor

# Start service
sudo systemctl start posture-monitor

# Check status
sudo systemctl status posture-monitor
```

**Expected Status:**
```
● posture-monitor.service - Posture Monitoring System
     Loaded: loaded (/etc/systemd/system/posture-monitor.service; enabled)
     Active: active (running) since Mon 2024-12-09 18:00:00 +07
```

#### 4. View Logs

```bash
# Follow logs in real-time
sudo journalctl -u posture-monitor -f

# View last 100 lines
sudo journalctl -u posture-monitor -n 100

# View logs since boot
sudo journalctl -u posture-monitor -b
```

#### 5. Service Management

```bash
# Restart service
sudo systemctl restart posture-monitor

# Stop service
sudo systemctl stop posture-monitor

# Disable auto-start
sudo systemctl disable posture-monitor
```

---

## 🔒 Security Configuration

### 1. Firewall Setup

```bash
# Install UFW
sudo apt install -y ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp comment 'SSH'

# Allow web server
sudo ufw allow 5000/tcp comment 'Posture Monitor'

# Allow Node-RED (if using)
sudo ufw allow 1880/tcp comment 'Node-RED'

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### 2. Change Default Passwords

#### Application Admin
1. Login to web interface
2. Go to **Users** → **Edit admin**
3. Set strong password
4. Save changes

#### Database Root
```bash
sudo mysql -u root -p
ALTER USER 'root'@'localhost' IDENTIFIED BY 'NewStrongPassword123!';
FLUSH PRIVILEGES;
EXIT;
```

#### Pi User
```bash
passwd
# Enter new password
```

### 3. SSH Hardening (Optional)

```bash
sudo nano /etc/ssh/sshd_config
```

Recommended changes:
```
PermitRootLogin no
PasswordAuthentication yes  # or 'no' if using SSH keys
PubkeyAuthentication yes
Port 22  # or change to non-standard port
```

Restart SSH:
```bash
sudo systemctl restart ssh
```

---

## ⚡ Performance Optimization

### 1. GPU Memory Allocation

```bash
sudo raspi-config
```

Navigate: **Performance Options** → **GPU Memory** → Set to **256MB**

### 2. Reduce Camera Resolution

Edit `.env`:
```env
CAMERA_WIDTH=320
CAMERA_HEIGHT=240
CAMERA_FPS=15
```

### 3. Use Lighter YOLO Model

In `app.py`, change:
```python
# From:
model = YOLO('yolov8n-pose.pt')

# To (lighter):
model = YOLO('yolov8n-pose.pt', task='pose')  # Already using nano
```

### 4. Increase Swap Size

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
```

Change:
```
CONF_SWAPSIZE=2048
```

Apply:
```bash
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 5. Disable Unnecessary Services

```bash
# Check running services
systemctl list-units --type=service --state=running

# Disable unused services (example)
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
```

---

## 🐛 Troubleshooting

### Issue: Camera Not Detected

**Symptoms:**
```
Error: Camera not found
```

**Solutions:**
```bash
# Check camera
vcgencmd get_camera

# Enable camera
sudo raspi-config
# Interface Options → Camera → Enable

# Reboot
sudo reboot

# Test camera
libcamera-hello
```

### Issue: Database Connection Failed

**Symptoms:**
```
sqlalchemy.exc.OperationalError: Can't connect to MySQL server
```

**Solutions:**
```bash
# Check MariaDB status
sudo systemctl status mariadb

# Restart MariaDB
sudo systemctl restart mariadb

# Verify credentials in .env
cat .env | grep DB_

# Test connection
mysql -u posture_user -p posture_monitor
```

### Issue: High CPU Usage

**Symptoms:**
- CPU at 100%
- System slow/unresponsive

**Solutions:**
1. Reduce camera FPS (see Performance Optimization)
2. Lower camera resolution
3. Check for runaway processes:
```bash
htop
# Press F5 to sort by CPU
```

### Issue: Out of Memory

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solutions:**
1. Increase swap size (see Performance Optimization)
2. Reduce batch size in AI model
3. Close unnecessary applications

### Issue: Service Won't Start

**Symptoms:**
```
systemctl status posture-monitor
● posture-monitor.service - failed
```

**Solutions:**
```bash
# Check detailed logs
sudo journalctl -u posture-monitor -n 50 --no-pager

# Common fixes:
# 1. Check file permissions
ls -la /home/pi/webserver/app.py

# 2. Verify venv path
ls -la /home/pi/webserver/venv/bin/python3

# 3. Test manual start
cd /home/pi/webserver
source venv/bin/activate
python3 app.py
```

---

## 📊 Monitoring & Maintenance

### System Health Checks

```bash
# CPU temperature
vcgencmd measure_temp

# Memory usage
free -h

# Disk space
df -h

# Service status
sudo systemctl status posture-monitor mariadb
```

### Database Maintenance

#### Backup
```bash
# Create backup
mysqldump -u posture_user -p posture_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_*.sql
```

#### Restore
```bash
# Restore from backup
gunzip backup_20241209_180000.sql.gz
mysql -u posture_user -p posture_monitor < backup_20241209_180000.sql
```

#### Cleanup Old Data
Use web interface: **System Management** → **Data Management** → **Clear Old Logs**

### Application Updates

```bash
cd ~/webserver

# Pull latest changes (if using git)
git pull

# Activate venv
source venv/bin/activate

# Update dependencies
pip install -r requirements-pi5.txt --upgrade

# Restart service
sudo systemctl restart posture-monitor
```

---

## 📝 Post-Deployment Checklist

- [ ] Application accessible via web browser
- [ ] Admin password changed
- [ ] Database credentials secured
- [ ] Firewall configured
- [ ] Auto-start service enabled
- [ ] Camera working (if applicable)
- [ ] System health metrics displaying
- [ ] Battery monitoring active (if using ESP32)
- [ ] Backup strategy in place
- [ ] Monitoring/alerting configured

---

## 🎯 Next Steps

1. **Configure Node-RED** (optional)
   - See [NODE_RED_FLOW.md](NODE_RED_FLOW.md)
   - Setup MQTT for ESP32 integration

2. **Setup HTTPS** (production)
   ```bash
   sudo apt install -y nginx certbot python3-certbot-nginx
   # Configure reverse proxy
   ```

3. **Configure Email Alerts** (optional)
   - Setup SMTP in application
   - Configure alert thresholds

4. **Mobile Access**
   - Port forwarding (if needed)
   - Dynamic DNS setup

---

## 📞 Support

**Logs Location:**
- Application: `sudo journalctl -u posture-monitor -f`
- System: `/var/log/syslog`
- Database: `/var/log/mysql/error.log`

**Common Commands:**
```bash
# Service status
sudo systemctl status posture-monitor

# Restart service
sudo systemctl restart posture-monitor

# View logs
sudo journalctl -u posture-monitor -f

# Check database
mysql -u posture_user -p posture_monitor
```

---

**Deployment Complete! 🎉**

Your Posture Monitoring System is now running on Raspberry Pi 5.

Access: `http://<PI_IP>:5000`
