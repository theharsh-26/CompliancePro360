"""User management endpoints"""
from fastapi import APIRouter, Depends
from app.core.security import require_tenant_admin

router = APIRouter()

@router.get("/")
async def list_users(current_user = Depends(require_tenant_admin)):
    """List users in tenant"""
    return {"message": "List users endpoint"}

@router.post("/")
async def create_user(current_user = Depends(require_tenant_admin)):
    """Create new user"""
    return {"message": "Create user endpoint"}
