import os
import sys
import random
import uuid
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

def send_email(to_email, subject, body):
    """
    Sends an email using standard SMTP.
    If SMTP server config is missing, prints the email body to console/log as a fallback.
    """
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_port = current_app.config.get('MAIL_PORT', 587)
    mail_use_tls = current_app.config.get('MAIL_USE_TLS', True)
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    default_sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'no-reply@voxai-studio.local')

    # Dual-mode simulation check
    if not mail_server or not mail_username or not mail_password:
        current_app.logger.info(f"\n[EMAIL SIMULATION] To: {to_email}\nSubject: {subject}\nBody: {body}\n")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = default_sender
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(mail_server, mail_port)
        if mail_use_tls:
            server.starttls()
        server.login(mail_username, mail_password)
        server.sendmail(default_sender, to_email, msg.as_string())
        server.close()
        current_app.logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email}: {e}")
        return False

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

def verification_required(f):
    """Decorator to enforce that the user's email is verified (now disabled)."""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
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

    new_user.email_verified = True
    new_user.verification_code = None

    db.session.add(new_user)
    db.session.commit()

    # Send welcome email
    welcome_body = f"""
    <h2>Welcome to VoxAI Studio! 🎙️✨</h2>
    <p>Hello {username},</p>
    <p>Thank you for registering. We are thrilled to have you at VoxAI Studio!</p>
    <p>You can now start converting your scripts into realistic neural speech across multiple languages.</p>
    <p>Regards,<br>VoxAI Studio Team</p>
    """
    send_email(email, "Welcome to VoxAI Studio! 🎙️✨", welcome_body)

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

@auth_bp.route('/auth/verify-email', methods=['POST'])
@token_required
def verify_email(current_user):
    """Verify the user's email using a 6-digit code."""
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    if not code:
        return jsonify({'success': False, 'message': 'Verification code is required.'}), 400

    if current_user.email_verified:
        return jsonify({'success': True, 'message': 'Email is already verified.'}), 200

    if current_user.verification_code == code:
        current_user.email_verified = True
        current_user.verification_code = None
        db.session.commit()
        
        # Send Welcome Email upon successful verification
        welcome_body = f"""
        <h2>Welcome to VoxAI Studio!</h2>
        <p>Hello {current_user.username},</p>
        <p>Your email address has been successfully verified. Welcome to VoxAI Studio!</p>
        <p>You can now start converting your scripts into realistic neural speech across multiple languages.</p>
        <p>Regards,<br>VoxAI Studio Team</p>
        """
        send_email(current_user.email, "Welcome to VoxAI Studio! 🎙️✨", welcome_body)
        
        return jsonify({'success': True, 'message': 'Email verified successfully!'}), 200

    return jsonify({'success': False, 'message': 'Invalid verification code.'}), 400

@auth_bp.route('/auth/resend-verification', methods=['POST'])
@token_required
def resend_verification(current_user):
    """Regenerate and resend the email verification code."""
    if current_user.email_verified:
        return jsonify({'success': True, 'message': 'Email is already verified.'}), 200

    v_code = str(random.randint(100000, 999999))
    current_user.verification_code = v_code
    db.session.commit()

    email_body = f"""
    <h2>Verify your email address</h2>
    <p>Your new verification code is: <b>{v_code}</b></p>
    <p>Regards,<br>VoxAI Studio Team</p>
    """
    if not send_email(current_user.email, "Verify your email address - VoxAI Studio", email_body):
        return jsonify({'success': False, 'message': 'Failed to resend verification email. Please check your server SMTP settings.'}), 500

    return jsonify({'success': True, 'message': 'Verification code resent successfully.'}), 200



@auth_bp.route('/auth/google', methods=['POST'])
def google_auth():
    """Authenticate user with Google credentials."""
    data = request.get_json() or {}
    credential = data.get('credential')
    if not credential:
        return jsonify({'success': False, 'message': 'Google credential is required.'}), 400

    email = None
    username = None

    # Handle simulation mode for testing
    # Handle simulation mode for testing
    is_simulated = (credential == "simulated_google_token")
    if is_simulated:
        email = data.get('email', 'google-test@example.com').lower()
        username = data.get('username', 'google-test')
        
        # Check if it's one of the preset test accounts
        preset_emails = ["google-test@example.com", "google-dev@example.com"]
        if email not in preset_emails:
            # Block simulated login for existing custom email accounts
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'Simulated Google Sign-In is disabled for existing registered accounts. Please log in using your password.'
                }), 403
    else:
        try:
            resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}", timeout=5)
            if resp.status_code != 200:
                return jsonify({'success': False, 'message': 'Invalid Google ID token.'}), 401
            
            payload = resp.json()
            client_id = current_app.config.get('GOOGLE_CLIENT_ID')
            if client_id and payload.get('aud') != client_id:
                return jsonify({'success': False, 'message': 'Google token audience mismatch.'}), 401

            email = payload.get('email', '').lower()
            username = payload.get('name', email.split('@')[0])
        except Exception as e:
            current_app.logger.error(f"Google auth verification failed: {e}")
            return jsonify({'success': False, 'message': 'Failed to verify Google token.'}), 500

    if not email:
        return jsonify({'success': False, 'message': 'Could not extract email from Google identity.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1

        user = User(username=username, email=email, email_verified=True)
        user.set_password(uuid.uuid4().hex)
        
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email for Google registrations!
        welcome_body = f"""
        <h2>Welcome to VoxAI Studio! 🎙️✨</h2>
        <p>Hello {username},</p>
        <p>Thank you for signing in with Google. We are thrilled to have you at VoxAI Studio!</p>
        <p>You can now start converting your scripts into realistic neural speech across multiple languages.</p>
        <p>Regards,<br>VoxAI Studio Team</p>
        """
        send_email(email, "Welcome to VoxAI Studio! 🎙️✨", welcome_body)
    else:
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
