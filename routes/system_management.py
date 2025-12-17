"""
System Management Routes
Handles system health monitoring and data management
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from utils.decorators import admin_required
from database import DBManager
from services.system_monitor import system_monitor
import logging

logger = logging.getLogger(__name__)

# Initialize database manager
db_manager = DBManager()

system_mgmt_bp = Blueprint('system_mgmt', __name__)


@system_mgmt_bp.route('/admin/system')
@login_required
@admin_required
def system_management():
    """System management page (health monitoring + data management)"""
    return render_template('admin_system.html')


# System Health API endpoints
@system_mgmt_bp.route('/api/admin/system/health')
@login_required
@admin_required
def get_system_health():
    """Get system health metrics"""
    try:
        metrics = system_monitor.get_metrics()
        return jsonify({'success': True, 'metrics': metrics}), 200
    except Exception as e:
        logger.error(f"Error getting system health: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# Database Stats API
@system_mgmt_bp.route('/api/admin/database/stats')
@login_required
@admin_required
def get_database_stats():
    """Get database statistics for cleanup suggestions"""
    try:
        stats = db_manager.get_database_stats()
        
        # Generate cleanup suggestions
        suggestions = []
        if stats.get('old_logs_30d', 0) > 1000:
            suggestions.append({
                'type': 'warning',
                'message': f"You have {stats['old_logs_30d']} logs older than 30 days. Consider cleaning them up.",
                'action': 'clear_old',
                'days': 30
            })
        
        if stats.get('total_logs', 0) > 50000:
            suggestions.append({
                'type': 'danger',
                'message': f"Database has {stats['total_logs']} logs. Performance may be affected.",
                'action': 'clear_old',
                'days': 60
            })
        
        return jsonify({
            'success': True,
            'stats': stats,
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get database stats'}), 500


# Data Reset API
@system_mgmt_bp.route('/api/admin/reset', methods=['POST'])
@login_required
@admin_required
def reset_data():
    """Clear historical data (with confirmation)"""
    try:
        data = request.get_json()
        confirm = data.get('confirm', False)
        action = data.get('action', 'clear_all')
        days = data.get('days', 30)
        
        if not confirm:
            return jsonify({'success': False, 'message': 'Confirmation required'}), 400
        
        logger.warning(f"Admin requested data reset: {action}")
        
        result = None
        if action == 'clear_all':
            result = db_manager.clear_all_logs()
        elif action == 'clear_old':
            result = db_manager.clear_old_logs(days=days)
        elif action == 'clear_stats':
            result = db_manager.clear_statistics()
        else:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
        
        if result and result.get('success'):
            return jsonify({
                'success': True,
                'message': f"Successfully deleted {result.get('deleted', 0)} records",
                'deleted': result.get('deleted', 0)
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to delete data')
            }), 500
        
    except Exception as e:
        logger.error(f"Error resetting data: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to reset data'}), 500
