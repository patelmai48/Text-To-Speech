"""
Profile API tests: GET/PUT /api/profile, PUT /api/profile/password, DELETE /api/profile
"""
import json
# pyrefly: ignore [missing-import]
import pytest
from models import db, User


# ── Helpers ──────────────────────────────────────────────────────────────────

def post_json(client, url, data, headers):
    return client.post(url, data=json.dumps(data), headers=headers)

def put_json(client, url, data, headers):
    return client.put(url, data=json.dumps(data), headers=headers)

def delete_json(client, url, data, headers):
    return client.delete(url, data=json.dumps(data), headers=headers)


# ── GET /api/profile ──────────────────────────────────────────────────────────

def test_get_profile_success(client, auth_headers):
    """Authenticated user can fetch their profile."""
    res = client.get('/api/profile', headers=auth_headers)
    data = res.get_json()
    assert res.status_code == 200
    assert data['success'] is True
    assert 'user' in data
    assert data['user']['username'] == 'testuser'
    assert 'stats' in data
    assert 'total_conversions' in data['stats']


def test_get_profile_unauthorized(client):
    """Missing token returns 401."""
    res = client.get('/api/profile')
    assert res.status_code == 401


# ── PUT /api/profile ──────────────────────────────────────────────────────────

def test_update_profile_success(client, auth_headers):
    """Authenticated user can update their username and email."""
    payload = {'username': 'newusername', 'email': 'newemail@example.com'}
    res = put_json(client, '/api/profile', payload, auth_headers)
    data = res.get_json()
    assert res.status_code == 200
    assert data['success'] is True
    assert data['user']['username'] == 'newusername'
    assert data['user']['email'] == 'newemail@example.com'


def test_update_profile_missing_fields(client, auth_headers):
    """Missing username or email returns 400."""
    res = put_json(client, '/api/profile', {'username': '', 'email': ''}, auth_headers)
    assert res.status_code == 400


def test_update_profile_short_username(client, auth_headers):
    """Username shorter than 3 chars returns 400."""
    res = put_json(client, '/api/profile', {'username': 'ab', 'email': 'test@example.com'}, auth_headers)
    assert res.status_code == 400


def test_update_profile_invalid_email(client, auth_headers):
    """Invalid email format returns 400."""
    res = put_json(client, '/api/profile', {'username': 'testuser', 'email': 'not-an-email'}, auth_headers)
    assert res.status_code == 400


def test_update_profile_username_collision(client, app, auth_headers):
    """Username already taken by another user returns 409."""
    with app.app_context():
        other = User(username='taken', email='taken@example.com', email_verified=True)
        other.set_password('pass123')
        db.session.add(other)
        db.session.commit()

    res = put_json(client, '/api/profile', {'username': 'taken', 'email': 'new@example.com'}, auth_headers)
    assert res.status_code == 409


def test_update_profile_email_collision(client, app, auth_headers):
    """Email already used by another user returns 409."""
    with app.app_context():
        other = User(username='other2', email='other2@example.com', email_verified=True)
        other.set_password('pass123')
        db.session.add(other)
        db.session.commit()

    res = put_json(client, '/api/profile', {'username': 'testuser', 'email': 'other2@example.com'}, auth_headers)
    assert res.status_code == 409


# ── PUT /api/profile/password ─────────────────────────────────────────────────

def test_change_password_success(client, auth_headers):
    """Correct current password allows password change."""
    payload = {'current_password': 'password123', 'new_password': 'newpass456'}
    res = put_json(client, '/api/profile/password', payload, auth_headers)
    data = res.get_json()
    assert res.status_code == 200
    assert data['success'] is True


def test_change_password_wrong_current(client, auth_headers):
    """Wrong current password returns 401."""
    payload = {'current_password': 'wrongpassword', 'new_password': 'newpass456'}
    res = put_json(client, '/api/profile/password', payload, auth_headers)
    assert res.status_code == 401


def test_change_password_too_short(client, auth_headers):
    """New password under 6 characters returns 400."""
    payload = {'current_password': 'password123', 'new_password': '123'}
    res = put_json(client, '/api/profile/password', payload, auth_headers)
    assert res.status_code == 400


def test_change_password_missing_fields(client, auth_headers):
    """Missing fields in password change returns 400."""
    res = put_json(client, '/api/profile/password', {}, auth_headers)
    assert res.status_code == 400


# ── DELETE /api/profile ───────────────────────────────────────────────────────

def test_delete_account_no_password(client, auth_headers):
    """DELETE without current_password returns 400."""
    res = delete_json(client, '/api/profile', {}, auth_headers)
    assert res.status_code == 400


def test_delete_account_wrong_password(client, auth_headers):
    """DELETE with wrong password returns 401."""
    res = delete_json(client, '/api/profile', {'current_password': 'wrongpass'}, auth_headers)
    assert res.status_code == 401


def test_delete_account_success(client, auth_headers):
    """DELETE with correct password removes the account."""
    res = delete_json(client, '/api/profile', {'current_password': 'password123'}, auth_headers)
    data = res.get_json()
    assert res.status_code == 200
    assert data['success'] is True
