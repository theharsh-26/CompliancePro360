"""
User model with RBAC (Role-Based Access Control)
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
import enum
from .base import BaseModel, TenantMixin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, enum.Enum):
    """User roles for RBAC"""
    SYSTEM_ADMIN = "system_admin"  # Super admin - manages all tenants
    TENANT_ADMIN = "tenant_admin"  # Tenant admin - manages tenant
    CA_PRACTITIONER = "ca_practitioner"  # CA - manages companies
    COMPANY_USER = "company_user"  # Company user - views own data
    AUDITOR = "auditor"  # Read-only access for auditing


class User(BaseModel, TenantMixin):
    """
    User model with multi-tenant support and RBAC
    """
    
    __tablename__ = "users"
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    
    # Role and Permissions
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.COMPANY_USER)
    permissions = Column(JSON, default=dict)  # Additional granular permissions
    
    # CA Firm Information (for CA practitioners)
    firm_name = Column(String(255))
    firm_registration_number = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0)
    
    # Relationships
    tenant_id_fk = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", back_populates="users")
    
    managed_companies = relationship(
        "Company",
        foreign_keys="Company.ca_user_id",
        back_populates="ca_user",
        cascade="all, delete-orphan"
    )
    
    company_profile = relationship(
        "Company",
        foreign_keys="Company.company_user_id",
        back_populates="company_user",
        uselist=False
    )
    
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, self.password_hash)
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if self.role == UserRole.SYSTEM_ADMIN:
            return True
        return self.permissions.get(permission, False)
    
    def to_dict(self):
        data = super().to_dict()
        data.pop('password_hash', None)  # Never expose password hash
        data['role'] = self.role.value if self.role else None
        return data
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
