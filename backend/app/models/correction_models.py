from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

class CorrectionType(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    SUGGESTED = "suggested"

class CorrectionStrategyEnum(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    UPDATE = "update"
    FORMAT = "format"
    CONVERT = "convert"
    ADJUST = "adjust"
    NORMALIZE = "normalize"
    STANDARDIZE = "standardize"
    VALIDATE = "validate"
    ENRICH = "enrich"
    DEDUPLICATE = "deduplicate"
    MERGE = "merge"
    SPLIT = "split"
    TRANSFORM = "transform"
    CALCULATE = "calculate"
    INFER = "infer"
    VALIDATE_FORMAT = "validate_format"
    VALIDATE_RANGE = "validate_range"
    VALIDATE_PATTERN = "validate_pattern"
    VALIDATE_RELATIONSHIP = "validate_relationship"
    VALIDATE_CONSISTENCY = "validate_consistency"
    VALIDATE_COMPLETENESS = "validate_completeness"
    VALIDATE_ACCURACY = "validate_accuracy"
    VALIDATE_TIMELINESS = "validate_timeliness"
    VALIDATE_UNIQUENESS = "validate_uniqueness"
    VALIDATE_INTEGRITY = "validate_integrity"
    VALIDATE_CONFORMITY = "validate_conformity"
    VALIDATE_BUSINESS_RULES = "validate_business_rules"

class CorrectionStrategy(BaseModel):
    strategy_id: str
    name: str
    description: str
    correction_type: CorrectionType
    parameters: Dict[str, Any]
    priority: int = 0
    is_active: bool = True 