"""
Configuration file for Posture Monitoring Webserver
Supports both development (Ubuntu) and production (Raspberry Pi 5)
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

# Environment
ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = ENV == 'development'

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))

# Database Configuration (MariaDB)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin')
DB_NAME = os.getenv('DB_NAME', 'posture_monitor')

# SQLAlchemy Database URI
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = DEBUG

# Camera Configuration
CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))  # USB Camera index
CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', 1280))
CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', 720))
CAMERA_FPS = int(os.getenv('CAMERA_FPS', 30))

# Model Paths
# Option 1: Use models from trained_models directory (recommended for production)
TRAINED_MODELS_DIR = BASE_DIR / 'trained_models'
SENSOR_MODEL_PATH = TRAINED_MODELS_DIR / 'sensor' / '9posture_recognition_model.pkl'
SENSOR_ENCODER_PATH = TRAINED_MODELS_DIR / 'sensor' / '9label_encoder.pkl'
CAMERA_MODEL_PATH = TRAINED_MODELS_DIR / 'camera' / 'posture_model_yolo_randomforest.pkl'
CAMERA_ENCODER_PATH = TRAINED_MODELS_DIR / 'camera' / 'label_encoder_yolo_randomforest.pkl'
YOLO_MODEL_PATH = TRAINED_MODELS_DIR / 'camera' / 'yolov8n-pose.pt'

# Option 2: Use models from original training directories (for development)
# Uncomment these lines if you want to use models directly from TrainSensor/TrainCamera
# SENSOR_MODEL_PATH = PROJECT_ROOT / 'TrainSensor' / '9posture_recognition_model.pkl'
# SENSOR_ENCODER_PATH = PROJECT_ROOT / 'TrainSensor' / '9label_encoder.pkl'
# CAMERA_MODEL_PATH = PROJECT_ROOT / 'TrainCamera' / 'yolo_pipeline' / 'posture_model_yolo_randomforest.pkl'
# CAMERA_ENCODER_PATH = PROJECT_ROOT / 'TrainCamera' / 'yolo_pipeline' / 'label_encoder_yolo_randomforest.pkl'
# YOLO_MODEL_PATH = PROJECT_ROOT / 'TrainCamera' / 'yolo_pipeline' / 'yolov8n-pose.pt'

# System Configuration File (JSON)
CONFIG_FILE = BASE_DIR / 'system_config.json'

# Default System Settings
DEFAULT_MODE = 'auto'  # 'sensor_only', 'camera_only', 'auto', 'fusion'
DEFAULT_AUTO_THRESHOLD = 0.70  # Confidence threshold for auto mode
DEFAULT_FUSION_WEIGHTS = {
    'sensor': 0.4,
    'camera': 0.6
}

# Warning Configuration
WARNING_THRESHOLD = 3  # Number of consecutive bad postures before warning
WARNING_TIME_LIMIT = 300  # Seconds (5 minutes) - warn if sitting too long

# MQTT Configuration (for reference, actual MQTT is handled by Node-RED)
MQTT_BROKER = os.getenv('MQTT_BROKER', '192.168.101.192')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER', 'mqttadmin')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'mqttadmin')
MQTT_TOPIC_FSR = 'esp32/fsrsensor'
MQTT_TOPIC_RESULT = 'esp32/recognitionresult'

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = BASE_DIR / 'logs' / 'webserver.log'

# Create logs directory if not exists
LOG_FILE.parent.mkdir(exist_ok=True)

# Posture Labels (must match training data)
POSTURE_LABELS = [
    'Correct_posture',
    'Leaning_backward',
    'Leaning_forward',
    'Leaning_left',
    'Leaning_right',
    'Left_leg_crossed',
    'Right_leg_crossed',
    'Sitting_at_front_edge',
    'Upper_body_hunched'
]

# Bad postures (for warning detection)
BAD_POSTURES = [
    'Leaning_backward',
    'Leaning_forward',
    'Leaning_left',
    'Leaning_right',
    'Left_leg_crossed',
    'Right_leg_crossed',
    'Sitting_at_front_edge',
    'Upper_body_hunched'
]
