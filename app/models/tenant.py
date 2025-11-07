"""
Tenant model for multi-tenant SaaS architecture
"""

from sqlalchemy import Column, String, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from .base import BaseModel


class Tenant(BaseModel):
    """
    Tenant model representing a CA firm or organization
    Each tenant has isolated data and resources
    """
    
    __tablename__ = "tenants"
    
    # Basic Information
    tenant_id = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False)
    
    # Contact Information
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    
    # Status and Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Subscription and Limits
    subscription_tier = Column(String(50), default="trial")  # trial, basic, professional, enterprise
    max_users = Column(Integer, default=5)
    max_companies = Column(Integer, default=10)
    
    # Settings
    settings = Column(JSON, default=dict)  # Tenant-specific configuration
    features = Column(JSON, default=dict)  # Feature flags
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="tenant", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"
    
    def to_dict(self):
        data = super().to_dict()
        data.pop('settings', None)  # Don't expose sensitive settings
        return data
