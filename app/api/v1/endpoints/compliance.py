"""Compliance management endpoints"""
from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter()

@router.get("/tasks")
async def list_compliance_tasks(current_user = Depends(get_current_user)):
    """List compliance tasks"""
    return {"message": "List compliance tasks endpoint"}

@router.get("/calendar/{company_id}")
async def get_compliance_calendar(company_id: int, current_user = Depends(get_current_user)):
    """Get compliance calendar for company"""
    return {"message": f"Compliance calendar for company {company_id}"}
