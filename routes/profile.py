import os
import sys

# Add parent directory to sys.path to ensure IDE linters and Flask resolve top-level modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
from flask import Blueprint, request, jsonify
from models import db, User, History, Favorite
from routes.auth import token_required

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Retrieve user profile metadata and statistics."""
    total_conversions = History.query.filter_by(user_id=current_user.id).count()
    
    # Sum character count
    history_records = History.query.filter_by(user_id=current_user.id).all()
    total_characters = sum(item.character_count for item in history_records)
    
    favorite_voices_count = Favorite.query.filter_by(user_id=current_user.id, item_type='voice').count()

    recent_conversions = [
        item.to_dict() for item in History.query.filter_by(user_id=current_user.id)
        .order_by(History.created_at.desc()).limit(5).all()
    ]

    return jsonify({
        'success': True,
        'user': current_user.to_dict(),
        'stats': {
            'total_conversions': total_conversions,
            'total_characters': total_characters,
            'favorite_voices_count': favorite_voices_count,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        },
        'recent_conversions': recent_conversions
    }), 200

@profile_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update user username and/or email address."""
    data = request.get_json() or {}
    new_username = data.get('username', '').strip()
    new_email = data.get('email', '').strip().lower()

    if not new_username or not new_email:
        return jsonify({'success': False, 'message': 'Username and email cannot be empty.'}), 400

    if len(new_username) < 3:
        return jsonify({'success': False, 'message': 'Username must be at least 3 characters long.'}), 400

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, new_email):
        return jsonify({'success': False, 'message': 'Invalid email format.'}), 400

    # Check for username collision
    if new_username != current_user.username:
        if User.query.filter_by(username=new_username).first():
            return jsonify({'success': False, 'message': 'Username is already taken.'}), 409
        current_user.username = new_username

    # Check for email collision
    if new_email != current_user.email:
        if User.query.filter_by(email=new_email).first():
            return jsonify({'success': False, 'message': 'Email address is already in use.'}), 409
        current_user.email = new_email

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Profile updated successfully!',
        'user': current_user.to_dict()
    }), 200

@profile_bp.route('/profile/password', methods=['PUT'])
@token_required
def change_password(current_user):
    """Change current user's password."""
    data = request.get_json() or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Current password and new password are required.'}), 400

    if not current_user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Incorrect current password.'}), 401

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'New password must be at least 6 characters.'}), 400

    current_user.set_password(new_password)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Password updated successfully!'
    }), 200

@profile_bp.route('/profile', methods=['DELETE'])
@token_required
def delete_account(current_user):
    """Permanently delete user account and associated records."""
    db.session.delete(current_user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Account deleted permanently.'
    }), 200
