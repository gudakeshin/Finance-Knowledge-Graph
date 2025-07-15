from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import List, Dict, Any, Optional
import uuid
import os
import json
from pathlib import Path
import shutil
from datetime import datetime
import logging
import hashlib

from app.services.entity_recognition import FinancialEntityRecognizer
from app.services.document_processing import DocumentProcessor
from app.services.llm_document_classifier import IntelligentDocumentClassifier, DocumentType
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/extraction", tags=["extraction"])

# Initialize services
try:
    entity_recognizer = FinancialEntityRecognizer()
    document_processor = DocumentProcessor()
    document_classifier = IntelligentDocumentClassifier()
    logger.info("Extraction services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize extraction services: {e}")
    entity_recognizer = None
    document_processor = None
    document_classifier = None

@router.post("/extract")
async def extract_document_data(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Extract structured data from uploaded document
    """
    if not entity_recognizer or not document_processor or not document_classifier:
        raise HTTPException(
            status_code=503,
            detail="Document extraction services are not available. Please try again later."
        )
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/') and file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=400, 
                detail="Only image files (PNG, JPG, JPEG) and PDF files are supported"
            )
        
        # Create unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix if file.filename else '.pdf'
        filename = f"{file_id}{file_extension}"
        
        # Save file to uploads directory
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Log file details
        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            file_md5 = hashlib.md5(file_bytes).hexdigest()
        logger.info(f"Uploaded file: {file.filename}, Saved as: {filename}, Size: {file_size} bytes, MD5: {file_md5}")
        
        # Process document
        try:
            # Extract text and entities
            extracted_text = document_processor.extract_text(str(file_path))
            logger.info(f"Extracted text (first 500 chars): {extracted_text[:500]}")
            entities = entity_recognizer.extract_entities(extracted_text)
            
            # Convert entities to serializable format for logging
            entities_summary = [{"type": entity.type, "text": entity.text[:50], "confidence": entity.confidence} for entity in entities[:5]]
            logger.info(f"Entities found: {len(entities)} entities, first 5: {entities_summary}")
            
            # Intelligently classify document and create dynamic schema
            doc_type, suggested_schema, classification_confidence, reasoning = document_classifier.classify_and_schema_document(extracted_text, entities)
            logger.info(f"Document classified as: {doc_type.value} with confidence: {classification_confidence}")
            logger.info(f"Classification reasoning: {reasoning}")
            logger.info(f"Dynamic schema created: {suggested_schema.name}")
            
            # Map entities to schema fields using LLM intelligence
            extraction_results = []
            
            # Convert entities to JSON-serializable format
            entities_dict = []
            for entity in entities[:20]:  # Limit to first 20 entities
                entities_dict.append({
                    "text": entity.text,
                    "type": entity.type,
                    "confidence": entity.confidence,
                    "start": entity.position.get("start", 0),
                    "end": entity.position.get("end", 0),
                    "page": entity.page,
                    "id": entity.id
                })
            
            # Create a mapping prompt for the LLM
            mapping_prompt = f"""
You are an expert at mapping extracted entities to appropriate schema fields.

Document type: {doc_type.value}
Schema: {suggested_schema.name}
Schema fields: {json.dumps(suggested_schema.fields, indent=2)}

Extracted entities:
{json.dumps(entities_dict, indent=2)}

Map each entity to the most appropriate schema field. Consider:
1. Entity type and value
2. Schema field requirements
3. Context and meaning

Respond in JSON format with mapped fields:
{{
    "mapped_fields": [
        {{
            "field": "Field Name",
            "key": "field_key",
            "value": "extracted_value",
            "confidence": 0.85,
            "entity_type": "original_entity_type",
            "schema_field": "schema_field_name",
            "required": true/false
        }}
    ]
}}

Only respond with valid JSON.
"""
            
            # Get LLM mapping
            mapping_response = document_classifier._call_ollama(mapping_prompt)
            
            try:
                if mapping_response and mapping_response.strip():
                    # Clean up the response
                    mapping_response = mapping_response.strip()
                    if mapping_response.startswith("```json"):
                        mapping_response = mapping_response[7:]
                    if mapping_response.endswith("```"):
                        mapping_response = mapping_response[:-3]
                    mapping_response = mapping_response.strip()
                    
                    mapping_result = json.loads(mapping_response)
                    mapped_fields = mapping_result.get("mapped_fields", [])
                    
                    for field in mapped_fields:
                        extraction_results.append({
                            "field": field.get("field", "Unknown"),
                            "key": field.get("key", "unknown"),
                            "value": field.get("value", ""),
                            "confidence": field.get("confidence", 0.0),
                            "entity_type": field.get("entity_type", ""),
                            "schema_field": field.get("schema_field", ""),
                            "required": field.get("required", False)
                        })
                        
                else:
                    # Fallback to basic mapping if LLM fails
                    logger.warning("LLM mapping failed, using fallback mapping")
                    for entity in entities[:10]:  # Limit to first 10 entities
                        extraction_results.append({
                            "field": entity.type.replace('_', ' ').title(),
                            "key": entity.type.lower(),
                            "value": entity.text,
                            "confidence": entity.confidence,
                            "entity_type": entity.type,
                            "schema_field": "",
                            "required": False
                        })
                        
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Failed to parse LLM mapping response: {e}")
                # Fallback to basic mapping
                for entity in entities[:10]:
                    extraction_results.append({
                        "field": entity.type.replace('_', ' ').title(),
                        "key": entity.type.lower(),
                        "value": entity.text,
                        "confidence": entity.confidence,
                        "entity_type": entity.type,
                        "schema_field": "",
                        "required": False
                    })
            
            # If no entities mapped to schema, add raw entities as fallback
            if not extraction_results:
                for entity in entities:
                    extraction_results.append({
                        "field": entity.type.replace('_', ' ').title(),
                        "key": entity.type.lower(),
                        "value": entity.text,
                        "confidence": entity.confidence,
                        "entity_type": entity.type,
                        "schema_field": None,
                        "required": False
                    })
            
            # Return text preview instead of entity extraction results
            extraction_results = []
            if extracted_text:
                # Split text into chunks for better display
                text_chunks = [extracted_text[i:i+500] for i in range(0, len(extracted_text), 500)]
                for i, chunk in enumerate(text_chunks[:3]):  # Limit to first 3 chunks
                    extraction_results.append({
                        "field": f"Text Preview {i+1}",
                        "key": f"text_preview_{i+1}",
                        "value": chunk,
                        "confidence": 1.0,
                        "entity_type": "TEXT_PREVIEW",
                        "schema_field": "document_summary",
                        "required": False
                    })
            
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return {
                "success": True,
                "file_id": file_id,
                "filename": file.filename,
                "document_classification": {
                    "type": doc_type.value,
                    "confidence": classification_confidence,
                    "suggested_schema": {
                        "name": suggested_schema.name,
                        "description": suggested_schema.description,
                        "fields": suggested_schema.fields
                    }
                },
                "extraction_results": extraction_results,
                "total_fields": len(extraction_results),
                "high_confidence_count": len([r for r in extraction_results if r["confidence"] >= 0.8])
            }
            
        except Exception as e:
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/document-types")
async def get_document_types():
    """
    Get available document types and their schemas
    """
    if not document_classifier:
        raise HTTPException(
            status_code=503,
            detail="Document classification service is not available"
        )
    
    document_types = document_classifier.get_available_document_types()
    
    return {
        "document_types": document_types,
        "total_types": len(document_types)
    }

@router.get("/fields")
async def get_extraction_fields():
    """
    Get available extraction fields
    """
    return {
        "fields": [
            {
                "name": "Invoice Number",
                "key": "invoice_number",
                "description": "Invoice or document number",
                "examples": ["INV-2024-001", "DOC-12345"]
            },
            {
                "name": "Date",
                "key": "date",
                "description": "Document date",
                "examples": ["2024-01-15", "15/01/2024"]
            },
            {
                "name": "Amount",
                "key": "amount",
                "description": "Total amount or sum",
                "examples": ["$1,250.00", "1250.00"]
            },
            {
                "name": "Vendor",
                "key": "vendor",
                "description": "Vendor or supplier name",
                "examples": ["ABC Corporation", "XYZ Ltd"]
            },
            {
                "name": "Customer",
                "key": "customer",
                "description": "Customer or client name",
                "examples": ["John Doe", "Company ABC"]
            },
            {
                "name": "Description",
                "key": "description",
                "description": "Item or service description",
                "examples": ["Consulting Services", "Product XYZ"]
            }
        ]
    }

@router.get("/status/{file_id}")
async def get_extraction_status(file_id: str):
    """
    Get extraction status for a file
    """
    # This would typically check against a database or cache
    # For now, return a mock response
    return {
        "file_id": file_id,
        "status": "completed",
        "progress": 100,
        "message": "Extraction completed successfully"
    } 

@router.get("/logs", response_class=PlainTextResponse)
async def get_backend_logs(lines: int = 100):
    """
    Return the last N lines of the backend log file.
    """
    log_path = os.path.join(os.path.dirname(__file__), '../../logs/backend.log')
    try:
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except Exception as e:
        return f"Error reading log file: {e}" 