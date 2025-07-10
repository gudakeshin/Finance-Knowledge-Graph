from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.post("/process")
async def process_data(data: Dict[str, Any]):
    """Process financial data and update the knowledge graph"""
    try:
        # TODO: Implement data processing logic
        return {"status": "success", "message": "Data processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    """Get the current processing status"""
    try:
        # TODO: Implement status checking logic
        return {"status": "idle"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 