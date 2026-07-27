import os
import sys

# Add parent directory to sys.path to ensure IDE linters and Flask resolve top-level modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# pyrefly: ignore [missing-import]
import jwt
import re
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from models import db, User

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """Decorator to enforce JWT token authorization on protected API routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'success': False, 'message': 'Authentication token is missing!'}), 401

        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            current_user = db.session.get(User, payload['user_id'])
            if not current_user:
                return jsonify({'success': False, 'message': 'User associated with token not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired. Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token. Authorization denied.'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account."""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Username, email, and password are required.'}), 400

    if len(username) < 3:
        return jsonify({'success': False, 'message': 'Username must be at least 3 characters long.'}), 400

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return jsonify({'success': False, 'message': 'Invalid email address format.'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long.'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username is already taken.'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email address is already registered.'}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    # Generate JWT token upon successful registration
    token_payload = {
        'user_id': new_user.id,
        'exp': datetime.now(timezone.utc) + current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(days=7))
    }
    token = jwt.encode(token_payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'success': True,
        'message': 'Account registered successfully!',
        'token': token,
        'user': new_user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT access token."""
    data = request.get_json() or {}
    email_or_username = data.get('email_or_username', '').strip()
    password = data.get('password', '')

    if not email_or_username or not password:
        return jsonify({'success': False, 'message': 'Please provide email/username and password.'}), 400

    # Match username or email
    user = User.query.filter(
        (User.email == email_or_username.lower()) | (User.username == email_or_username)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid credentials. Please check username/email and password.'}), 401

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    token_payload = {
        'user_id': user.id,
        'exp': datetime.now(timezone.utc) + current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(days=7))
    }
    token = jwt.encode(token_payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'success': True,
        'message': f'Welcome back, {user.username}!',
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def me(current_user):
    """Retrieve details for current authenticated user."""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200
