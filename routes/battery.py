"""
Battery Monitoring Routes
Handles battery voltage and status data from ESP32 via Node-RED
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from database import DBManager
from utils.auth import require_api_key
import logging

logger = logging.getLogger(__name__)

# Initialize database manager
db_manager = DBManager()

battery_bp = Blueprint('battery', __name__)


@battery_bp.route('/api/battery', methods=['POST'])
@require_api_key
def receive_battery_data():
    """Receive battery data from Node-RED"""
    try:
        data = request.get_json()
        
        voltage = float(data.get('voltage', 0))
        status = data.get('status', 'N/A')  # Default to N/A if not provided
        percentage = float(data.get('percentage', 0))
        level = data.get('level', 'unknown')
        
        # Insert into database
        success = db_manager.insert_battery_log(voltage, status, percentage, level)
        
        if success:
            return jsonify({'success': True, 'message': 'Battery data saved'}), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save'}), 500
            
    except Exception as e:
        logger.error(f"Error receiving battery data: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@battery_bp.route('/api/battery/latest')
@login_required
def get_latest_battery():
    """Get latest battery status"""
    try:
        data = db_manager.get_latest_battery()
        
        if data:
            return jsonify({'success': True, 'data': data}), 200
        else:
            return jsonify({'success': False, 'message': 'No battery data'}), 404
            
    except Exception as e:
        logger.error(f"Error getting latest battery: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@battery_bp.route('/api/battery/history')
@login_required
def get_battery_history():
    """Get battery history"""
    try:
        hours = request.args.get('hours', 24, type=int)
        data = db_manager.get_battery_history(hours=hours)
        
        return jsonify({'success': True, 'data': data}), 200
            
    except Exception as e:
        logger.error(f"Error getting battery history: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
