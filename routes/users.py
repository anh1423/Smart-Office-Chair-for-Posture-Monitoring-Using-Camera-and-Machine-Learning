"""
User Management Routes
Admin-only routes for managing user accounts
"""
import logging
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from utils.decorators import admin_required
from database import DBManager

logger = logging.getLogger(__name__)

# Create blueprint
users_bp = Blueprint('users', __name__)

# Initialize database manager
db_manager = DBManager()


@users_bp.route('/users')
@login_required
@admin_required
def users_page():
    """User management page (admin only)"""
    return render_template('users.html')


@users_bp.route('/api/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        users = db_manager.get_all_users()
        return jsonify({'success': True, 'users': users}), 200
    except Exception as e:
        logger.error(f"Error fetching users: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to fetch users'}), 500


@users_bp.route('/api/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Create new user (admin only)"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'user')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        # Create user
        user = db_manager.create_user(username, password, email)
        if not user:
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        # Set role if specified
        if role == 'admin':
            db_manager.update_user_role(user.id, 'admin')
        
        logger.info(f"Admin {current_user.username} created user {username}")
        return jsonify({'success': True, 'message': 'User created successfully', 'user': user.to_dict()}), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to create user'}), 500


@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    try:
        # Prevent self-deletion
        if user_id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
        
        success = db_manager.delete_user(user_id)
        if success:
            logger.info(f"Admin {current_user.username} deleted user {user_id}")
            return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting user: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to delete user'}), 500


@users_bp.route('/api/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Enable/disable user account (admin only)"""
    try:
        # Prevent self-disable
        if user_id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot disable your own account'}), 400
        
        data = request.get_json()
        is_active = data.get('is_active', True)
        
        success = db_manager.update_user_status(user_id, is_active)
        if success:
            status = 'enabled' if is_active else 'disabled'
            logger.info(f"Admin {current_user.username} {status} user {user_id}")
            return jsonify({'success': True, 'message': f'User {status} successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Error toggling user status: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to update user status'}), 500


@users_bp.route('/api/users/<int:user_id>/role', methods=['PUT'])
@login_required
@admin_required
def update_user_role(user_id):
    """Update user role (admin only)"""
    try:
        data = request.get_json()
        role = data.get('role')
        
        if role not in ['admin', 'user']:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        success = db_manager.update_user_role(user_id, role)
        if success:
            logger.info(f"Admin {current_user.username} changed user {user_id} role to {role}")
            return jsonify({'success': True, 'message': 'Role updated successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Error updating user role: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to update role'}), 500
