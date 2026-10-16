# SightMate — AI Visual Assistant

Student-friendly React + FastAPI prototype for image captions, OCR and object detection.

## Requirements
- Python 3.11+
- Node.js 18+
- OCR requires the Tesseract executable installed separately.
- Object detection and scene captioning are optional models. See `backend/requirements-vision.txt`; first run can download large model weights.

## Run backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Copy .env.example to .env and set values as needed
uvicorn app.main:app --reload --port 8000
```
For OCR, install Tesseract and ensure `tesseract` is on PATH. Windows users can set `TESSERACT_CMD` to the full executable path in the environment.

Optional AI models:
```bash
pip install -r requirements-vision.txt
```
Set `ENABLE_OBJECT_DETECTION=true` and/or `ENABLE_CAPTIONING=true` before starting the backend. The first model run may download weights. Missing capabilities return HTTP 503; no fake inference results are generated.

## Run frontend
In another terminal:
```bash
cd frontend
npm install
# Copy .env.example to .env
npm run dev
```
Open the Vite URL shown in the terminal. Camera access generally requires localhost or HTTPS and permission.

## API
- `GET /health`
- `POST /api/analyze-image` multipart fields `image`, `mode` (`scene_description`, `read_text`, `identify_object`)
- `POST /api/read-text` multipart field `image`
- `POST /api/detect-objects` multipart field `image`
- Swagger docs: `http://localhost:8000/docs`

## Tests
```bash
cd backend
pip install -r requirements.txt
pytest -q
```
Tests use service stubs where needed and validate API shape, input validation and errors; they do not measure model accuracy.

## Safety and privacy
Uploads are processed in memory and are not saved by default. AI can misread text or misidentify objects. Do not rely on this prototype for road crossing, hazard detection or safety-critical navigation. It does not replace a white cane, guide dog or orientation training.
