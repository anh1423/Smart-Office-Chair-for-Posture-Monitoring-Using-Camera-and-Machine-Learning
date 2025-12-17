"""
Main Flask Application for Posture Monitoring System
"""
import os
import logging
from flask import Flask, render_template, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv

# CRITICAL: Load environment variables FIRST, before importing config
load_dotenv()

# Now import config and routes (they will read from environment variables)
import config
from routes.api import api_bp
from routes.auth import auth_bp
from routes.users import users_bp
from routes.admin_analytics import admin_analytics_bp
from routes.battery import battery_bp
from routes.system_management import system_mgmt_bp
from routes.api_keys import api_keys_bp
from database import DBManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_app():
    """
    Application factory function
    
    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config)
    
    # Set secret key for sessions
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'
    login_manager.login_message = 'Please log in to access this page'
    
    # User loader for Flask-Login
    db_manager = DBManager()
    
    @login_manager.user_loader
    def load_user(user_id):
        user = db_manager.get_user_by_id(int(user_id))
        # Reject inactive users
        if user and not user.is_active:
            return None
        return user
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_analytics_bp)
    app.register_blueprint(battery_bp)
    app.register_blueprint(system_mgmt_bp)
    app.register_blueprint(api_keys_bp)
    
    # Main routes (protected)
    @app.route('/')
    @login_required
    def index():
        """Redirect to dashboard"""
        return redirect(url_for('dashboard'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Serve camera dashboard page"""
        return render_template('dashboard.html')
    
    @app.route('/analytics')
    @login_required
    def analytics():
        """Serve analytics page"""
        return render_template('analytics.html')
    
    @app.route('/documents')
    def api_documentation():
        """Serve API documentation page (public)"""
        return render_template('api_docs.html')
    
    @app.route('/api-keys')
    @login_required
    def manage_api_keys():
        """Serve API key management page (admin only)"""
        from flask_login import current_user
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
        return render_template('api_keys.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return {'error': 'Internal server error'}, 500
    
    logger.info("Flask application created successfully")
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    logger.info("="*60)
    logger.info("POSTURE MONITORING WEBSERVER")
    logger.info("="*60)
    logger.info(f"Environment: {config.ENV}")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"Host: {config.HOST}:{config.PORT}")
    logger.info("="*60)
    
    # Run Flask app
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True,
        use_reloader=False  # Disable reloader to prevent camera conflicts
    )
