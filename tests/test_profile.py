import pytest
from models import db, User

def test_get_profile_success(client, auth_headers):
    response = client.get('/api/profile', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['username'] == 'testuser'
    assert 'stats' in data
    assert data['stats']['total_conversions'] == 0
    assert 'recent_conversions' in data

def test_update_profile_success(client, auth_headers):
    response = client.put('/api/profile', headers=auth_headers, json={
        'username': 'updateduser',
        'email': 'updated@example.com'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['username'] == 'updateduser'
    assert data['user']['email'] == 'updated@example.com'

def test_update_profile_invalid_inputs(client, auth_headers):
    # Short username
    resp = client.put('/api/profile', headers=auth_headers, json={
        'username': 'ab',
        'email': 'test@example.com'
    })
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False

    # Invalid email
    resp = client.put('/api/profile', headers=auth_headers, json={
        'username': 'validname',
        'email': 'invalid-email-format'
    })
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False

    # Empty fields
    resp = client.put('/api/profile', headers=auth_headers, json={
        'username': '',
        'email': ''
    })
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False

def test_update_profile_collisions(client, app, auth_headers):
    # Create another user in DB
    with app.app_context():
        other_user = User(username='otheruser', email='other@example.com', email_verified=True)
        other_user.set_password('password123')
        db.session.add(other_user)
        db.session.commit()

    # Collision on username
    resp = client.put('/api/profile', headers=auth_headers, json={
        'username': 'otheruser',
        'email': 'unique@example.com'
    })
    assert resp.status_code == 409
    assert resp.get_json()['success'] is False

    # Collision on email
    resp = client.put('/api/profile', headers=auth_headers, json={
        'username': 'uniquename',
        'email': 'other@example.com'
    })
    assert resp.status_code == 409
    assert resp.get_json()['success'] is False

def test_change_password_success(client, auth_headers):
    response = client.put('/api/profile/password', headers=auth_headers, json={
        'current_password': 'password123',
        'new_password': 'newsecretpassword'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

def test_change_password_incorrect_current(client, auth_headers):
    response = client.put('/api/profile/password', headers=auth_headers, json={
        'current_password': 'wrongpassword',
        'new_password': 'newsecretpassword'
    })
    assert response.status_code == 401
    assert response.get_json()['success'] is False

def test_change_password_too_short(client, auth_headers):
    response = client.put('/api/profile/password', headers=auth_headers, json={
        'current_password': 'password123',
        'new_password': '123'
    })
    assert response.status_code == 400
    assert response.get_json()['success'] is False

def test_delete_account_requires_password(client, auth_headers):
    # Missing password
    resp = client.delete('/api/profile', headers=auth_headers, json={})
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False

    # Wrong password
    resp = client.delete('/api/profile', headers=auth_headers, json={'current_password': 'wrong'})
    assert resp.status_code == 401
    assert resp.get_json()['success'] is False

def test_delete_account_success(client, auth_headers):
    resp = client.delete('/api/profile', headers=auth_headers, json={'current_password': 'password123'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
