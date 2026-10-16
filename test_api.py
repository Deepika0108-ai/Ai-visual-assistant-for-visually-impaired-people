from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app import main

client = TestClient(app)

def png():
    b = BytesIO(); Image.new('RGB', (80, 60), 'white').save(b, format='PNG'); return b.getvalue()

def test_health():
    r = client.get('/health'); assert r.status_code == 200 and r.json()['status'] == 'ok'

def test_unsupported_type():
    r = client.post('/api/analyze-image', data={'mode':'read_text'}, files={'image':('x.txt', b'hello','text/plain')})
    assert r.status_code == 415

def test_bad_image():
    r = client.post('/api/analyze-image', data={'mode':'read_text'}, files={'image':('x.png', b'bad','image/png')})
    assert r.status_code == 400

def test_bad_mode():
    r = client.post('/api/analyze-image', data={'mode':'other'}, files={'image':('x.png', png(),'image/png')})
    assert r.status_code == 422

def test_ocr_shape(monkeypatch):
    monkeypatch.setattr(main, 'read_text', lambda image: ('Hello SightMate', []))
    r = client.post('/api/read-text', files={'image':('x.png', png(),'image/png')})
    assert r.status_code == 200 and r.json()['extracted_text'] == 'Hello SightMate'

def test_detector_service_error(monkeypatch):
    def fail(image): raise RuntimeError('Object detector unavailable for test')
    monkeypatch.setattr(main, 'detect_objects', fail)
    r = client.post('/api/detect-objects', files={'image':('x.png', png(),'image/png')})
    assert r.status_code == 503 and 'unavailable' in r.json()['detail']
