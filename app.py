import os
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
from config import config_by_name
from models import db
from routes.auth import auth_bp
from routes.tts import tts_bp
from routes.profile import profile_bp

def create_app(config_name=None):
    """Application factory for Flask app."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_by_name[config_name])

    # Ensure audio output directory exists
    os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register API Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(tts_bp, url_prefix='/api')
    app.register_blueprint(profile_bp, url_prefix='/api')

    # Frontend Page Routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/register')
    def register_page():
        return render_template('register.html')

    # Serve generated audio files directly if requested via /static/audio/<filename>
    @app.route('/static/audio/<filename>')
    def serve_audio(filename):
        return send_from_directory(app.config['AUDIO_FOLDER'], filename)

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'success': False, 'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An internal server error occurred'}), 500

    # Initialize Database Tables
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
