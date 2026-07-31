import os
from datetime import timedelta
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def _require_secret(env_var, fallback, env_name):
    """Return env var value or fallback secret key."""
    return os.getenv(env_var) or fallback



class Config:
    """Base Configuration"""
    SECRET_KEY = _require_secret('SECRET_KEY', 'default-secret-key-change-in-production', 'FLASK_ENV')
    JWT_SECRET_KEY = _require_secret('JWT_SECRET_KEY', 'jwt-default-secret-key-change-in-production', 'FLASK_ENV')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # SQLAlchemy database configuration
    _db_url = os.getenv('DATABASE_URL')
    if _db_url and _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url or f'sqlite:///{os.path.join(BASE_DIR, "database.db")}'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    } if 'postgresql' in SQLALCHEMY_DATABASE_URI else {}

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Audio uploads configuration
    AUDIO_FOLDER = os.path.join(BASE_DIR, 'static', 'audio')
    MAX_TEXT_LENGTH = 5000

    # SMTP configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # Google Sign-in Client ID
    _raw_google_id = os.getenv('GOOGLE_CLIENT_ID', '593348183512-bi8t063tk73uesvqd6j643btukr8uia4.apps.googleusercontent.com')
    GOOGLE_CLIENT_ID = _raw_google_id.strip().replace('\n', '').replace('\r', '') if _raw_google_id else None

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    PRESERVE_CONTEXT_ON_EXCEPTION = False

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
