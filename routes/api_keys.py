"""
API Key Management Routes
Admin-only endpoints for managing API keys
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import DBManager
from utils.decorators import admin_required

logger = logging.getLogger(__name__)

# Create blueprint
api_keys_bp = Blueprint('api_keys', __name__, url_prefix='/api/admin')

# Initialize database manager
db_manager = DBManager()


@api_keys_bp.route('/api-keys', methods=['GET'])
@login_required
@admin_required
def list_api_keys():
    """
    List all API keys
    
    Returns:
        JSON list of API keys (without exposing full key values)
    """
    try:
        keys = db_manager.list_api_keys()
        
        # Mask the API key for security (show only first 8 chars)
        for key in keys:
            if 'key' in key:
                key['key_preview'] = key['key'][:8] + '...' + key['key'][-4:]
                del key['key']  # Don't expose full key
        
        return jsonify({'success': True, 'api_keys': keys}), 200
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@api_keys_bp.route('/api-keys', methods=['POST'])
@login_required
@admin_required
def create_api_key():
    """
    Create a new API key
    
    Expected JSON:
    {
        "name": "Node-RED Production"
    }
    
    Returns:
        JSON with the new API key (ONLY TIME the full key is returned)
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'success': False, 'message': 'Name is required'}), 400
        
        name = data['name']
        
        # Create API key
        key_obj = db_manager.create_api_key(name)
        
        if not key_obj:
            return jsonify({'success': False, 'message': 'Failed to create API key'}), 500
        
        logger.info(f"Admin '{current_user.username}' created API key: {name}")
        
        # Return full key (ONLY TIME it's exposed)
        return jsonify({
            'success': True,
            'message': 'API key created successfully',
            'api_key': key_obj.to_dict()
        }), 201
    except Exception as e:
        logger.error(f"Failed to create API key: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@api_keys_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_api_key(key_id):
    """
    Delete an API key permanently
    
    Args:
        key_id: API key ID
    
    Returns:
        JSON success/failure message
    """
    try:
        success = db_manager.delete_api_key(key_id)
        
        if success:
            logger.info(f"Admin '{current_user.username}' deleted API key ID: {key_id}")
            return jsonify({'success': True, 'message': 'API key deleted'}), 200
        else:
            return jsonify({'success': False, 'message': 'API key not found'}), 404
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@api_keys_bp.route('/api-keys/<int:key_id>/revoke', methods=['PATCH'])
@login_required
@admin_required
def revoke_api_key(key_id):
    """
    Revoke (disable) an API key
    
    Args:
        key_id: API key ID
    
    Returns:
        JSON success/failure message
    """
    try:
        success = db_manager.revoke_api_key(key_id)
        
        if success:
            logger.info(f"Admin '{current_user.username}' revoked API key ID: {key_id}")
            return jsonify({'success': True, 'message': 'API key revoked'}), 200
        else:
            return jsonify({'success': False, 'message': 'API key not found'}), 404
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
