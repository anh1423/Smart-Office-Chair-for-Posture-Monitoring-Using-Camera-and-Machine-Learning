"""
Advanced Analytics Routes (Admin Only)
Provides comprehensive analytics, AI performance tracking, and system monitoring
"""
import logging
from flask import Blueprint, request, jsonify, render_template, send_file
from flask_login import login_required, current_user
from utils.decorators import admin_required
from database import DBManager
from datetime import datetime, timedelta
import io

logger = logging.getLogger(__name__)

# Create blueprint
admin_analytics_bp = Blueprint('admin_analytics', __name__)

# Initialize database manager
db_manager = DBManager()


@admin_analytics_bp.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics_page():
    """Advanced analytics dashboard (admin only)"""
    return render_template('admin_analytics.html')


@admin_analytics_bp.route('/api/admin/stats/<period>')
@login_required
@admin_required
def get_period_stats(period):
    """Get statistics for specified period (day/week/month)"""
    try:
        # Calculate date range based on period (local time)
        end_date_local = datetime.now()
        
        if period == 'day':
            start_date_local = end_date_local.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date_local = end_date_local - timedelta(days=7)
        elif period == 'month':
            start_date_local = end_date_local - timedelta(days=30)
        else:
            return jsonify({'success': False, 'message': 'Invalid period'}), 400
        
        # Convert to UTC for database query
        start_date = start_date_local - timedelta(hours=7)
        end_date = end_date_local - timedelta(hours=7)
        
        # Get statistics
        stats = db_manager.get_statistics_by_date_range(start_date, end_date)
        
        return jsonify({
            'success': True,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting period stats: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get statistics'}), 500


@admin_analytics_bp.route('/api/admin/stats/custom', methods=['POST'])
@login_required
@admin_required
def get_custom_stats():
    """Get statistics for custom date range"""
    try:
        data = request.get_json()
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        
        # Add one day to end_date to include the entire day
        end_date = end_date + timedelta(days=1)
        
        stats = db_manager.get_statistics_by_date_range(start_date, end_date)
        
        return jsonify({
            'success': True,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting custom stats: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get statistics'}), 500


@admin_analytics_bp.route('/api/admin/trend/<period>')
@login_required
@admin_required
def get_trend_data(period):
    """Get daily trend data for charts"""
    try:
        # Get local time then convert to UTC for database query
        end_date_local = datetime.now()
        
        if period == 'day':
            start_date_local = end_date_local.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date_local = end_date_local - timedelta(days=7)
        elif period == 'month':
            start_date_local = end_date_local - timedelta(days=30)
        else:
            return jsonify({'success': False, 'message': 'Invalid period'}), 400
        
        # Convert to UTC (subtract 7 hours) for database query
        start_date = start_date_local - timedelta(hours=7)
        end_date = end_date_local - timedelta(hours=7)
        
        trend = db_manager.get_daily_trend(start_date, end_date)
        
        return jsonify({
            'success': True,
            'trend': trend
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trend data: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get trend data'}), 500


@admin_analytics_bp.route('/api/admin/warnings/<period>')
@login_required
@admin_required
def get_warning_frequency(period):
    """Get warning frequency data"""
    try:
        end_date_local = datetime.now()
        
        if period == 'day':
            start_date_local = end_date_local.replace(hour=0, minute=0, second=0, microsecond=0)
            group_by = 'hour'
        elif period == 'week':
            start_date_local = end_date_local - timedelta(days=7)
            group_by = 'day'
        elif period == 'month':
            start_date_local = end_date_local - timedelta(days=30)
            group_by = 'day'
        else:
            return jsonify({'success': False, 'message': 'Invalid period'}), 400
        
        # Convert to UTC for database query
        start_date = start_date_local - timedelta(hours=7)
        end_date = end_date_local - timedelta(hours=7)
        
        frequency = db_manager.get_warning_frequency(start_date, end_date, group_by)
        
        return jsonify({
            'success': True,
            'frequency': frequency
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting warning frequency: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get warning frequency'}), 500


@admin_analytics_bp.route('/api/admin/export', methods=['POST'])
@login_required
@admin_required
def export_data():
    """Export data to Excel or CSV"""
    try:
        data = request.get_json()
        format_type = data.get('format', 'excel')  # 'excel' or 'csv'
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        end_date = end_date + timedelta(days=1)
        
        # Get logs
        logs = db_manager.get_logs_by_date_range(start_date, end_date)
        
        if not logs:
            return jsonify({'success': False, 'message': 'No data to export'}), 400
        
        # Create DataFrame
        import pandas as pd
        df = pd.DataFrame(logs)
        
        # Format columns
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create file
        output = io.BytesIO()
        filename = f"posture_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        
        if format_type == 'excel':
            df.to_excel(output, index=False, engine='openpyxl')
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename += '.xlsx'
        else:  # csv
            df.to_csv(output, index=False)
            mimetype = 'text/csv'
            filename += '.csv'
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to export data'}), 500


@admin_analytics_bp.route('/api/admin/reset', methods=['POST'])
@login_required
@admin_required
def reset_data():
    """Clear historical data (with confirmation)"""
    try:
        data = request.get_json()
        confirm = data.get('confirm', False)
        action = data.get('action', 'clear_all')  # clear_all, clear_old, clear_stats
        days = data.get('days', 30)  # For clear_old action
        
        if not confirm:
            return jsonify({'success': False, 'message': 'Confirmation required'}), 400
        
        logger.warning(f"Admin {current_user.username} requested data reset: {action}")
        
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


# ==================== AI Model Performance Routes ====================

@admin_analytics_bp.route('/api/admin/ai-performance/camera-activation/<period>')
@login_required
@admin_required
def get_camera_activation(period):
    """Get camera activation statistics"""
    try:
        end_date_local = datetime.now()
        
        if period == 'day':
            start_date_local = end_date_local.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date_local = end_date_local - timedelta(days=7)
        elif period == 'month':
            start_date_local = end_date_local - timedelta(days=30)
        else:
            return jsonify({'success': False, 'message': 'Invalid period'}), 400
        
        # Convert to UTC
        start_date = start_date_local - timedelta(hours=7)
        end_date = end_date_local - timedelta(hours=7)
        
        stats = db_manager.get_camera_activation_stats(start_date, end_date)
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting camera activation stats: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get camera activation stats'}), 500


@admin_analytics_bp.route('/api/admin/ai-performance/confidence-comparison/<period>')
@login_required
@admin_required
def get_confidence_comparison(period):
    """Get confidence score comparison between sensor and camera"""
    try:
        end_date_local = datetime.now()
        
        if period == 'day':
            start_date_local = end_date_local.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date_local = end_date_local - timedelta(days=7)
        elif period == 'month':
            start_date_local = end_date_local - timedelta(days=30)
        else:
            return jsonify({'success': False, 'message': 'Invalid period'}), 400
        
        # Convert to UTC
        start_date = start_date_local - timedelta(hours=7)
        end_date = end_date_local - timedelta(hours=7)
        
        comparison = db_manager.get_confidence_comparison(start_date, end_date)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting confidence comparison: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get confidence comparison'}), 500


@admin_analytics_bp.route('/api/admin/ai-performance/fusion-conflicts/<period>')
@login_required
@admin_required
def get_fusion_conflicts(period):
    """Get fusion decision log (conflicts)"""
    try:
        end_date_local = datetime.now()
        
        if period == 'day':
            start_date_local = end_date_local.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date_local = end_date_local - timedelta(days=7)
        elif period == 'month':
            start_date_local = end_date_local - timedelta(days=30)
        else:
            return jsonify({'success': False, 'message': 'Invalid period'}), 400
        
        # Convert to UTC
        start_date = start_date_local - timedelta(hours=7)
        end_date = end_date_local - timedelta(hours=7)
        
        conflicts = db_manager.get_fusion_conflicts(start_date, end_date)
        
        return jsonify({
            'success': True,
            'conflicts': conflicts
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting fusion conflicts: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get fusion conflicts'}), 500


# ==================== Sensor Visualization Routes ====================

@admin_analytics_bp.route('/api/admin/sensor/realtime')
@login_required
@admin_required
def get_realtime_sensor():
    """Get real-time sensor data from latest log"""
    try:
        latest = db_manager.get_latest_posture_log()
        
        if not latest:
            return jsonify({
                'success': False,
                'message': 'No sensor data available'
            }), 404
        
        return jsonify({
            'success': True,
            'timestamp': latest.timestamp.isoformat(),
            'posture': latest.posture,
            'sensor_values': latest.sensor_values or {}
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting realtime sensor data: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get sensor data'}), 500


@admin_analytics_bp.route('/api/admin/sensor/history')
@login_required
@admin_required
def get_sensor_history():
    """Get sensor history for selected period"""
    try:
        from datetime import datetime, timedelta
        
        period = request.args.get('period', 'day')
        
        # Calculate date range based on period
        end_date_local = datetime.now()
        
        if period == 'day':
            start_date_local = end_date_local.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date_local = end_date_local - timedelta(days=7)
        elif period == 'month':
            start_date_local = end_date_local - timedelta(days=30)
        else:
            start_date_local = end_date_local.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Convert to UTC
        start_date = start_date_local - timedelta(hours=7)
        end_date = end_date_local - timedelta(hours=7)
        
        logs = db_manager.get_logs_by_date_range(start_date, end_date)
        
        # Format for chart
        history = []
        for log in logs:
            if log.get('sensor_values'):
                history.append({
                    'timestamp': log['timestamp'],
                    'sensors': log['sensor_values']
                })
        
        return jsonify({
            'success': True,
            'history': history
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sensor history: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get sensor history'}), 500


# ==================== System Health Monitoring Routes ====================

@admin_analytics_bp.route('/api/admin/system/health')
@login_required
@admin_required
def get_system_health():
    """Get current system health metrics"""
    try:
        from services import system_monitor
        
        metrics = system_monitor.get_all_metrics()
        
        return jsonify({
            'success': True,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get system health'}), 500


@admin_analytics_bp.route('/api/admin/database/stats')
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


# ==================== Battery Monitoring Routes ====================

@admin_analytics_bp.route('/api/admin/battery/status')
@login_required
@admin_required
def get_battery_status():
    """Get current battery status"""
    try:
        status = db_manager.get_latest_battery_status()
        
        if status:
            return jsonify({
                'success': True,
                'battery': status
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No battery data available'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting battery status: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get battery status'}), 500


@admin_analytics_bp.route('/api/admin/battery/history')
@login_required
@admin_required
def get_battery_history():
    """Get battery history"""
    try:
        hours = request.args.get('hours', 24, type=int)
        history = db_manager.get_battery_history(hours=hours)
        
        return jsonify({
            'success': True,
            'history': history
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting battery history: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to get battery history'}), 500
