import os
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS
# pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]
from flask_limiter import Limiter
# pyrefly: ignore [missing-import]
from flask_limiter.util import get_remote_address
# pyrefly: ignore [missing-import]
from flask_migrate import Migrate
# pyrefly: ignore [missing-import]
from flask_talisman import Talisman

from config import config_by_name
from models import db
from routes.auth import auth_bp
from routes.tts import tts_bp
from routes.profile import profile_bp
from services.keep_alive import start_keep_alive

def create_app(config_name=None):
    """Application factory for Flask app."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_by_name[config_name])

    # Ensure audio output directory exists
    os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

    # Initialize Extensions
    db.init_app(app)
    Migrate(app, db)

    # Security Headers & Content Security Policy (Talisman)
    # Disabled force_https in testing/development environments
    is_testing = config_name == 'testing' or app.config.get('TESTING', False)
    csp = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://accounts.google.com", "https://cdn.jsdelivr.net"],
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"],
        'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", "data:"],
        'img-src': ["'self'", "data:", "https://*"],
        'connect-src': ["'self'", "https://*"],
        'frame-src': ["'self'", "https://accounts.google.com"],
        'media-src': ["'self'", "blob:", "data:"]
    }
    Talisman(
        app,
        content_security_policy=csp,
        force_https=not is_testing and not app.debug,
        session_cookie_secure=not is_testing and not app.debug
    )

    # Configurable CORS origins (restricts wildcard * in production)
    raw_origins = os.getenv('ALLOWED_ORIGINS')
    if raw_origins:
        allowed_origins = [origin.strip() for origin in raw_origins.split(',')]
    elif is_testing or app.debug:
        allowed_origins = '*'
    else:
        allowed_origins = ['http://localhost:5000', 'http://127.0.0.1:5000']

    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    # Rate Limiter
    redis_url = os.getenv('REDIS_URL', 'memory://')
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["300 per day", "60 per hour"],
        storage_uri=redis_url
    )

    # Rate limit sensitive API Blueprints
    limiter.limit("15 per minute")(auth_bp)
    limiter.limit("30 per minute")(tts_bp)

    # Register API Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(tts_bp, url_prefix='/api')
    app.register_blueprint(profile_bp, url_prefix='/api')

    # Security Headers Middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Health Check Endpoint for Cloud Orchestrators & Render
    @app.route('/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'disconnected: {e}'
            
        status_code = 200 if db_status == 'connected' else 500
        return jsonify({
            'status': 'healthy' if db_status == 'connected' else 'degraded',
            'database': db_status,
            'service': 'VoxAI Studio'
        }), status_code

    # Configure logging
    import logging
    from logging.handlers import RotatingFileHandler
    logging.basicConfig(level=logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    
    file_handler = RotatingFileHandler('app.log', maxBytes=1024000, backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('VoxAI Studio starting up...')

    # Frontend Page Routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login_page():
        google_credential = None
        try:
            if request.method == 'POST':
                google_credential = request.form.get('credential')
            if not google_credential:
                google_credential = request.args.get('credential')
        except Exception as e:
            app.logger.warning(f"Error reading login credential: {e}")
        return render_template('login.html', google_credential=google_credential)

    @app.route('/register', methods=['GET', 'POST'])
    def register_page():
        google_credential = None
        try:
            if request.method == 'POST':
                google_credential = request.form.get('credential')
            if not google_credential:
                google_credential = request.args.get('credential')
        except Exception as e:
            app.logger.warning(f"Error reading register credential: {e}")
        return render_template('register.html', google_credential=google_credential)

    @app.route('/privacy')
    def privacy_page():
        return render_template('privacy.html')

    @app.route('/terms')
    def terms_page():
        return render_template('terms.html')

    # Serve generated audio files directly if requested via /static/audio/<filename>
    @app.route('/static/audio/<filename>')
    def serve_audio(filename):
        res = send_from_directory(app.config['AUDIO_FOLDER'], filename)
        res.headers['Cache-Control'] = 'public, max-age=86400'
        return res

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 error: {error}")
        return jsonify({'success': False, 'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An internal server error occurred'}), 500

    # Initialize Database Tables
    with app.app_context():
        # Auto-upgrade SQLite schema if columns are missing
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'users' in inspector.get_table_names():
                columns = [c['name'] for c in inspector.get_columns('users')]
                with db.engine.begin() as conn:
                    if 'email_verified' not in columns:
                        conn.execute(db.text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0 NOT NULL"))
                    if 'verification_code' not in columns:
                        conn.execute(db.text("ALTER TABLE users ADD COLUMN verification_code VARCHAR(32)"))
                    if 'reset_code' not in columns:
                        conn.execute(db.text("ALTER TABLE users ADD COLUMN reset_code VARCHAR(32)"))
                    if 'reset_code_expiry' not in columns:
                        conn.execute(db.text("ALTER TABLE users ADD COLUMN reset_code_expiry DATETIME"))
        except Exception as e:
            app.logger.warning(f"Database schema auto-upgrade failed: {e}")

        try:
            db.create_all()
        except Exception as e:
            app.logger.info(f"Database table initialization note: {e}")

    # Start automated 5-minute keep-alive ping thread
    start_keep_alive(app)

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
