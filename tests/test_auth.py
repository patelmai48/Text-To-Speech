# pyrefly: ignore [missing-import]
import pytest

def test_register_success(client):
    response = client.post('/api/register', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert 'token' in data
    assert data['user']['username'] == 'newuser'

def test_register_missing_fields(client):
    response = client.post('/api/register', json={
        'username': 'newuser'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

def test_register_duplicate_username(client, test_user):
    response = client.post('/api/register', json={
        'username': 'testuser',
        'email': 'unique@example.com',
        'password': 'password123'
    })
    assert response.status_code == 409
    data = response.get_json()
    assert data['success'] is False

def test_login_success(client, test_user):
    response = client.post('/api/login', json={
        'email_or_username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'token' in data

def test_login_invalid_password(client, test_user):
    response = client.post('/api/login', json={
        'email_or_username': 'testuser',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    data = response.get_json()
    assert data['success'] is False

def test_get_me_success(client, auth_headers):
    response = client.get('/api/me', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['username'] == 'testuser'

def test_get_me_unauthorized(client):
    response = client.get('/api/me')
    assert response.status_code == 401

def test_forgot_and_reset_password(client, test_user):
    # Request password reset code
    forgot_resp = client.post('/api/auth/forgot-password', json={
        'email': 'test@example.com'
    })
    assert forgot_resp.status_code == 200
    forgot_data = forgot_resp.get_json()
    assert forgot_data['success'] is True
    dev_code = forgot_data.get('dev_code')

    if dev_code:
        # Test reset password using dev code
        reset_resp = client.post('/api/auth/reset-password', json={
            'email': 'test@example.com',
            'code': dev_code,
            'new_password': 'newpassword123'
        })
        assert reset_resp.status_code == 200
        assert reset_resp.get_json()['success'] is True

        # Test login with new password
        login_resp = client.post('/api/login', json={
            'email_or_username': 'testuser',
            'password': 'newpassword123'
        })
        assert login_resp.status_code == 200

def test_google_auth_simulation(client, test_user):
    # Non-existing user attempt should fail with 404
    fail_resp = client.post('/api/auth/google', json={
        'credential': 'simulated_google_token',
        'email': 'nonexistent@example.com'
    })
    assert fail_resp.status_code == 404
    assert fail_resp.get_json()['success'] is False

    # Existing user attempt should succeed
    success_resp = client.post('/api/auth/google', json={
        'credential': 'simulated_google_token',
        'email': 'test@example.com'
    })
    assert success_resp.status_code == 200
    data = success_resp.get_json()
    assert data['success'] is True
    assert 'token' in data

def test_refresh_token_success(client, auth_headers):
    response = client.post('/api/auth/refresh', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'token' in data
    assert data['user']['username'] == 'testuser'

def test_verify_email_already_verified(client, auth_headers):
    response = client.post('/api/auth/verify-email', headers=auth_headers, json={'code': '123456'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'already verified' in data['message'].lower()

