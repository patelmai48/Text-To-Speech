import os
from datetime import timedelta
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base Configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-default-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "database.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Audio uploads configuration
    AUDIO_FOLDER = os.path.join(BASE_DIR, 'static', 'audio')
    MAX_TEXT_LENGTH = 3000

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
