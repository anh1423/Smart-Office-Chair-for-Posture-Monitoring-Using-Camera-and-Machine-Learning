"""
System Health Monitoring Service
Monitors CPU, RAM, Temperature, and other system metrics
"""
import logging
import os

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor system health metrics"""
    
    def __init__(self):
        self.psutil_available = False
        try:
            import psutil
            self.psutil = psutil
            self.psutil_available = True
            logger.info("psutil loaded successfully")
        except ImportError:
            logger.warning("psutil not available - system monitoring disabled")
    
    def get_cpu_usage(self):
        """Get current CPU usage percentage"""
        if not self.psutil_available:
            return {'available': False, 'usage': 0}
        
        try:
            cpu_percent = self.psutil.cpu_percent(interval=0.1)
            cpu_count = self.psutil.cpu_count()
            
            return {
                'available': True,
                'usage': round(cpu_percent, 1),
                'cores': cpu_count
            }
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return {'available': False, 'usage': 0}
    
    def get_memory_usage(self):
        """Get current memory usage"""
        if not self.psutil_available:
            return {'available': False}
        
        try:
            mem = self.psutil.virtual_memory()
            
            return {
                'available': True,
                'total': mem.total,
                'used': mem.used,
                'free': mem.free,
                'percent': round(mem.percent, 1),
                'total_gb': round(mem.total / (1024**3), 2),
                'used_gb': round(mem.used / (1024**3), 2),
                'free_gb': round(mem.free / (1024**3), 2)
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {'available': False}
    
    def get_cpu_temperature(self):
        """Get CPU temperature (Raspberry Pi specific)"""
        if not self.psutil_available:
            return {'available': False, 'temp': 0}
        
        try:
            # Try psutil sensors_temperatures first
            temps = self.psutil.sensors_temperatures()
            if temps:
                # Look for CPU temp
                for name, entries in temps.items():
                    for entry in entries:
                        if 'cpu' in name.lower() or 'core' in entry.label.lower():
                            return {
                                'available': True,
                                'temp': round(entry.current, 1),
                                'high': entry.high if entry.high else 85,
                                'critical': entry.critical if entry.critical else 95
                            }
        except:
            pass
        
        # Fallback: Read from /sys/class/thermal (Raspberry Pi)
        try:
            thermal_file = '/sys/class/thermal/thermal_zone0/temp'
            if os.path.exists(thermal_file):
                with open(thermal_file, 'r') as f:
                    temp = float(f.read().strip()) / 1000.0
                return {
                    'available': True,
                    'temp': round(temp, 1),
                    'high': 70,
                    'critical': 80
                }
        except Exception as e:
            logger.error(f"Error reading temperature: {e}")
        
        return {'available': False, 'temp': 0}
    
    def get_disk_usage(self):
        """Get disk usage for current partition"""
        if not self.psutil_available:
            return {'available': False}
        
        try:
            disk = self.psutil.disk_usage('/')
            
            return {
                'available': True,
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': round(disk.percent, 1),
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2)
            }
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {'available': False}
    
    def get_all_metrics(self):
        """Get all system metrics at once"""
        return {
            'cpu': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'temperature': self.get_cpu_temperature(),
            'disk': self.get_disk_usage()
        }


# Global instance
system_monitor = SystemMonitor()
