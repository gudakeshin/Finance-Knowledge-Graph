from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class ValidationSummary(BaseModel):
    total_rules: int
    passed_rules: int
    failed_rules: int
    warnings: int
    errors: int
    info: int
    summary_details: Optional[Dict[str, Any]] = None

class CorrectionSummary(BaseModel):
    total_corrections: int
    successful_corrections: int
    failed_corrections: int
    manual_corrections: int
    auto_corrections: int
    summary_details: Optional[Dict[str, Any]] = None

class BatchSummary(BaseModel):
    batch_id: str
    total_documents: int
    processed_documents: int
    failed_documents: int
    start_time: datetime
    end_time: Optional[datetime] = None
    summary_details: Optional[Dict[str, Any]] = None 