# ⚡ Quick Reference - Posture Monitor

Essential commands and configurations for daily operations.

---

## 🚀 Quick Start

```bash
# Start application
cd ~/webserver
source venv/bin/activate
python3 app.py
```

Access: `http://<PI_IP>:5000`  
Login: `admin` / `admin123`

---

## 🔧 Service Management

```bash
# Start
sudo systemctl start posture-monitor

# Stop
sudo systemctl stop posture-monitor

# Restart
sudo systemctl restart posture-monitor

# Status
sudo systemctl status posture-monitor

# View logs
sudo journalctl -u posture-monitor -f
```

---

## 💾 Database

### Quick Access
```bash
mysql -u posture_user -p posture_monitor
```

### Backup
```bash
mysqldump -u posture_user -p posture_monitor > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
mysql -u posture_user -p posture_monitor < backup_20241209.sql
```

---

## 📊 System Monitoring

```bash
# CPU temp
vcgencmd measure_temp

# Memory
free -h

# Disk space
df -h

# Top processes
htop
```

---

## 🔍 Troubleshooting

### Camera Issues
```bash
vcgencmd get_camera
sudo raspi-config  # Enable camera
libcamera-hello    # Test camera
```

### Database Issues
```bash
sudo systemctl status mariadb
sudo systemctl restart mariadb
```

### High CPU
- Lower camera FPS in `.env`
- Reduce resolution
- Check `htop`

### View Logs
```bash
# Application
sudo journalctl -u posture-monitor -n 100

# System
tail -f /var/log/syslog

# Database
sudo tail -f /var/log/mysql/error.log
```

---

## 📁 Important Files

| File | Location | Purpose |
|------|----------|---------|
| Main app | `/home/pi/webserver/app.py` | Flask application |
| Config | `/home/pi/webserver/.env` | Environment variables |
| Service | `/etc/systemd/system/posture-monitor.service` | Systemd service |
| Logs | `sudo journalctl -u posture-monitor` | Application logs |
| Database | `mysql -u posture_user -p` | MariaDB access |

---

## 🌐 Web Interface

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/dashboard` | Main dashboard |
| Analytics | `/admin/analytics` | Analytics & charts |
| System | `/admin/system` | System health & data mgmt |
| Users | `/admin/users` | User management |

---

## 🔑 Default Credentials

**Web Interface:**
- Username: `admin`
- Password: `admin123` ⚠️ Change immediately!

**Database:**
- User: `posture_user`
- Password: Set during installation

---

## 📞 Quick Help

**Can't access web interface?**
```bash
sudo systemctl status posture-monitor
sudo journalctl -u posture-monitor -n 50
```

**Database connection error?**
```bash
sudo systemctl restart mariadb
mysql -u posture_user -p posture_monitor
```

**Camera not working?**
```bash
vcgencmd get_camera
sudo raspi-config  # Enable camera
sudo reboot
```

---

## 🔄 Update Application

```bash
cd ~/webserver
git pull
source venv/bin/activate
pip install -r requirements-pi5.txt --upgrade
sudo systemctl restart posture-monitor
```

---

**For detailed instructions, see:**
- [README.md](README.md) - Full documentation
- [PI5_DEPLOYMENT_GUIDE.md](PI5_DEPLOYMENT_GUIDE.md) - Deployment guide
