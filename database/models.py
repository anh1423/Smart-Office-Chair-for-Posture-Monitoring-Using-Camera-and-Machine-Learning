"""
SQLAlchemy Models for Posture Monitoring System
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
import bcrypt

Base = declarative_base()


class User(Base, UserMixin):
    """Model for user authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default='user')  # 'admin' or 'user'
    is_active = Column(Boolean, nullable=False, default=True)  # Account enabled/disabled
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class PostureLog(Base):
    """Model for storing posture detection logs"""
    __tablename__ = 'posture_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    posture = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    mode = Column(String(20), nullable=False)  # 'sensor_only', 'auto', 'fusion'
    warning_flag = Column(Boolean, nullable=False, default=False, index=True)
    sensor_values = Column(JSON, nullable=True)  # Store raw sensor data as JSON
    
    # AI Model Performance fields
    sensor_confidence = Column(Float, nullable=True)  # Sensor model confidence
    camera_confidence = Column(Float, nullable=True)  # Camera model confidence
    camera_activated = Column(Boolean, nullable=True, default=False)  # Was camera used?
    fusion_reason = Column(String(200), nullable=True)  # Why fusion made this decision
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'posture': self.posture,
            'confidence': self.confidence,
            'mode': self.mode,
            'warning_flag': self.warning_flag,
            'sensor_values': self.sensor_values,
            'sensor_confidence': self.sensor_confidence,
            'camera_confidence': self.camera_confidence,
            'camera_activated': self.camera_activated,
            'fusion_reason': self.fusion_reason
        }
    
    def __repr__(self):
        return f"<PostureLog(id={self.id}, posture='{self.posture}', confidence={self.confidence:.2f})>"


class SystemConfig(Base):
    """Model for storing system configuration"""
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.config_key}', value='{self.config_value}')>"


class DailyStatistics(Base):
    """Model for storing pre-aggregated daily statistics"""
    __tablename__ = 'daily_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    total_detections = Column(Integer, nullable=False, default=0)
    total_warnings = Column(Integer, nullable=False, default=0)
    correct_posture_count = Column(Integer, nullable=False, default=0)
    bad_posture_count = Column(Integer, nullable=False, default=0)
    posture_distribution = Column(JSON, nullable=True)  # {'posture_name': count, ...}
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_detections': self.total_detections,
            'total_warnings': self.total_warnings,
            'correct_posture_count': self.correct_posture_count,
            'bad_posture_count': self.bad_posture_count,
            'posture_distribution': self.posture_distribution,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<DailyStatistics(date={self.date}, detections={self.total_detections})>"


class BatteryLog(Base):
    """Battery monitoring log"""
    __tablename__ = 'battery_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    voltage = Column(Float, nullable=False)  # Battery voltage (V)
    status = Column(String(20), nullable=False)  # charging / not charging
    percentage = Column(Float, nullable=False)  # Battery percentage (0-100)
    level = Column(String(20), nullable=False)  # critical / low / medium / high
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'voltage': self.voltage,
            'status': self.status,
            'percentage': self.percentage,
            'level': self.level
        }


class ApiKey(Base):
    """Model for API key authentication"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False, index=True)  # API key (UUID format)
    name = Column(String(100), nullable=False)  # Description/label for the key
    is_active = Column(Boolean, nullable=False, default=True)  # Enable/disable key
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)  # Track last usage
    rate_limit = Column(Integer, nullable=False, default=60)  # Requests per minute
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'key': self.key,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'rate_limit': self.rate_limit
        }
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, name='{self.name}', active={self.is_active})>"
