"""Tenant management endpoints"""
from fastapi import APIRouter, Depends
from app.core.security import require_system_admin

router = APIRouter()

@router.get("/")
async def list_tenants(current_user = Depends(require_system_admin)):
    """List all tenants (System Admin only)"""
    return {"message": "List tenants endpoint"}

@router.get("/{tenant_id}")
async def get_tenant(tenant_id: str, current_user = Depends(require_system_admin)):
    """Get tenant details"""
    return {"message": f"Get tenant {tenant_id}"}
