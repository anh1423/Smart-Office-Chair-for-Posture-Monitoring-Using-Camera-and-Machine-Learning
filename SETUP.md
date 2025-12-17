# 🚀 Setup Guide - Posture Monitoring System

## 📋 System Requirements

### Hardware
- **Raspberry Pi 5** (4GB+ RAM recommended)
- **Camera** USB or Pi Camera Module
- **SD Card** 32GB or larger
- **ESP32** (for battery monitoring - optional)
- **7 pressure sensors** (optional)

### Software
- **OS**: Raspberry Pi OS (64-bit) Bookworm
- **Python**: 3.12 or 3.13
- **Database**: MariaDB 10.5+
- **Node-RED**: (optional, for MQTT integration)

---

## 📦 Quick Installation (5 Steps)

### Step 1: Prepare Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git python3-pip python3-venv mariadb-server
```

### Step 2: Clone Project

```bash
cd ~
git clone <repository-url> webserver
cd webserver
```

### Step 3: Install Dependencies

```bash
# Run automated installation script
chmod +x install-pi5.sh
./install-pi5.sh
```

The script will automatically:
- Create virtual environment
- Install all Python packages
- Install PyTorch, OpenCV, YOLOv8
- Time: ~15-20 minutes

### Step 4: Configure Database

```bash
# Secure MariaDB
sudo mysql_secure_installation
```

Answer the prompts:
- Set root password? **Y** → Enter strong password
- Remove anonymous users? **Y**
- Disallow root login remotely? **Y**
- Remove test database? **Y**
- Reload privilege tables? **Y**

```bash
# Create database and user
sudo mysql -u root -p
```

Run these SQL commands:

```sql
CREATE DATABASE posture_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'posture_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON posture_monitor.* TO 'posture_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 5: Configure Application

```bash
# Create .env file
nano .env
```

Add this configuration:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=posture_monitor
DB_USER=posture_user
DB_PASSWORD=your_secure_password

# Flask Configuration
SECRET_KEY=change-this-to-a-random-secret-key-min-32-characters
FLASK_ENV=production
DEBUG=False

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Camera Configuration (optional)
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
```

**Generate random SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🎯 Running the Application

### Manual Start

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python3 app.py
```

Access: `http://<PI_IP>:5000`

**Default Login:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT**: Change password immediately after first login!

### Auto-Start (Systemd Service)

```bash
# Copy service file
sudo cp posture_monitor.service /etc/systemd/system/

# Edit paths if needed
sudo nano /etc/systemd/system/posture_monitor.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable posture-monitor
sudo systemctl start posture-monitor

# Check status
sudo systemctl status posture-monitor
```

**Service management:**
```bash
sudo systemctl stop posture-monitor     # Stop
sudo systemctl restart posture-monitor  # Restart
sudo systemctl status posture-monitor   # Check status
sudo journalctl -u posture-monitor -f   # View logs
```

---

## 🔧 Advanced Configuration

### 1. Camera Configuration

```bash
# Check camera
vcgencmd get_camera

# If not enabled
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot
```

### 2. Increase Swap (If RAM < 4GB)

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Edit: CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 3. Configure Firewall

```bash
sudo apt install -y ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5000/tcp  # Web server
sudo ufw enable
```

### 4. Install Node-RED (Optional)

```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)

# Start Node-RED
node-red-start

# Auto-start on boot
sudo systemctl enable nodered
```

See details: [NODE_RED_FLOW.md](NODE_RED_FLOW.md)

---

## 🔐 Security

### 1. Change Admin Password

1. Login with `admin/admin123`
2. Go to **Users** → Click **Edit** on admin user
3. Enter new password (minimum 8 characters)
4. Click **Save**

### 2. Create New User

```bash
# Or use script
python3 create_admin.py
```

### 3. Use HTTPS (Production)

```bash
# Install Nginx + Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Configure Nginx reverse proxy
sudo nano /etc/nginx/sites-available/posture-monitor
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/posture-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## 🧪 Testing Installation

### Test Database Connection

```bash
python3 test_db_connection.py
```

Expected output:
```
✅ Database connection successful
✅ Tables created successfully
```

### Test Camera

```bash
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Error')"
```

### Test Web Server

```bash
curl http://localhost:5000
```

---

## 📊 Backup & Restore

### Backup Database

```bash
# Create backup
mysqldump -u posture_user -p posture_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_*.sql
```

### Restore Database

```bash
# Decompress (if needed)
gunzip backup_20241217_120000.sql.gz

# Restore
mysql -u posture_user -p posture_monitor < backup_20241217_120000.sql
```

### Backup Entire Project

```bash
cd ~
tar -czf webserver_backup_$(date +%Y%m%d).tar.gz webserver/
```

---

## 🐛 Troubleshooting

### Error: "Camera not found"

```bash
# Check camera
ls /dev/video*
vcgencmd get_camera

# Enable camera
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot
```

### Error: "Database connection failed"

```bash
# Check MariaDB
sudo systemctl status mariadb
sudo systemctl restart mariadb

# Check credentials in .env
cat .env | grep DB_

# Test connection
mysql -u posture_user -p posture_monitor
```

### Error: "Port 5000 already in use"

```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>
```

### Error: "Out of memory"

```bash
# Increase swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Reduce camera resolution in .env
CAMERA_WIDTH=320
CAMERA_HEIGHT=240
```

### Error: "Permission denied"

```bash
# Fix permissions
sudo chown -R pi:pi ~/webserver
chmod +x ~/webserver/*.sh
```

---

## 📝 Logs & Monitoring

### View Application Logs

```bash
# If running with systemd
sudo journalctl -u posture-monitor -f

# If running manually
tail -f logs/app.log
```

### View System Logs

```bash
tail -f /var/log/syslog
```

### Monitor System Resources

```bash
# CPU, RAM, Disk
htop

# Temperature
vcgencmd measure_temp
```

---

## 🔄 Updating Application

```bash
cd ~/webserver

# Pull latest code
git pull

# Activate venv
source venv/bin/activate

# Update dependencies
pip install -r requirements-pi5.txt --upgrade

# Restart service
sudo systemctl restart posture-monitor
```

---

## ✅ Completion Checklist

- [ ] Raspberry Pi OS installed and updated
- [ ] Python 3.12+ installed
- [ ] MariaDB installed and configured
- [ ] Project cloned and dependencies installed
- [ ] .env file created with correct information
- [ ] Database created and connection tested
- [ ] Camera enabled and tested
- [ ] Application running on port 5000
- [ ] Admin password changed
- [ ] Systemd service configured (optional)
- [ ] Firewall configured (recommended)
- [ ] Database backup/restore tested

---

## 📞 Support

If you encounter issues:

1. Check [Troubleshooting](#-troubleshooting)
2. View logs: `sudo journalctl -u posture-monitor -f`
3. Test database connection: `python3 test_db_connection.py`
4. Test camera: `vcgencmd get_camera`

---

**Happy installing! 🎉**
