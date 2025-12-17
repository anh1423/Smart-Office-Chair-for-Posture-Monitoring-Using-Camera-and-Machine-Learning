"""
Database Manager for Posture Monitoring System
Handles all database operations using SQLAlchemy
"""
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
import logging

from database.models import Base, PostureLog, SystemConfig, DailyStatistics, ApiKey
import config

logger = logging.getLogger(__name__)


class DBManager:
    """Database manager class for handling all DB operations"""
    
    def __init__(self, database_uri: str = None):
        """
        Initialize database manager
        
        Args:
            database_uri: SQLAlchemy database URI (defaults to config.SQLALCHEMY_DATABASE_URI)
        """
        self.database_uri = database_uri or config.SQLALCHEMY_DATABASE_URI
        self.engine = None
        self.Session = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(
                self.database_uri,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=config.SQLALCHEMY_ECHO
            )
            
            # Create session factory
            session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(session_factory)
            
            # Create all tables
            Base.metadata.create_all(self.engine)
            
            logger.info("Database initialized successfully")
        except SQLAlchemyError as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def close_session(self, session):
        """Close a database session"""
        if session:
            session.close()
    
    # ==================== PostureLog Operations ====================
    
    def insert_posture_log(self, posture: str, confidence: float, mode: str,
                          warning_flag: bool, sensor_values: Dict = None,
                          sensor_confidence: float = None, camera_confidence: float = None,
                          camera_activated: bool = None, fusion_reason: str = None) -> Optional[PostureLog]:
        """
        Insert a new posture log entry
        
        Args:
            posture: Detected posture label
            confidence: Confidence score (0-1)
            mode: Detection mode ('sensor_only', 'auto', 'fusion')
            warning_flag: Whether this is a warning posture
            sensor_values: Raw sensor data (dict)
        
        Returns:
            PostureLog object if successful, None otherwise
        """
        session = self.get_session()
        try:
            log = PostureLog(
                posture=posture,
                confidence=confidence,
                mode=mode,
                warning_flag=warning_flag,
                sensor_values=sensor_values,
                sensor_confidence=sensor_confidence,
                camera_confidence=camera_confidence,
                camera_activated=camera_activated,
                fusion_reason=fusion_reason
            )
            session.add(log)
            session.commit()
            
            # Update daily statistics
            self._update_daily_statistics(session, log)
            session.commit()
            
            logger.info(f"Inserted posture log: {posture} (confidence: {confidence:.2f})")
            return log
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to insert posture log: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_posture_logs(self, start_date: datetime = None, end_date: datetime = None, 
                        limit: int = 100) -> List[PostureLog]:
        """
        Get posture logs within date range
        
        Args:
            start_date: Start datetime (inclusive)
            end_date: End datetime (inclusive)
            limit: Maximum number of records to return
        
        Returns:
            List of PostureLog objects
        """
        session = self.get_session()
        try:
            query = session.query(PostureLog)
            
            if start_date:
                query = query.filter(PostureLog.timestamp >= start_date)
            if end_date:
                query = query.filter(PostureLog.timestamp <= end_date)
            
            logs = query.order_by(PostureLog.timestamp.desc()).limit(limit).all()
            return logs
        except SQLAlchemyError as e:
            logger.error(f"Failed to get posture logs: {e}")
            return []
        finally:
            self.close_session(session)
    
    def _update_daily_statistics(self, session, log: PostureLog):
        """Update daily statistics based on new log entry"""
        try:
            today = log.timestamp.date()
            
            # Get or create daily stats
            stats = session.query(DailyStatistics).filter_by(date=today).first()
            if not stats:
                stats = DailyStatistics(
                    date=today,
                    total_detections=0,
                    total_warnings=0,
                    correct_posture_count=0,
                    bad_posture_count=0,
                    posture_distribution={}
                )
                session.add(stats)
            
            # Rebuild from database (single query, optimized)
            all_logs_today = session.query(PostureLog).filter(
                func.date(PostureLog.timestamp) == today
            ).all()
            
            # Recalculate all statistics
            stats.total_detections = len(all_logs_today)
            stats.total_warnings = sum(1 for l in all_logs_today if l.warning_flag)
            stats.correct_posture_count = sum(1 for l in all_logs_today if l.posture == 'Sitting_upright')
            stats.bad_posture_count = sum(1 for l in all_logs_today if l.posture != 'Sitting_upright')
            
            # Rebuild posture distribution from all logs
            from collections import Counter
            posture_counts = Counter(l.posture for l in all_logs_today)
            stats.posture_distribution = dict(posture_counts)
            
        except Exception as e:
            logger.error(f"Failed to update daily statistics: {e}")
    
    # ==================== SystemConfig Operations ====================
    
    def get_config(self, key: str) -> Optional[str]:
        """
        Get configuration value by key
        
        Args:
            key: Configuration key
        
        Returns:
            Configuration value as string, or None if not found
        """
        session = self.get_session()
        try:
            config_obj = session.query(SystemConfig).filter_by(config_key=key).first()
            return config_obj.config_value if config_obj else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get config '{key}': {e}")
            return None
        finally:
            self.close_session(session)
    
    def set_config(self, key: str, value: str) -> bool:
        """
        Set configuration value
        
        Args:
            key: Configuration key
            value: Configuration value (will be converted to string)
        
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            config_obj = session.query(SystemConfig).filter_by(config_key=key).first()
            
            if config_obj:
                config_obj.config_value = str(value)
            else:
                config_obj = SystemConfig(config_key=key, config_value=str(value))
                session.add(config_obj)
            
            session.commit()
            logger.info(f"Set config '{key}' = '{value}'")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to set config '{key}': {e}")
            return False
        finally:
            self.close_session(session)
    
    def get_all_configs(self) -> Dict[str, str]:
        """
        Get all configuration key-value pairs
        
        Returns:
            Dictionary of all configs
        """
        session = self.get_session()
        try:
            configs = session.query(SystemConfig).all()
            return {c.config_key: c.config_value for c in configs}
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all configs: {e}")
            return {}
        finally:
            self.close_session(session)
    
    # ==================== Statistics Operations ====================
    
    def get_daily_statistics(self, target_date: date = None) -> Optional[DailyStatistics]:
        """
        Get statistics for a specific date
        
        Args:
            target_date: Target date (defaults to today)
        
        Returns:
            DailyStatistics object or None
        """
        if target_date is None:
            target_date = date.today()
        
        session = self.get_session()
        try:
            stats = session.query(DailyStatistics).filter_by(date=target_date).first()
            return stats
        except SQLAlchemyError as e:
            logger.error(f"Failed to get daily statistics: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_statistics_range(self, start_date: date, end_date: date) -> List[DailyStatistics]:
        """
        Get statistics for a date range
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        
        Returns:
            List of DailyStatistics objects
        """
        session = self.get_session()
        try:
            stats = session.query(DailyStatistics).filter(
                and_(
                    DailyStatistics.date >= start_date,
                    DailyStatistics.date <= end_date
                )
            ).order_by(DailyStatistics.date).all()
            return stats
        except SQLAlchemyError as e:
            logger.error(f"Failed to get statistics range: {e}")
            return []
        finally:
            self.close_session(session)
    
    def get_posture_summary(self, target_date: date = None) -> Dict:
        """
        Get posture summary for a specific date
        
        Args:
            target_date: Target date (defaults to today)
        
        Returns:
            Dictionary with summary statistics
        """
        stats = self.get_daily_statistics(target_date)
        
        if not stats:
            return {
                'date': (target_date or date.today()).isoformat(),
                'total_detections': 0,
                'total_warnings': 0,
                'correct_posture_count': 0,
                'bad_posture_count': 0,
                'correct_percentage': 0.0,
                'posture_distribution': {}
            }
        
        total = stats.total_detections or 1  # Avoid division by zero
        correct_pct = (stats.correct_posture_count / total) * 100
        
        return {
            'date': stats.date.isoformat(),
            'total_detections': stats.total_detections,
            'total_warnings': stats.total_warnings,
            'correct_posture_count': stats.correct_posture_count,
            'bad_posture_count': stats.bad_posture_count,
            'correct_percentage': round(correct_pct, 2),
            'posture_distribution': stats.posture_distribution or {}
        }
    
    def close(self):
        """Close database connection"""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connection closed")

    # ==================== User Operations ====================
    
    def create_user(self, username: str, password: str, email: str = None):
        """Create a new user"""
        from database.models import User
        
        session = self.get_session()
        try:
            existing = session.query(User).filter_by(username=username).first()
            if existing:
                logger.warning(f"User '{username}' already exists")
                return None
            
            user = User(username=username, email=email)
            user.set_password(password)
            session.add(user)
            session.commit()
            
            logger.info(f"Created user: {username}")
            return user
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to create user: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_user_by_username(self, username: str):
        """Get user by username"""
        from database.models import User
        
        session = self.get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_user_by_id(self, user_id: int):
        """Get user by ID"""
        from database.models import User
        
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user: {e}")
            return None
        finally:
            self.close_session(session)
    
    def create_default_admin(self) -> bool:
        """Create default admin user if not exists"""
        try:
            existing = self.get_user_by_username('admin')
            if existing:
                logger.info("Admin user already exists")
                return True
            
            admin = self.create_user('admin', 'admin123', 'admin@postureperfect.local')
            if admin:
                logger.info("Default admin user created successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to create default admin: {e}")
            return False

    # ==================== User Management Operations ====================
    
    def get_all_users(self):
        """Get all users"""
        session = self.get_session()
        try:
            from database.models import User
            users = session.query(User).all()
            return [user.to_dict() for user in users]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all users: {e}")
            return []
        finally:
            self.close_session(session)
    
    def update_user_status(self, user_id: int, is_active: bool) -> bool:
        """Enable or disable user account"""
        session = self.get_session()
        try:
            from database.models import User
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.warning(f"User {user_id} not found")
                return False
            
            user.is_active = is_active
            session.commit()
            logger.info(f"User {user.username} status updated to {'active' if is_active else 'inactive'}")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to update user status: {e}")
            return False
        finally:
            self.close_session(session)
    
    def update_user_role(self, user_id: int, role: str) -> bool:
        """Update user role"""
        session = self.get_session()
        try:
            from database.models import User
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.warning(f"User {user_id} not found")
                return False
            
            user.role = role
            session.commit()
            logger.info(f"User {user.username} role updated to {role}")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to update user role: {e}")
            return False
        finally:
            self.close_session(session)
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user account"""
        session = self.get_session()
        try:
            from database.models import User
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.warning(f"User {user_id} not found")
                return False
            
            username = user.username
            session.delete(user)
            session.commit()
            logger.info(f"User {username} deleted")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to delete user: {e}")
            return False
        finally:
            self.close_session(session)
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        session = self.get_session()
        try:
            from database.models import User
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.warning(f"User {user_id} not found")
                return False
            
            user.set_password(new_password)
            session.commit()
            logger.info(f"Password updated for user {user.username}")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to update password: {e}")
            return False
        finally:
            self.close_session(session)

    # ==================== Advanced Analytics Operations ====================
    
    def get_logs_by_date_range(self, start_date, end_date):
        """Get posture logs within date range"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime
            
            # Convert to datetime if strings
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date
            ).order_by(PostureLog.timestamp.asc()).all()
            
            return [log.to_dict() for log in logs]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get logs by date range: {e}")
            return []
        finally:
            self.close_session(session)
    
    def get_statistics_by_date_range(self, start_date, end_date):
        """Get aggregated statistics for date range"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime
            from collections import Counter
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date
            ).all()
            
            if not logs:
                return {
                    'total_detections': 0,
                    'correct_posture_count': 0,
                    'bad_posture_count': 0,
                    'total_warnings': 0,
                    'correct_percentage': 0,
                    'posture_distribution': {},
                    'mode_distribution': {}
                }
            
            # Calculate statistics
            total = len(logs)
            correct = sum(1 for l in logs if l.posture == 'Sitting_upright')
            warnings = sum(1 for l in logs if l.warning_flag)
            
            posture_counts = Counter(l.posture for l in logs)
            mode_counts = Counter(l.mode for l in logs)
            
            return {
                'total_detections': total,
                'correct_posture_count': correct,
                'bad_posture_count': total - correct,
                'total_warnings': warnings,
                'correct_percentage': round((correct / total * 100), 1) if total > 0 else 0,
                'posture_distribution': dict(posture_counts),
                'mode_distribution': dict(mode_counts)
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
        finally:
            self.close_session(session)
    
    def get_daily_trend(self, start_date, end_date):
        """Get daily posture counts for trend chart"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime, timedelta
            from collections import defaultdict
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date
            ).all()
            
            # Check if single day - if so, group by hour instead
            days_diff = (end_date - start_date).days
            is_single_day = days_diff <= 1
            
            if is_single_day:
                # Group by hour for single day
                hourly_data = defaultdict(lambda: {'correct': 0, 'bad': 0, 'total': 0})
                
                for log in logs:
                    # Convert UTC to local time (UTC+7)
                    local_time = log.timestamp + timedelta(hours=7)
                    hour_key = local_time.strftime('%Y-%m-%d %H:00')
                    hourly_data[hour_key]['total'] += 1
                    if log.posture == 'Sitting_upright':
                        hourly_data[hour_key]['correct'] += 1
                    else:
                        hourly_data[hour_key]['bad'] += 1
                
                # Create result for 24 hours
                result = []
                current_hour = (start_date + timedelta(hours=7)).replace(minute=0, second=0, microsecond=0)
                end_hour = (end_date + timedelta(hours=7)).replace(minute=0, second=0, microsecond=0)
                
                while current_hour <= end_hour:
                    hour_key = current_hour.strftime('%Y-%m-%d %H:00')
                    result.append({
                        'date': current_hour.strftime('%H:00'),  # Show only hour for single day
                        'correct': hourly_data[hour_key]['correct'],
                        'bad': hourly_data[hour_key]['bad'],
                        'total': hourly_data[hour_key]['total']
                    })
                    current_hour += timedelta(hours=1)
                
                return result
            else:
                # Group by date for multiple days
                daily_data = defaultdict(lambda: {'correct': 0, 'bad': 0, 'total': 0})
                
                for log in logs:
                    date_key = log.timestamp.date().isoformat()
                    daily_data[date_key]['total'] += 1
                    if log.posture == 'Sitting_upright':
                        daily_data[date_key]['correct'] += 1
                    else:
                        daily_data[date_key]['bad'] += 1
                
                # Fill in missing dates
                result = []
                current = start_date.date()
                end = end_date.date()
                
                while current < end:
                    date_key = current.isoformat()
                    result.append({
                        'date': date_key,
                        'correct': daily_data[date_key]['correct'],
                        'bad': daily_data[date_key]['bad'],
                        'total': daily_data[date_key]['total']
                    })
                    current += timedelta(days=1)
                
                return result
        except SQLAlchemyError as e:
            logger.error(f"Failed to get daily trend: {e}")
            return []
        finally:
            self.close_session(session)
    
    def get_warning_frequency(self, start_date, end_date, group_by='hour'):
        """Get warning frequency grouped by time period"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime
            from collections import defaultdict
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date,
                PostureLog.warning_flag == True
            ).all()
            
            frequency = defaultdict(int)
            
            for log in logs:
                if group_by == 'hour':
                    key = log.timestamp.strftime('%Y-%m-%d %H:00')
                elif group_by == 'day':
                    key = log.timestamp.strftime('%Y-%m-%d')
                else:
                    key = log.timestamp.strftime('%Y-%m-%d')
                
                frequency[key] += 1
            
            return dict(frequency)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get warning frequency: {e}")
            return {}
        finally:
            self.close_session(session)

    # ==================== AI Model Performance Analysis ====================
    
    def get_camera_activation_stats(self, start_date, end_date):
        """Get camera activation statistics for Auto mode"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get logs in auto/fusion mode
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date,
                PostureLog.mode.in_(['auto', 'fusion'])
            ).all()
            
            if not logs:
                return {
                    'total': 0,
                    'sensor_only': 0,
                    'camera_activated': 0,
                    'sensor_percentage': 0,
                    'camera_percentage': 0
                }
            
            total = len(logs)
            camera_activated = sum(1 for l in logs if l.camera_activated)
            sensor_only = total - camera_activated
            
            return {
                'total': total,
                'sensor_only': sensor_only,
                'camera_activated': camera_activated,
                'sensor_percentage': round((sensor_only / total * 100), 1) if total > 0 else 0,
                'camera_percentage': round((camera_activated / total * 100), 1) if total > 0 else 0
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to get camera activation stats: {e}")
            return {}
        finally:
            self.close_session(session)
    
    def get_confidence_comparison(self, start_date, end_date):
        """Compare sensor vs camera confidence scores"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime
            from collections import defaultdict
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get logs with both sensor and camera data
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date,
                PostureLog.sensor_confidence.isnot(None),
                PostureLog.camera_confidence.isnot(None)
            ).all()
            
            if not logs:
                return {
                    'sensor_avg': 0,
                    'camera_avg': 0,
                    'by_posture': {}
                }
            
            # Calculate overall averages
            sensor_avg = sum(l.sensor_confidence for l in logs) / len(logs)
            camera_avg = sum(l.camera_confidence for l in logs) / len(logs)
            
            # Calculate by posture type
            by_posture = defaultdict(lambda: {'sensor': [], 'camera': []})
            for log in logs:
                by_posture[log.posture]['sensor'].append(log.sensor_confidence)
                by_posture[log.posture]['camera'].append(log.camera_confidence)
            
            posture_comparison = {}
            for posture, data in by_posture.items():
                posture_comparison[posture] = {
                    'sensor_avg': round(sum(data['sensor']) / len(data['sensor']) * 100, 1),
                    'camera_avg': round(sum(data['camera']) / len(data['camera']) * 100, 1),
                    'count': len(data['sensor'])
                }
            
            return {
                'sensor_avg': round(sensor_avg * 100, 1),
                'camera_avg': round(camera_avg * 100, 1),
                'by_posture': posture_comparison
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to get confidence comparison: {e}")
            return {}
        finally:
            self.close_session(session)
    
    def get_fusion_conflicts(self, start_date, end_date, limit=50):
        """Get cases where sensor and camera disagreed"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get logs where fusion_reason is not null (indicates conflict/decision)
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date,
                PostureLog.fusion_reason.isnot(None)
            ).order_by(PostureLog.timestamp.desc()).limit(limit).all()
            
            return [log.to_dict() for log in logs]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get fusion conflicts: {e}")
            return []
        finally:
            self.close_session(session)

    # ==================== AI Model Performance Analytics ====================
    
    def get_camera_activation_stats(self, start_date, end_date):
        """Get camera activation statistics for auto/fusion modes"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date,
                PostureLog.mode.in_(['auto', 'fusion'])
            ).all()
            
            if not logs:
                return {
                    'total': 0,
                    'sensor_only': 0,
                    'camera_activated': 0,
                    'sensor_percentage': 0,
                    'camera_percentage': 0
                }
            
            total = len(logs)
            camera_activated = sum(1 for l in logs if l.camera_activated)
            sensor_only = total - camera_activated
            
            return {
                'total': total,
                'sensor_only': sensor_only,
                'camera_activated': camera_activated,
                'sensor_percentage': round((sensor_only / total * 100), 1) if total > 0 else 0,
                'camera_percentage': round((camera_activated / total * 100), 1) if total > 0 else 0
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to get camera activation stats: {e}")
            return {}
        finally:
            self.close_session(session)
    
    def get_confidence_comparison(self, start_date, end_date):
        """Compare sensor vs camera confidence scores"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime
            from collections import defaultdict
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get logs with both sensor and camera data
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date,
                PostureLog.sensor_confidence.isnot(None),
                PostureLog.camera_confidence.isnot(None)
            ).all()
            
            if not logs:
                return {
                    'sensor_avg': 0,
                    'camera_avg': 0,
                    'by_posture': {}
                }
            
            # Calculate overall averages
            sensor_avg = sum(l.sensor_confidence for l in logs) / len(logs) * 100
            camera_avg = sum(l.camera_confidence for l in logs) / len(logs) * 100
            
            # Group by posture
            by_posture = defaultdict(lambda: {'sensor': [], 'camera': []})
            for log in logs:
                by_posture[log.posture]['sensor'].append(log.sensor_confidence * 100)
                by_posture[log.posture]['camera'].append(log.camera_confidence * 100)
            
            # Calculate averages per posture
            posture_stats = {}
            for posture, data in by_posture.items():
                posture_stats[posture] = {
                    'sensor_avg': round(sum(data['sensor']) / len(data['sensor']), 1),
                    'camera_avg': round(sum(data['camera']) / len(data['camera']), 1),
                    'count': len(data['sensor'])
                }
            
            return {
                'sensor_avg': round(sensor_avg, 1),
                'camera_avg': round(camera_avg, 1),
                'by_posture': posture_stats
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to get confidence comparison: {e}")
            return {}
        finally:
            self.close_session(session)
    
    def get_fusion_conflicts(self, start_date, end_date, limit=50):
        """Get fusion decision log showing conflicts"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get fusion mode logs with camera activated
            logs = session.query(PostureLog).filter(
                PostureLog.timestamp >= start_date,
                PostureLog.timestamp < end_date,
                PostureLog.mode == 'fusion',
                PostureLog.camera_activated == True
            ).order_by(PostureLog.timestamp.desc()).limit(limit).all()
            
            return [log.to_dict() for log in logs]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get fusion conflicts: {e}")
            return []
        finally:
            self.close_session(session)

    def get_latest_posture_log(self):
        """Get the most recent posture log entry"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            
            log = session.query(PostureLog).order_by(
                PostureLog.timestamp.desc()
            ).first()
            
            return log
        except SQLAlchemyError as e:
            logger.error(f"Failed to get latest posture log: {e}")
            return None
        finally:
            self.close_session(session)

    # ==================== Data Management & Cleanup ====================
    
    def get_database_stats(self):
        """Get database statistics for cleanup suggestions"""
        session = self.get_session()
        try:
            from database.models import PostureLog, DailyStatistics
            from datetime import datetime, timedelta
            
            # Count total logs
            total_logs = session.query(PostureLog).count()
            
            # Count logs older than 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            old_logs = session.query(PostureLog).filter(
                PostureLog.timestamp < thirty_days_ago
            ).count()
            
            # Get oldest and newest log dates
            oldest = session.query(PostureLog).order_by(
                PostureLog.timestamp.asc()
            ).first()
            newest = session.query(PostureLog).order_by(
                PostureLog.timestamp.desc()
            ).first()
            
            # Count daily statistics
            total_stats = session.query(DailyStatistics).count()
            
            return {
                'total_logs': total_logs,
                'old_logs_30d': old_logs,
                'total_statistics': total_stats,
                'oldest_log': oldest.timestamp if oldest else None,
                'newest_log': newest.timestamp if newest else None,
                'days_of_data': (newest.timestamp - oldest.timestamp).days if (oldest and newest) else 0
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
        finally:
            self.close_session(session)
    
    def clear_old_logs(self, days=30):
        """Clear logs older than specified days"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted = session.query(PostureLog).filter(
                PostureLog.timestamp < cutoff_date
            ).delete()
            
            session.commit()
            logger.info(f"Deleted {deleted} logs older than {days} days")
            
            return {'success': True, 'deleted': deleted}
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to clear old logs: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            self.close_session(session)
    
    def clear_all_logs(self):
        """Clear all posture logs"""
        session = self.get_session()
        try:
            from database.models import PostureLog
            
            deleted = session.query(PostureLog).delete()
            session.commit()
            
            logger.warning(f"Deleted ALL {deleted} posture logs")
            
            return {'success': True, 'deleted': deleted}
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to clear all logs: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            self.close_session(session)
    
    def clear_statistics(self):
        """Clear all daily statistics"""
        session = self.get_session()
        try:
            from database.models import DailyStatistics
            
            deleted = session.query(DailyStatistics).delete()
            session.commit()
            
            logger.warning(f"Deleted ALL {deleted} daily statistics")
            
            return {'success': True, 'deleted': deleted}
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to clear statistics: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            self.close_session(session)

    # ==================== Battery Monitoring ====================
    
    def get_latest_battery_status(self):
        """Get the most recent battery status"""
        session = self.get_session()
        try:
            from database.battery_model import BatteryStatus
            
            status = session.query(BatteryStatus).order_by(
                BatteryStatus.timestamp.desc()
            ).first()
            
            return status.to_dict() if status else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get battery status: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_battery_history(self, hours=24):
        """Get battery history for last N hours"""
        session = self.get_session()
        try:
            from database.battery_model import BatteryStatus
            from datetime import datetime, timedelta
            
            cutoff = datetime.now() - timedelta(hours=hours)
            
            history = session.query(BatteryStatus).filter(
                BatteryStatus.timestamp >= cutoff
            ).order_by(BatteryStatus.timestamp.asc()).all()
            
            return [h.to_dict() for h in history]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get battery history: {e}")
            return []
        finally:
            self.close_session(session)

    # ==================== Battery Monitoring Methods ====================
    
    def insert_battery_status(self, voltage, status, percentage, level):
        """Insert battery status data"""
        session = self.get_session()
        try:
            from database.battery_model import BatteryStatus
            
            battery = BatteryStatus(
                voltage=voltage,
                status=status,
                percentage=percentage,
                level=level
            )
            
            session.add(battery)
            session.commit()
            
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to insert battery status: {e}")
            return False
        finally:
            self.close_session(session)
    
    def get_latest_battery_status(self):
        """Get the most recent battery status"""
        session = self.get_session()
        try:
            from database.battery_model import BatteryStatus
            
            latest = session.query(BatteryStatus).order_by(
                BatteryStatus.timestamp.desc()
            ).first()
            
            return latest.to_dict() if latest else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get latest battery status: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_battery_history(self, hours=24):
        """Get battery history for last N hours"""
        session = self.get_session()
        try:
            from database.battery_model import BatteryStatus
            from datetime import datetime, timedelta
            
            cutoff = datetime.now() - timedelta(hours=hours)
            
            history = session.query(BatteryStatus).filter(
                BatteryStatus.timestamp >= cutoff
            ).order_by(BatteryStatus.timestamp.asc()).all()
            
            return [b.to_dict() for b in history]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get battery history: {e}")
            return []
        finally:
            self.close_session(session)

    # ==================== Battery Monitoring ====================
    
    def insert_battery_log(self, voltage, status, percentage, level):
        """Insert battery monitoring log"""
        session = self.get_session()
        try:
            from database.models import BatteryLog
            
            log = BatteryLog(
                voltage=voltage,
                status=status,
                percentage=percentage,
                level=level
            )
            
            session.add(log)
            session.commit()
            
            logger.info(f"Battery log inserted: {voltage}V, {percentage}%, {status}")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to insert battery log: {e}")
            return False
        finally:
            self.close_session(session)
    
    def get_latest_battery(self):
        """Get latest battery status"""
        session = self.get_session()
        try:
            from database.models import BatteryLog
            
            log = session.query(BatteryLog).order_by(
                BatteryLog.timestamp.desc()
            ).first()
            
            return log.to_dict() if log else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get latest battery: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_battery_history(self, hours=24):
        """Get battery history for last N hours"""
        session = self.get_session()
        try:
            from database.models import BatteryLog
            from datetime import datetime, timedelta
            
            cutoff = datetime.now() - timedelta(hours=hours)
            
            logs = session.query(BatteryLog).filter(
                BatteryLog.timestamp >= cutoff
            ).order_by(BatteryLog.timestamp.asc()).all()
            
            return [log.to_dict() for log in logs]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get battery history: {e}")
            return []
        finally:
            self.close_session(session)

    # ==================== API Key Management Operations ====================
    
    def create_api_key(self, name: str) -> Optional[ApiKey]:
        """
        Create a new API key
        
        Args:
            name: Description/label for the API key
        
        Returns:
            ApiKey object if successful, None otherwise
        """
        import secrets
        
        session = self.get_session()
        try:
            # Generate secure random API key (32 bytes = 64 hex characters)
            api_key = secrets.token_hex(32)
            
            # Create API key object
            key_obj = ApiKey(
                key=api_key,
                name=name,
                is_active=True,
                rate_limit=60  # Default 60 requests per minute
            )
            
            session.add(key_obj)
            session.commit()
            
            logger.info(f"Created API key: {name}")
            return key_obj
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to create API key: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_api_key(self, key: str) -> Optional[ApiKey]:
        """
        Get and validate API key
        
        Args:
            key: API key string
        
        Returns:
            ApiKey object if valid and active, None otherwise
        """
        session = self.get_session()
        try:
            key_obj = session.query(ApiKey).filter_by(key=key, is_active=True).first()
            return key_obj
        except SQLAlchemyError as e:
            logger.error(f"Failed to get API key: {e}")
            return None
        finally:
            self.close_session(session)
    
    def list_api_keys(self) -> List[Dict]:
        """
        List all API keys (for admin panel)
        
        Returns:
            List of API key dictionaries
        """
        session = self.get_session()
        try:
            keys = session.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
            return [k.to_dict() for k in keys]
        except SQLAlchemyError as e:
            logger.error(f"Failed to list API keys: {e}")
            return []
        finally:
            self.close_session(session)
    
    def revoke_api_key(self, key_id: int) -> bool:
        """
        Revoke (disable) an API key
        
        Args:
            key_id: API key ID
        
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            key_obj = session.query(ApiKey).filter_by(id=key_id).first()
            if not key_obj:
                logger.warning(f"API key {key_id} not found")
                return False
            
            key_obj.is_active = False
            session.commit()
            logger.info(f"Revoked API key: {key_obj.name}")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to revoke API key: {e}")
            return False
        finally:
            self.close_session(session)
    
    def update_api_key_last_used(self, key: str) -> bool:
        """
        Update last_used_at timestamp for API key
        
        Args:
            key: API key string
        
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            key_obj = session.query(ApiKey).filter_by(key=key).first()
            if key_obj:
                key_obj.last_used_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to update API key last used: {e}")
            return False
        finally:
            self.close_session(session)
    
    def delete_api_key(self, key_id: int) -> bool:
        """
        Permanently delete an API key
        
        Args:
            key_id: API key ID
        
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            key_obj = session.query(ApiKey).filter_by(id=key_id).first()
            if not key_obj:
                logger.warning(f"API key {key_id} not found")
                return False
            
            name = key_obj.name
            session.delete(key_obj)
            session.commit()
            logger.info(f"Deleted API key: {name}")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to delete API key: {e}")
            return False
        finally:
            self.close_session(session)

