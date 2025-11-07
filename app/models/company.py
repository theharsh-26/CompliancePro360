"""
Company model with master data from government portals
"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, Date, Float
from sqlalchemy.orm import relationship
from .base import BaseModel, TenantMixin


class Company(BaseModel, TenantMixin):
    """
    Company model storing all master data and compliance information
    """
    
    __tablename__ = "companies"
    
    # Basic Information
    company_name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(255))
    
    # Government Identifiers
    cin = Column(String(21), unique=True, index=True)  # Corporate Identification Number
    pan = Column(String(10), unique=True, index=True)  # Permanent Account Number
    gstin = Column(String(15), unique=True, index=True)  # GST Identification Number
    tan = Column(String(10))  # Tax Deduction Account Number
    
    # Registration Details
    date_of_incorporation = Column(Date)
    registration_number = Column(String(50))
    company_type = Column(String(50))  # Private Limited, LLP, Public Limited, etc.
    company_category = Column(String(50))  # Company with Share Capital, etc.
    company_sub_category = Column(String(50))
    
    # Address Information
    registered_address = Column(Text)
    corporate_address = Column(Text)
    state = Column(String(50))
    city = Column(String(100))
    pincode = Column(String(10))
    
    # Status
    company_status = Column(String(50))  # Active, Inactive, Dissolved, etc.
    listing_status = Column(String(50))  # Listed, Unlisted
    
    # Directors and Stakeholders
    directors = Column(JSON, default=list)  # List of director details
    authorized_capital = Column(Float)
    paid_up_capital = Column(Float)
    
    # Business Information
    business_activity = Column(Text)
    industry_type = Column(String(100))
    
    # Compliance Score and Health
    compliance_score = Column(Integer, default=100)
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    
    # Master Data Source
    data_source = Column(String(50), default="manual")  # manual, mca, gst, income_tax
    last_synced_at = Column(DateTime)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    tenant_id_fk = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", back_populates="companies")
    
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ca_user = relationship("User", foreign_keys=[ca_user_id], back_populates="managed_companies")
    
    company_user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    company_user = relationship("User", foreign_keys=[company_user_id], back_populates="company_profile")
    
    compliance_tasks = relationship("ComplianceTask", back_populates="company", cascade="all, delete-orphan")
    compliance_calendars = relationship("ComplianceCalendar", back_populates="company", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="company", cascade="all, delete-orphan")
    metrics = relationship("ComplianceMetrics", back_populates="company", cascade="all, delete-orphan")
    
    def to_dict(self, include_sensitive=False):
        data = super().to_dict()
        if not include_sensitive:
            # Remove sensitive financial data for non-authorized users
            data.pop('authorized_capital', None)
            data.pop('paid_up_capital', None)
        return data
    
    def __repr__(self):
        return f"<Company(id={self.id}, name={self.company_name}, cin={self.cin})>"
