"""
Subscription and billing models
"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Float, Boolean, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel


class SubscriptionTier(str, enum.Enum):
    """Subscription tiers"""
    TRIAL = "trial"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Subscription(BaseModel):
    """
    Subscription management for tenants
    """
    
    __tablename__ = "subscriptions"
    
    # Tenant
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", back_populates="subscriptions")
    
    # Subscription Details
    tier = Column(SQLEnum(SubscriptionTier), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    
    # Billing Period
    billing_cycle = Column(String(20), default="monthly")  # monthly, quarterly, annually
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    trial_end_date = Column(Date)
    
    # Pricing
    base_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    
    # Limits
    max_users = Column(Integer, default=5)
    max_companies = Column(Integer, default=10)
    max_storage_gb = Column(Integer, default=10)
    
    # Features
    features = Column(JSON, default=dict)
    
    # Auto-renewal
    auto_renew = Column(Boolean, default=True)
    next_billing_date = Column(Date)
    
    # Payment Gateway
    payment_gateway = Column(String(50))  # stripe, razorpay
    payment_gateway_subscription_id = Column(String(255))
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    billing_history = relationship("BillingHistory", back_populates="subscription", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, tier={self.tier}, status={self.status})>"


class BillingHistory(BaseModel):
    """
    Billing and payment history
    """
    
    __tablename__ = "billing_history"
    
    # Subscription
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    subscription = relationship("Subscription", back_populates="billing_history")
    
    # Invoice Details
    invoice_number = Column(String(100), unique=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)
    
    # Amount
    amount = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    
    # Payment
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_date = Column(Date)
    payment_method = Column(String(50))
    payment_gateway = Column(String(50))
    transaction_id = Column(String(255))
    
    # Invoice File
    invoice_file_path = Column(String(500))
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<BillingHistory(id={self.id}, invoice={self.invoice_number}, status={self.payment_status})>"
