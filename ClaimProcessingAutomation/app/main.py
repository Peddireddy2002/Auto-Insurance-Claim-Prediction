from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from . import ocr, llm_agent, validator, routing, user_history
import shutil
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...), user_id: str = Form(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    user_history.log_upload(user_id, file.filename)
    return {"filename": file.filename, "path": file_path}

@app.post("/extract/")
async def extract_text(file_path: str = Form(...)):
    text = ocr.extract_text_from_pdf(file_path)
    return {"text": text}

@app.post("/convert_to_json/")
async def convert_to_json(text: str = Form(...)):
    json_data = llm_agent.text_to_json(text)
    return json_data

@app.post("/validate/")
async def validate_claim(data: dict):
    is_valid, errors = validator.validate_claim(data)
    return {"is_valid": is_valid, "errors": errors}

@app.post("/route_payment/")
async def route_payment(data: dict):
    result = routing.route_to_stripe(data)
    return result