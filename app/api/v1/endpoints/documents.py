"""Document management endpoints"""
from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter()

@router.get("/")
async def list_documents(current_user = Depends(get_current_user)):
    """List documents"""
    return {"message": "List documents endpoint"}

@router.post("/upload")
async def upload_document(current_user = Depends(get_current_user)):
    """Upload document"""
    return {"message": "Upload document endpoint"}
