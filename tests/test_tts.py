import pytest

def test_get_voices(client):
    response = client.get('/api/voices')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'voices' in data
    assert len(data['voices']) > 0

def test_tts_synthesis(client, auth_headers):
    response = client.post('/api/tts', json={
        'text': 'Hello world! Welcome to VoxAI Studio.',
        'language': 'en',
        'voice': 'en-us-female',
        'speed': 1.0,
        'pitch': 1.0,
        'volume': 1.0
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert 'history' in data
    assert 'id' in data['history']
    assert 'audio_url' in data['history']

def test_tts_summarize(client, auth_headers):
    response = client.post('/api/tts/summarize', json={
        'text': 'Artificial intelligence is transforming technology worldwide.',
        'mode': 'condense'
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'summary' in data

def test_get_history(client, auth_headers):
    # First generate a speech history item
    client.post('/api/tts', json={'text': 'Test text'}, headers=auth_headers)

    response = client.get('/api/history', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['history']) >= 1

def test_get_history_pagination(client, auth_headers):
    for i in range(3):
        client.post('/api/tts', json={'text': f'Paginated text item {i}'}, headers=auth_headers)

    response = client.get('/api/history?page=1&per_page=2', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['page'] == 1
    assert data['per_page'] == 2
    assert len(data['history']) == 2
    assert 'total_count' in data

def test_export_history_csv(client, auth_headers):
    client.post('/api/tts', json={'text': 'Export test'}, headers=auth_headers)
    response = client.get('/api/history/export/csv', headers=auth_headers)
    assert response.status_code == 200
    assert response.content_type == 'text/csv; charset=utf-8'

def test_export_history_pdf(client, auth_headers):
    client.post('/api/tts', json={'text': 'Export PDF test'}, headers=auth_headers)
    response = client.get('/api/history/export/pdf', headers=auth_headers)
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'

def test_favorites_crud(client, auth_headers):
    # Add favorite
    add_resp = client.post('/api/favorites', json={
        'item_type': 'voice',
        'item_value': 'en-us-female'
    }, headers=auth_headers)
    assert add_resp.status_code == 201
    fav_id = add_resp.get_json()['favorite']['id']

    # Get favorites
    get_resp = client.get('/api/favorites', headers=auth_headers)
    assert get_resp.status_code == 200
    assert len(get_resp.get_json()['favorites']) >= 1

    # Delete favorite
    del_resp = client.delete(f'/api/favorites/{fav_id}', headers=auth_headers)
    assert del_resp.status_code == 200
