from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class ValidationHistory(BaseModel):
    history_id: str
    batch_id: str
    document_id: str
    timestamp: datetime
    status: str
    details: Optional[Dict[str, Any]] = None

class CorrectionHistory(BaseModel):
    history_id: str
    batch_id: str
    document_id: str
    timestamp: datetime
    correction_applied: bool
    correction_details: Optional[Dict[str, Any]] = None

class BatchHistory(BaseModel):
    batch_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    processed_documents: int
    failed_documents: int
    metadata: Dict[str, Any] = {} 