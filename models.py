from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_code = db.Column(db.String(32), nullable=True)
    reset_code = db.Column(db.String(32), nullable=True)
    reset_code_expiry = db.Column(db.DateTime, nullable=True)

    # Relationships
    histories = db.relationship('History', backref='user', lazy=True, cascade="all, delete-orphan")
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade="all, delete-orphan")
    summaries = db.relationship('Summary', backref='user', lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_password(self, password):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Return dict representation of User."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'email_verified': self.email_verified,
            'created_at': self.created_at.replace(tzinfo=timezone.utc).isoformat() if self.created_at else None,
            'last_login': self.last_login.replace(tzinfo=timezone.utc).isoformat() if self.last_login else None
        }

class History(db.Model):
    __tablename__ = 'histories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), nullable=False, default='en')
    voice = db.Column(db.String(50), nullable=False, default='en-us-female')
    speed = db.Column(db.Float, default=1.0)
    pitch = db.Column(db.Float, default=1.0)
    volume = db.Column(db.Float, default=1.0)
    audio_filename = db.Column(db.String(255), nullable=True)
    character_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        """Return dict representation of History item."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'text': self.text,
            'language': self.language,
            'voice': self.voice,
            'speed': self.speed,
            'pitch': self.pitch,
            'volume': self.volume,
            'audio_filename': self.audio_filename,
            'audio_url': f'/static/audio/{self.audio_filename}' if self.audio_filename else None,
            'character_count': self.character_count,
            'created_at': self.created_at.replace(tzinfo=timezone.utc).isoformat() if self.created_at else None
        }

class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'voice' or 'language'
    item_value = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        """Return dict representation of Favorite item."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'item_type': self.item_type,
            'item_value': self.item_value,
            'created_at': self.created_at.replace(tzinfo=timezone.utc).isoformat() if self.created_at else None
        }

class Summary(db.Model):
    __tablename__ = 'summaries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    original_topic = db.Column(db.Text, nullable=False)
    summary_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        """Return dict representation of Summary item."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_topic': self.original_topic,
            'summary_content': self.summary_content,
            'created_at': self.created_at.replace(tzinfo=timezone.utc).isoformat() if self.created_at else None
        }

