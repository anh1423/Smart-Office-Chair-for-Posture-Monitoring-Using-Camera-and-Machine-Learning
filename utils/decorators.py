"""
Utility decorators for route protection
"""
from functools import wraps
from flask import redirect, url_for, abort
from flask_login import current_user


def admin_required(f):
    """
    Decorator to require admin role for route access
    
    Usage:
        @app.route('/admin-only')
        @login_required
        @admin_required
        def admin_page():
            return "Admin only content"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login_page'))
        
        if current_user.role != 'admin':
            abort(403)  # Forbidden
        
        return f(*args, **kwargs)
    
    return decorated_function
