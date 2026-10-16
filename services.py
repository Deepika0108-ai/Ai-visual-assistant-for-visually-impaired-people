from io import BytesIO
import os
from PIL import Image, ImageOps, ImageEnhance, UnidentifiedImageError
from fastapi import HTTPException, UploadFile
from app.core import MAX_UPLOAD_MB, enabled

ALLOWED_MIME = {'image/jpeg', 'image/png', 'image/webp', 'image/bmp'}

async def load_image(upload: UploadFile) -> Image.Image:
    if (upload.content_type or '').lower() not in ALLOWED_MIME:
        raise HTTPException(415, 'Unsupported image type. Upload JPEG, PNG, WEBP, or BMP.')
    data = await upload.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if not data:
        raise HTTPException(400, 'The uploaded file is empty.')
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f'Image exceeds the {MAX_UPLOAD_MB} MB upload limit.')
    try:
        image = Image.open(BytesIO(data)); image.verify()
        image = Image.open(BytesIO(data))
        if image.format not in {'JPEG', 'PNG', 'WEBP', 'BMP'}:
            raise HTTPException(415, 'File content is not a supported image.')
        if image.width * image.height > 25_000_000:
            raise HTTPException(413, 'Image dimensions are too large. Choose a smaller image.')
        image.load()
        return image.convert('RGB')
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(400, 'Could not decode a valid, safe image.')

def read_text(image: Image.Image) -> tuple[str, list[str]]:
    import pytesseract
    cmd = os.getenv('TESSERACT_CMD', '').strip()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    try:
        prepared = ImageEnhance.Contrast(ImageOps.grayscale(image)).enhance(1.5)
        text = pytesseract.image_to_string(prepared, config='--psm 6').strip()
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError('Tesseract OCR is not installed or not on PATH. Install it and restart the backend.') from exc
    except Exception as exc:
        raise RuntimeError('OCR could not process this image. Try a sharper, well-lit image.') from exc
    return text, ([] if text else ['No readable text detected. Try a closer, sharper image with better lighting.'])

_caption_processor = _caption_model = _yolo_model = None

def describe_image(image: Image.Image) -> str:
    global _caption_processor, _caption_model
    if not enabled('ENABLE_CAPTIONING'):
        raise RuntimeError('Scene captioning is disabled. Install requirements-vision.txt and set ENABLE_CAPTIONING=true.')
    try:
        import torch
        from transformers import BlipProcessor, BlipForConditionalGeneration
    except ImportError as exc:
        raise RuntimeError('Captioning dependencies missing. Run pip install -r requirements-vision.txt.') from exc
    model_name = os.getenv('CAPTION_MODEL', 'Salesforce/blip-image-captioning-base')
    if _caption_processor is None:
        _caption_processor = BlipProcessor.from_pretrained(model_name)
        _caption_model = BlipForConditionalGeneration.from_pretrained(model_name).eval()
    inputs = _caption_processor(images=image, return_tensors='pt')
    with torch.inference_mode():
        output = _caption_model.generate(**inputs, max_new_tokens=45)
    caption = _caption_processor.decode(output[0], skip_special_tokens=True).strip()
    if not caption:
        raise RuntimeError('The caption model returned no description. Try another image.')
    return caption

def detect_objects(image: Image.Image) -> list[dict]:
    global _yolo_model
    if not enabled('ENABLE_OBJECT_DETECTION'):
        raise RuntimeError('Object detection is disabled. Install requirements-vision.txt and set ENABLE_OBJECT_DETECTION=true.')
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError('Object detection dependencies missing. Run pip install -r requirements-vision.txt.') from exc
    if _yolo_model is None:
        _yolo_model = YOLO(os.getenv('YOLO_MODEL', 'yolov8n.pt'))
    results = _yolo_model.predict(source=image, verbose=False, conf=0.35)
    items = []
    if results and results[0].boxes is not None:
        result = results[0]
        for box in result.boxes:
            idx = int(box.cls[0].item())
            items.append({'label': str(result.names[idx]), 'confidence': round(float(box.conf[0].item()), 4)})
    return items
