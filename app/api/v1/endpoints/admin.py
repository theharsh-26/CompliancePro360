"""Admin endpoints"""
from fastapi import APIRouter, Depends
from app.core.security import require_system_admin

router = APIRouter()

@router.get("/stats")
async def get_system_stats(current_user = Depends(require_system_admin)):
    """Get system statistics"""
    return {"message": "System stats endpoint"}

@router.post("/trigger-engine")
async def trigger_compliance_engine(current_user = Depends(require_system_admin)):
    """Manually trigger compliance engine"""
    return {"message": "Trigger engine endpoint"}
