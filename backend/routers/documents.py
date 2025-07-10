from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import shutil
import models
import schemas
from database import get_db

router = APIRouter()

# Create (upload)
@router.post("/", response_model=schemas.Document)
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    db_document = models.Document(
        title=document.title,
        content=document.content,
        file_path=document.file_path,
        file_type=document.file_type,
        description=document.description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

# Read (get all)
@router.get("/", response_model=List[schemas.Document])
def get_documents(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search term to filter documents by title"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Document)
    if search:
        query = query.filter(models.Document.title.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

# Read (get one)
@router.get("/{document_id}", response_model=schemas.Document)
def get_document(document_id: int, db: Session = Depends(get_db)):
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

# Update
@router.put("/{document_id}", response_model=schemas.Document)
def update_document(document_id: int, document: schemas.DocumentUpdate, db: Session = Depends(get_db)):
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    for key, value in document.model_dump(exclude_unset=True).items():
        setattr(db_document, key, value)
    
    db_document.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_document)
    return db_document

# Delete
@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(db_document)
    db.commit()
    return {"message": "Document deleted successfully"}

# Download file
@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(doc.path, filename=doc.filename)

# Analytics
@router.get("/analytics")
def document_analytics(db: Session = Depends(get_db)):
    total = db.query(models.Document).count()
    latest = db.query(models.Document).order_by(models.Document.upload_time.desc()).first()
    return {
        "total_documents": total,
        "latest_document": DocumentOut.from_orm(latest) if latest else None
    } 