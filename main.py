from typing import Literal
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.core import ALLOWED_ORIGINS, enabled
from app.services import load_image, read_text, describe_image, detect_objects

app = FastAPI(title='SightMate API', version='1.0.0', description='Accessible image assistance: captions, OCR, object detection.')
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=False, allow_methods=['GET','POST'], allow_headers=['*'])

class DetectedObject(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
class AnalysisResponse(BaseModel):
    success: bool = True
    mode: Literal['scene_description','read_text','identify_object']
    description: str | None = None
    extracted_text: str | None = None
    objects: list[DetectedObject] = []
    warnings: list[str] = []

def service_error(exc: RuntimeError):
    return HTTPException(status_code=503, detail=str(exc))

@app.get('/')
def root(): return {'name':'SightMate API','docs':'/docs','health':'/health'}

@app.get('/health')
def health():
    try:
        import pytesseract
        ocr_python_package = True
    except ImportError: ocr_python_package = False
    try:
        import ultralytics
        detector_package = True
    except ImportError: detector_package = False
    try:
        import transformers, torch
        caption_package = True
    except ImportError: caption_package = False
    return {'status':'ok','service':'SightMate API','capabilities':{'ocr_python_package':ocr_python_package,'object_detection_enabled':enabled('ENABLE_OBJECT_DETECTION'),'object_detection_package':detector_package,'captioning_enabled':enabled('ENABLE_CAPTIONING'),'captioning_package':caption_package},'note':'OCR also requires the Tesseract executable. Optional models may download weights on first use.'}

@app.post('/api/analyze-image', response_model=AnalysisResponse)
async def analyze_image(image: UploadFile = File(...), mode: str = Form(...)):
    if mode not in {'scene_description','read_text','identify_object'}:
        raise HTTPException(422, 'Unsupported mode. Use scene_description, read_text, or identify_object.')
    img = await load_image(image)
    if mode == 'read_text':
        try: text, warnings = read_text(img)
        except RuntimeError as exc: raise service_error(exc)
        return AnalysisResponse(mode=mode, extracted_text=text, warnings=warnings)
    if mode == 'identify_object':
        try: objects = detect_objects(img)
        except RuntimeError as exc: raise service_error(exc)
        warnings = [] if objects else ['No objects were detected above the confidence threshold.']
        warnings.append('Object detection may miss objects or return incorrect labels.')
        return AnalysisResponse(mode=mode, objects=objects, warnings=warnings)
    try: description = describe_image(img)
    except RuntimeError as exc: raise service_error(exc)
    return AnalysisResponse(mode=mode, description=description, warnings=['AI-generated descriptions may be incomplete or incorrect. Do not use this result for safety-critical navigation.'])

@app.post('/api/read-text', response_model=AnalysisResponse)
async def read_text_endpoint(image: UploadFile = File(...)):
    img = await load_image(image)
    try: text, warnings = read_text(img)
    except RuntimeError as exc: raise service_error(exc)
    return AnalysisResponse(mode='read_text', extracted_text=text, warnings=warnings)

@app.post('/api/detect-objects', response_model=AnalysisResponse)
async def detect_objects_endpoint(image: UploadFile = File(...)):
    img = await load_image(image)
    try: objects = detect_objects(img)
    except RuntimeError as exc: raise service_error(exc)
    return AnalysisResponse(mode='identify_object', objects=objects, warnings=[] if objects else ['No objects were detected above the confidence threshold.'])
