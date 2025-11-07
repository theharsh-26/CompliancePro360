"""Analytics and reporting endpoints"""
from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_analytics(current_user = Depends(get_current_user)):
    """Get dashboard analytics"""
    return {"message": "Dashboard analytics endpoint"}

@router.get("/company/{company_id}/metrics")
async def get_company_metrics(company_id: int, current_user = Depends(get_current_user)):
    """Get company compliance metrics"""
    return {"message": f"Company {company_id} metrics endpoint"}
