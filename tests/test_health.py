import pytest

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'

def test_404_not_found(client):
    response = client.get('/api/non-existent-endpoint-123')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert 'message' in data
