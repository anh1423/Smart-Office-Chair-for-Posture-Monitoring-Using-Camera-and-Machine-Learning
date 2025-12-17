# 🏥 Posture Monitoring System

AI-powered smart posture monitoring and detection system running on Raspberry Pi 5.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.9-red)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Key Features

### 🎯 Posture Detection
- **AI Detection**: YOLOv8 pose estimation + Sensor fusion
- **4 Detection Modes**: Sensor Only, Camera Only, Auto Smart, Fusion
- **Real-time Monitoring**: Live camera feed & instant alerts
- **8 Posture Types**: Leaning Forward/Left/Right, Leg Crossed, Sitting Upright, Hunched, etc.

### 📊 Analytics & Reporting
- **Advanced Dashboard**: Posture distribution, daily trends, warning frequency
- **AI Performance Metrics**: Camera activation stats, confidence comparison
- **Sensor Visualization**: Real-time radar chart, seat heatmap
- **Data Export**: CSV/JSON export for analysis

### 🔧 System Management
- **Health Monitoring**: CPU, RAM, Temperature, Disk, Battery
- **Database Tools**: Statistics, cleanup, backup/restore
- **User Management**: Role-based access (Admin/User)
- **API Key Management**: Secure API access for IoT devices

### 🌐 Multi-language Support
- **English** / **Vietnamese**
- **Theme Switcher**: Dark / Light mode
- **Responsive Design**: Works on desktop, tablet, mobile

---

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 5 (4GB+ RAM recommended)
- Raspberry Pi OS (64-bit) Bookworm
- Python 3.12 or 3.13
- MariaDB 10.5+

### Installation

```bash
# 1. Clone repository
git clone <repo-url> webserver
cd webserver

# 2. Run installation script
chmod +x install-pi5.sh
./install-pi5.sh

# 3. Setup database
sudo mysql_secure_installation
sudo mysql -u root -p < setup_db.sql

# 4. Configure environment
cp .env.example .env
nano .env  # Edit database credentials

# 5. Start application
source venv/bin/activate
python3 app.py
```

**Access**: `http://<PI_IP>:5000`

**Default Login**: `admin` / `admin123` (⚠️ Change immediately!)

📖 **Details**: See [SETUP.md](SETUP.md) for complete guide

---

## 📁 Project Structure

```
webserver/
├── app.py                    # Main Flask application
├── config.py                 # Configuration
├── requirements-pi5.txt      # Python dependencies
│
├── database/                 # Database layer
│   ├── models.py            # SQLAlchemy models
│   └── db_manager.py        # Database operations
│
├── routes/                   # Flask blueprints
│   ├── auth.py              # Authentication
│   ├── api.py               # Main API
│   ├── admin_analytics.py   # Analytics dashboard
│   ├── system_management.py # System health
│   └── users.py             # User management
│
├── models/                   # AI/ML models
│   ├── sensor_model.py      # Sensor detection
│   ├── camera_model.py      # Camera detection
│   └── fusion_logic.py      # Fusion algorithm
│
├── templates/                # Jinja2 templates
│   ├── base.html
│   ├── dashboard.html
│   ├── analytics.html
│   ├── admin_analytics.html
│   └── admin_system.html
│
└── static/                   # Static assets
    ├── css/style.css
    ├── js/
    │   ├── theme.js         # Theme switcher
    │   ├── language.js      # Language switcher
    │   └── translations.js  # Translation dictionary
    └── images/
```

---

## 🎮 Usage

### Web Interface

| Page | URL | Description |
|------|-----|-------------|
| **Dashboard** | `/dashboard` | Live camera, current posture, alerts |
| **Analytics** | `/analytics` | Today's statistics, posture distribution |
| **Advanced Analytics** | `/admin/analytics` | Charts, trends, AI performance |
| **System Management** | `/admin/system` | System health, database tools |
| **User Management** | `/admin/users` | Add/edit users, roles |
| **API Keys** | `/admin/api-keys` | Manage API keys for IoT |

### API Endpoints

```bash
# Posture Detection
GET  /api/posture/current        # Current status
POST /api/posture/log            # Log detection
GET  /api/posture/history        # Historical data

# Battery Monitoring
POST /api/battery                # Receive from ESP32
GET  /api/battery/latest         # Latest status

# System Health
GET /api/admin/system/health     # System metrics
GET /api/admin/database/stats    # Database stats
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# Database
DB_HOST=localhost
DB_NAME=posture_monitor
DB_USER=posture_user
DB_PASSWORD=your_password

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
DEBUG=False

# Server
HOST=0.0.0.0
PORT=5000
```

### Auto-Start on Boot

```bash
# Copy service file
sudo cp posture_monitor.service /etc/systemd/system/

# Enable and start
sudo systemctl enable posture-monitor
sudo systemctl start posture-monitor

# Check status
sudo systemctl status posture-monitor
```

---

## 🔒 Security

1. **Change default password** immediately after first login
2. **Use strong SECRET_KEY**: `python3 -c "import secrets; print(secrets.token_hex(32))"`
3. **Configure firewall**: `sudo ufw allow 5000/tcp`
4. **Use HTTPS** in production (Nginx + Certbot)
5. **Regular backups**: `mysqldump -u posture_user -p posture_monitor > backup.sql`

---

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Detailed installation guide
- **[NODE_RED_FLOW.md](NODE_RED_FLOW.md)** - MQTT/Node-RED setup
- **[API_KEYS_UI_GUIDE.md](API_KEYS_UI_GUIDE.md)** - API key management
- **[PI5_DEPLOYMENT_GUIDE.md](PI5_DEPLOYMENT_GUIDE.md)** - Deployment guide

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Flask 3.0, SQLAlchemy 2.0, PyMySQL |
| **AI/ML** | PyTorch 2.9, YOLOv8, scikit-learn |
| **Computer Vision** | OpenCV 4.10 |
| **Database** | MariaDB 10.5+ |
| **IoT** | MQTT, Node-RED, ESP32 |
| **Frontend** | Vanilla JS, Chart.js, CSS3 |

---

## 🐛 Troubleshooting

### Common Issues

**Camera not detected**
```bash
vcgencmd get_camera
sudo raspi-config  # Enable camera
```

**Database connection failed**
```bash
sudo systemctl restart mariadb
# Check .env credentials
```

**Out of memory**
```bash
# Increase swap
sudo nano /etc/dphys-swapfile  # CONF_SWAPSIZE=2048
sudo dphys-swapfile setup && sudo dphys-swapfile swapon
```

**View logs**
```bash
sudo journalctl -u posture-monitor -f
```

📖 **More**: See [SETUP.md#troubleshooting](SETUP.md#-troubleshooting)

---

## 🤝 Contributing

```bash
# Fork and clone
git clone <your-fork-url>
cd webserver

# Create branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "Add your feature"

# Push and create PR
git push origin feature/your-feature
```

---

## 📄 License

This project is part of a graduation thesis (DATN - Đồ Án Tốt Nghiệp).

---

## 📞 Support

For issues:
1. Check [Troubleshooting](#-troubleshooting)
2. Review [SETUP.md](SETUP.md)
3. Check logs: `sudo journalctl -u posture-monitor -f`
4. Test database: `python3 test_db_connection.py`

---

## 🎯 Features

- [x] AI-powered posture detection
- [x] Multi-mode detection (Sensor/Camera/Fusion)
- [x] Real-time monitoring & alerts
- [x] Advanced analytics dashboard
- [x] System health monitoring
- [x] User & API key management
- [x] Multi-language support (EN/VI)
- [x] Dark/Light theme
- [x] Mobile responsive design
- [x] Database backup tools
- [x] MQTT/Node-RED integration
- [ ] Mobile app (planned)
- [ ] Cloud backup (planned)
- [ ] Email/SMS notifications (planned)

---

**Version**: 1.0.0  
**Last Updated**: December 2025
**Python**: 3.12+ | 3.13+  
**Platform**: Raspberry Pi 5

**Made with ❤️ for better posture health**
