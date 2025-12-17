"""
Authentication utilities for API security
Provides decorators for API key and JWT authentication
"""
import logging
from functools import wraps
from flask import request, jsonify
from database import DBManager

logger = logging.getLogger(__name__)

# Initialize database manager
db_manager = DBManager()


def require_api_key(f):
    """
    Decorator to require API key authentication
    
    Usage:
        @api_bp.route('/predict', methods=['POST'])
        @require_api_key
        def predict():
            # Your endpoint logic
            pass
    
    API key should be provided in request header:
        X-API-Key: your-api-key-here
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning(f"API request to {request.path} without API key")
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide X-API-Key header'
            }), 401
        
        # Validate API key
        key_obj = db_manager.get_api_key(api_key)
        
        if not key_obj:
            logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid or has been revoked'
            }), 401
        
        # Update last used timestamp (async, don't wait)
        try:
            db_manager.update_api_key_last_used(api_key)
        except Exception as e:
            logger.error(f"Failed to update API key last used: {e}")
        
        # Store API key info in request context for logging
        request.api_key_name = key_obj.name
        request.api_key_id = key_obj.id
        
        logger.info(f"API request authenticated: {key_obj.name}")
        
        # Call the actual endpoint
        return f(*args, **kwargs)
    
    return decorated_function


def optional_api_key(f):
    """
    Decorator for endpoints that accept both authenticated and public access
    If API key is provided, it will be validated
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if api_key:
            # Validate if provided
            key_obj = db_manager.get_api_key(api_key)
            if key_obj:
                request.api_key_name = key_obj.name
                request.api_key_id = key_obj.id
                db_manager.update_api_key_last_used(api_key)
        
        return f(*args, **kwargs)
    
    return decorated_function
