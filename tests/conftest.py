import os
import tempfile
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from app import create_app
from models import db, User

@pytest.fixture
def app():
    """Create and configure a new Flask app instance for tests."""
    db_fd, db_path = tempfile.mkstemp()
    
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key-that-is-at-least-32-bytes-long-12345',
        'JWT_SECRET_KEY': 'test-jwt-secret-key-that-is-at-least-32-bytes-long-12345',
        'AUDIO_FOLDER': tempfile.mkdtemp(),
        'RATELIMIT_ENABLED': False
    }

    app = create_app('testing')
    app.config.update(test_config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Create a standard test user in the database."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com', email_verified=True)
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

@pytest.fixture
def auth_headers(app, test_user):
    """Generate authorization headers containing a valid JWT token."""
    with app.app_context():
        token_payload = {
            'user_id': test_user.id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
