"""
API Routes for Posture Monitoring System
Handles all REST API endpoints
"""
import json
import logging
from datetime import datetime, date
from flask import Blueprint, request, jsonify, Response
import numpy as np

from database import DBManager
from models import get_fusion_logic
from utils import get_camera_manager
from utils.auth import require_api_key
import config

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize components
db_manager = DBManager()
fusion_logic = get_fusion_logic()
camera_manager = get_camera_manager()

# Warning tracker: {posture_label: consecutive_count}
warning_tracker = {
    'last_posture': None,
    'consecutive_count': 0,
    'warning_threshold': 5,  # Require 5 consecutive detections for first warning
    'warned_postures': set()  # Track postures that have been warned before
}


@api_bp.route('/predict', methods=['POST'])
@require_api_key
def predict():
    """
    Main prediction endpoint - receives sensor data from Node-RED
    
    Expected JSON:
    {
        "sensor1": float,
        "sensor2": float,
        ...
        "sensor7": float
    }
    
    Returns JSON:
    {
        "label": str,
        "confidence": float,
        "warning": bool,
        "mode": str,
        "timestamp": str
    }
    """
    try:
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract sensor values
        sensor_values = []
        for i in range(1, 8):
            key = f'sensor{i}'
            if key not in data:
                return jsonify({'error': f'Missing {key}'}), 400
            sensor_values.append(float(data[key]))
        
        logger.info(f"Received sensor data: {sensor_values}")
        
        # Load current configuration from database
        mode = db_manager.get_config('mode') or config.DEFAULT_MODE
        auto_threshold = float(db_manager.get_config('auto_threshold') or config.DEFAULT_AUTO_THRESHOLD)
        fusion_weights_str = db_manager.get_config('fusion_weights')
        
        if fusion_weights_str:
            fusion_weights = json.loads(fusion_weights_str)
        else:
            fusion_weights = config.DEFAULT_FUSION_WEIGHTS
        
        # Update fusion logic configuration
        fusion_logic.update_config(
            mode=mode,
            auto_threshold=auto_threshold,
            fusion_weights=fusion_weights
        )
        
        # Get camera frame if needed (for camera_only, auto, or fusion mode)
        camera_frame = None
        if mode in ['camera_only', 'auto', 'fusion']:
            camera_frame = camera_manager.capture_for_inference()
            if camera_frame is None:
                logger.warning(f"Camera frame not available for mode '{mode}'")
        
        # Make prediction
        label, confidence, metadata = fusion_logic.predict(sensor_values, camera_frame)
        
        # Check if this is a bad posture
        is_bad = fusion_logic.is_bad_posture(label)
        
        # Update warning tracker - ALWAYS check if posture changed
        if warning_tracker['last_posture'] != label:
            # Posture changed (from anything to anything)
            
            # If we're leaving a bad posture, remove it from warned set
            # This ensures it needs 5 consecutive again next time
            if warning_tracker['last_posture'] and warning_tracker['last_posture'] in warning_tracker['warned_postures']:
                warning_tracker['warned_postures'].discard(warning_tracker['last_posture'])
                logger.info(f"Removed {warning_tracker['last_posture']} from warned set (interrupted)")
            
            # Update to new posture
            warning_tracker['last_posture'] = label
            warning_tracker['consecutive_count'] = 1 if is_bad else 0
            logger.info(f"Posture changed to: {label}, Bad: {is_bad}, Reset counter to {warning_tracker['consecutive_count']}")
        else:
            # Same posture as before
            if is_bad:
                # Same bad posture, increment counter
                warning_tracker['consecutive_count'] += 1
                logger.info(f"Same bad posture: {label}, Consecutive: {warning_tracker['consecutive_count']}")
            else:
                # Same good posture, keep counter at 0
                warning_tracker['consecutive_count'] = 0
        
        # Determine warning flag
        if is_bad:
            # Check if this posture was warned before
            already_warned = label in warning_tracker['warned_postures']
            
            if already_warned:
                # This posture was warned before, trigger warning immediately
                warning_flag = True
                logger.info(f"Posture: {label}, Already warned before → Warning: True")
            else:
                # First time seeing this bad posture, need 5 consecutive
                warning_flag = warning_tracker['consecutive_count'] >= warning_tracker['warning_threshold']
                if warning_flag:
                    # Reached threshold, add to warned set
                    warning_tracker['warned_postures'].add(label)
                    logger.info(f"Posture: {label}, Consecutive: {warning_tracker['consecutive_count']}, First warning → Added to warned set")
                else:
                    logger.info(f"Posture: {label}, Consecutive: {warning_tracker['consecutive_count']}/{warning_tracker['warning_threshold']}, Warning: False")
        else:
            # Good posture, no warning
            warning_flag = False
        
        # Save to database with AI performance tracking
        sensor_data_dict = {f'sensor{i+1}': val for i, val in enumerate(sensor_values)}
        
        # Extract AI performance metadata
        sensor_conf = metadata.get('sensor_confidence')
        camera_conf = metadata.get('camera_confidence')
        camera_used = metadata.get('camera_used', False)
        
        # Determine fusion reason
        fusion_reason = None
        if mode == 'auto':
            if camera_used:
                if sensor_conf is not None:
                    fusion_reason = f"Sensor low ({sensor_conf:.2f}), camera activated"
                else:
                    fusion_reason = "Camera activated"
            else:
                if sensor_conf is not None:
                    fusion_reason = f"Sensor confident ({sensor_conf:.2f})"
                else:
                    fusion_reason = "Sensor only"
        elif mode == 'fusion':
            sensor_label = metadata.get('sensor_label', '')
            camera_label = metadata.get('camera_label', '')
            if sensor_label != camera_label:
                fusion_reason = f"Conflict: S={sensor_label}, C={camera_label}"
            else:
                fusion_reason = "Both models agree"
        
        db_manager.insert_posture_log(
            posture=label,
            confidence=confidence,
            mode=mode,
            warning_flag=warning_flag,
            sensor_values=sensor_data_dict,
            sensor_confidence=sensor_conf,
            camera_confidence=camera_conf,
            camera_activated=camera_used,
            fusion_reason=fusion_reason
        )
        
        # Prepare response
        response = {
            'label': label,
            'confidence': round(confidence, 4),
            'warning': warning_flag,
            'mode': mode,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata
        }
        
        logger.info(f"Prediction result: {label} (confidence: {confidence:.2f}, warning: {warning_flag})")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get current system configuration
    
    Returns JSON:
    {
        "mode": str,
        "auto_threshold": float,
        "fusion_weights": {...},
        "warning_threshold": int,
        "warning_time_limit": int
    }
    """
    try:
        # Load from file
        if config.CONFIG_FILE.exists():
            with open(config.CONFIG_FILE, 'r') as f:
                file_config = json.load(f)
        else:
            file_config = {}
        
        # Also get from database
        db_config = db_manager.get_all_configs()
        
        # Merge (database takes priority)
        merged_config = {
            'mode': db_config.get('mode', file_config.get('mode', config.DEFAULT_MODE)),
            'auto_threshold': float(db_config.get('auto_threshold', file_config.get('auto_threshold', config.DEFAULT_AUTO_THRESHOLD))),
            'fusion_weights': json.loads(db_config.get('fusion_weights', json.dumps(file_config.get('fusion_weights', config.DEFAULT_FUSION_WEIGHTS)))),
            'warning_threshold': int(db_config.get('warning_threshold', file_config.get('warning_threshold', config.WARNING_THRESHOLD))),
            'warning_time_limit': int(db_config.get('warning_time_limit', file_config.get('warning_time_limit', config.WARNING_TIME_LIMIT)))
        }
        
        return jsonify(merged_config), 200
        
    except Exception as e:
        logger.error(f"Get config error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/config', methods=['POST'])
def save_config():
    """
    Save system configuration
    
    Expected JSON:
    {
        "mode": str,  # 'sensor_only', 'camera_only', 'auto', 'fusion'
        "auto_threshold": float,
        "fusion_weights": {"sensor": float, "camera": float},
        "warning_threshold": int,
        "warning_time_limit": int
    }
    
    Returns JSON:
    {
        "success": bool,
        "message": str
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Validate mode
        valid_modes = ['sensor_only', 'camera_only', 'auto', 'fusion']
        if 'mode' in data and data['mode'] not in valid_modes:
            return jsonify({'success': False, 'message': f'Invalid mode. Must be one of: {valid_modes}'}), 400
        
        # Save to file
        with open(config.CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save to database
        for key, value in data.items():
            if isinstance(value, dict):
                value = json.dumps(value)
            db_manager.set_config(key, str(value))
        
        logger.info(f"Configuration saved: {data}")
        
        return jsonify({'success': True, 'message': 'Configuration saved successfully'}), 200
        
    except Exception as e:
        logger.error(f"Save config error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get statistics for a specific date
    
    Query params:
        date: YYYY-MM-DD (optional, defaults to today)
    
    Returns JSON:
    {
        "date": str,
        "total_detections": int,
        "total_warnings": int,
        "correct_posture_count": int,
        "bad_posture_count": int,
        "correct_percentage": float,
        "posture_distribution": {...}
    }
    """
    try:
        # Get date parameter
        date_str = request.args.get('date')
        
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        # Get statistics
        stats = db_manager.get_posture_summary(target_date)
        
        return jsonify(stats), 200
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        logger.error(f"Get stats error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/stats/range', methods=['GET'])
def get_stats_range():
    """
    Get statistics for a date range
    
    Query params:
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
    
    Returns JSON:
    {
        "stats": [...]
    }
    """
    try:
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')
        
        if not start_str or not end_str:
            return jsonify({'error': 'Both start_date and end_date are required'}), 400
        
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        
        # Get statistics
        stats_list = db_manager.get_statistics_range(start_date, end_date)
        stats_dict = [s.to_dict() for s in stats_list]
        
        return jsonify({'stats': stats_dict}), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        logger.error(f"Get stats range error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/video_feed', methods=['GET'])
def video_feed():
    """
    Video streaming endpoint - returns MJPEG stream
    
    Returns:
        MJPEG stream
    """
    def generate_frames():
        """Generator function for video frames"""
        while True:
            try:
                # Get JPEG frame from camera manager
                frame_bytes = camera_manager.get_jpeg_frame(quality=80)
                
                if frame_bytes is None:
                    # No frame available, send placeholder or wait
                    import time
                    time.sleep(0.1)
                    continue
                
                # Yield frame in multipart format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
            except Exception as e:
                logger.error(f"Video feed error: {e}")
                break
    
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@api_bp.route('/camera/status', methods=['GET'])
def camera_status():
    """
    Get camera status
    
    Returns JSON:
    {
        "is_available": bool,
        "camera_index": int,
        "width": int,
        "height": int,
        ...
    }
    """
    try:
        status = camera_manager.get_status()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Camera status error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/latest', methods=['GET'])
def get_latest_posture():
    """
    Get the latest posture log
    
    Returns JSON:
    {
        "posture": str,
        "confidence": float,
        "timestamp": str,
        "warning": bool,
        "mode": str
    }
    """
    try:
        # Get latest log from database
        logs = db_manager.get_posture_logs(limit=1)
        
        if not logs:
            return jsonify({'error': 'No posture data available'}), 404
        
        latest = logs[0]
        
        return jsonify({
            'posture': latest.posture,
            'confidence': round(latest.confidence, 4),
            'timestamp': latest.timestamp.isoformat(),
            'warning': latest.warning_flag,
            'mode': latest.mode
        }), 200
        
    except Exception as e:
        logger.error(f"Get latest posture error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Returns JSON:
    {
        "status": "ok",
        "timestamp": str,
        "components": {...}
    }
    """
    try:
        components = {
            'database': 'ok' if db_manager else 'error',
            'camera': 'ok' if camera_manager.is_available() else 'error',
            'sensor_model': 'ok' if fusion_logic.sensor_model.is_loaded else 'error',
            'camera_model': 'ok' if fusion_logic.camera_model.is_loaded else 'error'
        }
        
        overall_status = 'ok' if all(v == 'ok' for v in components.values()) else 'degraded'
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'components': components
        }), 200
        
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500
