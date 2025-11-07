"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    decode_token,
    get_current_user
)
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.audit import AuditLog

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    firm_name: str
    phone: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login endpoint
    Returns access and refresh tokens
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please contact support."
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    db.commit()
    
    # Create tokens
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "tenant_id": user.tenant_id
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user.id})
    
    # Log successful login
    audit_log = AuditLog(
        action="login",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        user_email=user.email,
        user_role=user.role.value,
        tenant_id=user.tenant_id,
        status="success"
    )
    db.add(audit_log)
    db.commit()
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user.to_dict()
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register new CA firm (tenant) with admin user
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Generate unique tenant ID
    import uuid
    tenant_id = str(uuid.uuid4())
    
    # Create subdomain from firm name
    subdomain = request.firm_name.lower().replace(" ", "-").replace(".", "")[:50]
    
    # Check if subdomain exists
    existing_tenant = db.query(Tenant).filter(Tenant.subdomain == subdomain).first()
    if existing_tenant:
        subdomain = f"{subdomain}-{str(uuid.uuid4())[:8]}"
    
    # Create tenant
    tenant = Tenant(
        tenant_id=tenant_id,
        name=request.firm_name,
        subdomain=subdomain,
        email=request.email,
        phone=request.phone,
        is_active=True,
        is_verified=False,
        subscription_tier="trial"
    )
    db.add(tenant)
    db.flush()
    
    # Create admin user for tenant
    user = User(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        firm_name=request.firm_name,
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
        tenant_id_fk=tenant.id,
        is_active=True,
        is_verified=False
    )
    user.set_password(request.password)
    db.add(user)
    db.commit()
    
    return {
        "message": "Registration successful",
        "tenant_id": tenant_id,
        "subdomain": subdomain,
        "user": user.to_dict()
    }


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    try:
        payload = decode_token(request.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "tenant_id": user.tenant_id
        }
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"sub": user.id})
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user=user.to_dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Logout user (client should discard tokens)
    """
    # Log logout action
    audit_log = AuditLog(
        action="logout",
        entity_type="user",
        entity_id=current_user.id,
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        tenant_id=current_user.tenant_id,
        status="success"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user.to_dict()
