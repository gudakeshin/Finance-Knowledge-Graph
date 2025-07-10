from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from uuid import uuid4
import os
from pydantic import BaseModel
from typing import Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UploadResponse(BaseModel):
    document_id: str
    status: str
    error: Optional[str] = None

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    try:
        logger.info(f"Upload request received for file: {file.filename}")
        logger.info(f"DATA_DIR: {DATA_DIR}")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        
        contents = await file.read()
        logger.info(f"File size: {len(contents)} bytes")
        
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 50MB limit.")
        
        document_id = str(uuid4())
        doc_dir = os.path.join(DATA_DIR, document_id)
        logger.info(f"Creating directory: {doc_dir}")
        
        os.makedirs(doc_dir, exist_ok=True)
        file_path = os.path.join(doc_dir, file.filename)
        logger.info(f"Saving file to: {file_path}")
        
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        logger.info(f"File saved successfully")
        return UploadResponse(document_id=document_id, status="uploaded")
        
    except Exception as e:
        logger.error(f"Error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
