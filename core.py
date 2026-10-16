import os

MAX_UPLOAD_MB = max(1, min(int(os.getenv('MAX_UPLOAD_MB', '10')), 25))
ALLOWED_ORIGINS = [x.strip() for x in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]

def enabled(name: str) -> bool:
    return os.getenv(name, 'false').lower() in {'true', '1', 'yes', 'on'}
