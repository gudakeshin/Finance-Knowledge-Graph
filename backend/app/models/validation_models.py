from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationRule(BaseModel):
    rule_id: str
    description: str
    severity: ValidationSeverity
    condition: Dict[str, Any]
    correction_strategy: Optional[Dict[str, Any]] = None

class ValidationResult(BaseModel):
    rule_id: str
    is_valid: bool
    message: str
    severity: ValidationSeverity
    details: Optional[Dict[str, Any]] = None
    suggested_corrections: Optional[List[Dict[str, Any]]] = None 