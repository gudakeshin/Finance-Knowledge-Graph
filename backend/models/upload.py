from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    document_id: str
    status: str
    error: Optional[str] = None
