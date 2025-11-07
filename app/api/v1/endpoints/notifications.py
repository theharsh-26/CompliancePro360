"""Notification endpoints"""
from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter()

@router.get("/")
async def list_notifications(current_user = Depends(get_current_user)):
    """List user notifications"""
    return {"message": "List notifications endpoint"}

@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: int, current_user = Depends(get_current_user)):
    """Mark notification as read"""
    return {"message": f"Mark notification {notification_id} as read"}
