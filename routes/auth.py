"""
Authentication Routes for Posture Monitoring System
Handles login, logout, and session management
"""
import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from database import DBManager

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize database manager
db_manager = DBManager()


@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Display login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle login form submission"""
    try:
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Please provide both username and password', 'error')
            return redirect(url_for('auth.login_page'))
        
        # Get user from database
        user = db_manager.get_user_by_username(username)
        
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login_page'))
        
        # Login user
        login_user(user, remember=remember)
        logger.info(f"User '{username}' logged in successfully")
        
        # Redirect to dashboard
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))
        
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        flash('An error occurred during login', 'error')
        return redirect(url_for('auth.login_page'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout current user"""
    try:
        username = current_user.username
        logout_user()
        logger.info(f"User '{username}' logged out")
        flash('You have been logged out successfully', 'success')
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
    
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """API endpoint for AJAX login"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        remember = data.get('remember', False)
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        # Get user from database
        user = db_manager.get_user_by_username(username)
        
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
        
        # Login user
        login_user(user, remember=remember)
        logger.info(f"User '{username}' logged in via API")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': url_for('index')
        }), 200
        
    except Exception as e:
        logger.error(f"API login error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@auth_bp.route('/signup', methods=['GET'])
def signup_page():
    """Display signup page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('signup.html')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Handle signup form submission"""
    try:
        # Get form data
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([fullname, email, password, confirm_password]):
            flash('Please fill in all fields', 'error')
            return redirect(url_for('auth.signup_page'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.signup_page'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('auth.signup_page'))
        
        # Create username from email (before @)
        username = email.split('@')[0]
        
        # Create user
        user = db_manager.create_user(username, password, email)
        
        if not user:
            flash('Username or email already exists', 'error')
            return redirect(url_for('auth.signup_page'))
        
        # Auto-login after signup
        login_user(user)
        logger.info(f"New user '{username}' signed up and logged in")
        
        flash('Account created successfully! Welcome to PosturePerfect!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        flash('An error occurred during signup', 'error')
        return redirect(url_for('auth.signup_page'))
