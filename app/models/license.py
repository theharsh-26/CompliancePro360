"""
License and Subscription Management Models
Production-level SaaS licensing system
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import secrets
import enum
from .base import BaseModel, TenantMixin, TimestampMixin


class LicenseType(enum.Enum):
    """License types"""
    TRIAL = "trial"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class LicenseStatus(enum.Enum):
    """License status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class License(BaseModel, TenantMixin, TimestampMixin):
    """
    License Key Management
    Each practitioner gets a license key after purchase
    """
    __tablename__ = "licenses"
    
    license_key = Column(String(64), unique=True, nullable=False, index=True)
    license_type = Column(SQLEnum(LicenseType), nullable=False)
    status = Column(SQLEnum(LicenseStatus), default=LicenseStatus.ACTIVE)
    
    # Practitioner details
    practitioner_name = Column(String(200), nullable=False)
    practitioner_email = Column(String(200), nullable=False, index=True)
    practitioner_phone = Column(String(20))
    firm_name = Column(String(200))
    
    # License validity
    valid_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=False)
    auto_renew = Column(Boolean, default=False)
    
    # Pricing
    monthly_fee = Column(Numeric(10, 2), nullable=False)  # Fixed monthly charge
    setup_fee = Column(Numeric(10, 2), default=0.00)
    adhoc_rate_per_company = Column(Numeric(10, 2), default=0.00)  # Per company charge
    max_companies = Column(Integer, default=100)  # Company limit
    max_clients = Column(Integer, default=10)  # Client user limit
    
    # Usage tracking
    companies_count = Column(Integer, default=0)
    clients_count = Column(Integer, default=0)
    total_tasks_processed = Column(Integer, default=0)
    
    # Shareable link
    shareable_link = Column(String(500))  # Unique link for practitioner
    link_expiry = Column(DateTime)
    
    # Payment info
    payment_method = Column(String(50))
    last_payment_date = Column(DateTime)
    next_billing_date = Column(DateTime)
    
    # Features enabled
    features = Column(JSON, default=lambda: {
        "ai_automation": True,
        "data_scraping": True,
        "risk_prediction": True,
        "client_portal": True,
        "whatsapp_notifications": False,
        "api_access": False
    })
    
    # Metadata
    purchase_date = Column(DateTime, default=datetime.utcnow)
    activated_date = Column(DateTime)
    notes = Column(String(500))
    
    # Relationships
    tenant_id_fk = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'))
    tenant = relationship('Tenant', back_populates='licenses')
    
    invoices = relationship('Invoice', back_populates='license', cascade='all, delete-orphan')
    client_invitations = relationship('ClientInvitation', back_populates='license', cascade='all, delete-orphan')
    
    @staticmethod
    def generate_license_key():
        """Generate unique license key"""
        prefix = "CP360"
        key = secrets.token_hex(16).upper()
        return f"{prefix}-{key[:4]}-{key[4:8]}-{key[8:12]}-{key[12:16]}"
    
    @staticmethod
    def generate_shareable_link(license_key: str):
        """Generate shareable link for practitioner"""
        token = secrets.token_urlsafe(32)
        return f"https://app.compliancepro360.com/join/{license_key}/{token}"
    
    def is_valid(self) -> bool:
        """Check if license is valid"""
        if self.status != LicenseStatus.ACTIVE:
            return False
        if datetime.utcnow() > self.valid_until:
            return False
        return True
    
    def can_add_company(self) -> bool:
        """Check if can add more companies"""
        return self.companies_count < self.max_companies
    
    def can_add_client(self) -> bool:
        """Check if can add more clients"""
        return self.clients_count < self.max_clients
    
    def calculate_monthly_bill(self) -> float:
        """Calculate total monthly bill (fixed + adhoc)"""
        fixed = float(self.monthly_fee)
        adhoc = self.companies_count * float(self.adhoc_rate_per_company)
        return fixed + adhoc
    
    def to_dict(self):
        return {
            'id': self.id,
            'license_key': self.license_key,
            'license_type': self.license_type.value,
            'status': self.status.value,
            'practitioner_name': self.practitioner_name,
            'practitioner_email': self.practitioner_email,
            'firm_name': self.firm_name,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'monthly_fee': float(self.monthly_fee),
            'adhoc_rate_per_company': float(self.adhoc_rate_per_company),
            'companies_count': self.companies_count,
            'max_companies': self.max_companies,
            'shareable_link': self.shareable_link,
            'is_valid': self.is_valid(),
            'features': self.features
        }


class ClientInvitation(BaseModel, TimestampMixin):
    """
    Client Invitations sent by practitioners
    Clients can access via unique link
    """
    __tablename__ = "client_invitations"
    
    license_id = Column(Integer, ForeignKey('licenses.id', ondelete='CASCADE'), nullable=False)
    
    # Client details
    client_name = Column(String(200))
    client_email = Column(String(200), nullable=False, index=True)
    client_phone = Column(String(20))
    company_name = Column(String(200))
    
    # Invitation
    invitation_token = Column(String(100), unique=True, nullable=False)
    invitation_link = Column(String(500))
    invited_by = Column(Integer, ForeignKey('users.id'))
    invited_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Status
    is_accepted = Column(Boolean, default=False)
    accepted_at = Column(DateTime)
    is_revoked = Column(Boolean, default=False)
    
    # Created user (after acceptance)
    created_user_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    license = relationship('License', back_populates='client_invitations')
    
    @staticmethod
    def generate_invitation_link(license_key: str, token: str):
        """Generate client invitation link"""
        return f"https://app.compliancepro360.com/client/join/{license_key}/{token}"
    
    def is_valid(self) -> bool:
        """Check if invitation is still valid"""
        if self.is_accepted or self.is_revoked:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True


class Invoice(BaseModel, TimestampMixin):
    """
    Invoices for license billing
    """
    __tablename__ = "invoices"
    
    license_id = Column(Integer, ForeignKey('licenses.id', ondelete='CASCADE'), nullable=False)
    
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    
    # Billing period
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    
    # Amounts
    fixed_fee = Column(Numeric(10, 2), nullable=False)
    adhoc_fee = Column(Numeric(10, 2), default=0.00)
    companies_billed = Column(Integer, default=0)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    # Payment
    payment_status = Column(String(20), default="pending")  # pending, paid, overdue, cancelled
    payment_method = Column(String(50))
    payment_date = Column(DateTime)
    payment_transaction_id = Column(String(100))
    
    # Invoice details
    invoice_url = Column(String(500))  # URL to download invoice PDF
    notes = Column(String(500))
    
    # Relationships
    license = relationship('License', back_populates='invoices')
    
    @staticmethod
    def generate_invoice_number():
        """Generate unique invoice number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random = secrets.token_hex(4).upper()
        return f"INV-{timestamp}-{random}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'fixed_fee': float(self.fixed_fee),
            'adhoc_fee': float(self.adhoc_fee),
            'total_amount': float(self.total_amount),
            'payment_status': self.payment_status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None
        }
