"""
Compliance models for task management and calendar
"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, Date, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel, TenantMixin


class ComplianceType(str, enum.Enum):
    """Types of compliance"""
    GST = "gst"
    INCOME_TAX = "income_tax"
    TDS = "tds"
    MCA = "mca"
    PF = "pf"
    ESI = "esi"
    PT = "pt"
    LABOUR = "labour"
    ENVIRONMENTAL = "environmental"
    OTHER = "other"


class ComplianceStatus(str, enum.Enum):
    """Status of compliance tasks"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FILED = "filed"
    OVERDUE = "overdue"
    MISSED = "missed"
    NOT_APPLICABLE = "not_applicable"


class CompliancePriority(str, enum.Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceFrequency(str, enum.Enum):
    """Frequency of compliance"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"
    ANNUALLY = "annually"
    ONE_TIME = "one_time"
    EVENT_BASED = "event_based"


class ComplianceTask(BaseModel, TenantMixin):
    """
    Individual compliance task/filing
    """
    
    __tablename__ = "compliance_tasks"
    
    # Task Information
    task_name = Column(String(255), nullable=False, index=True)
    task_code = Column(String(50))  # e.g., GSTR-3B, GSTR-1, Form 24Q
    description = Column(Text)
    
    # Compliance Type and Category
    compliance_type = Column(SQLEnum(ComplianceType), nullable=False)
    form_name = Column(String(100))
    act_name = Column(String(255))
    
    # Period and Dates
    period = Column(String(50))  # e.g., "October 2025", "Q2 FY2025-26"
    period_start_date = Column(Date)
    period_end_date = Column(Date)
    due_date = Column(DateTime, nullable=False, index=True)
    extended_due_date = Column(DateTime)
    actual_filing_date = Column(DateTime)
    
    # Status and Priority
    status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.PENDING, nullable=False)
    priority = Column(SQLEnum(CompliancePriority), default=CompliancePriority.MEDIUM)
    
    # Due Date Management
    source_of_due_date = Column(String(50), default="system")  # system, llm_auto, manual, government_portal
    due_date_updated_by = Column(String(50))
    due_date_update_reason = Column(Text)
    
    # Filing Information
    acknowledgment_number = Column(String(100))
    filing_reference = Column(String(100))
    filed_by = Column(String(255))
    
    # Notifications
    reminder_sent = Column(Boolean, default=False)
    last_reminder_at = Column(DateTime)
    escalation_sent = Column(Boolean, default=False)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    notes = Column(Text)
    
    # Relationships
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", back_populates="compliance_tasks")
    
    rule_id = Column(Integer, ForeignKey("compliance_rules.id"))
    rule = relationship("ComplianceRule", back_populates="tasks")
    
    documents = relationship("Document", back_populates="compliance_task", cascade="all, delete-orphan")
    
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        from datetime import datetime
        if self.status in [ComplianceStatus.COMPLETED, ComplianceStatus.FILED]:
            return False
        due = self.extended_due_date or self.due_date
        return datetime.utcnow() > due
    
    def days_until_due(self) -> int:
        """Calculate days until due date"""
        from datetime import datetime
        due = self.extended_due_date or self.due_date
        delta = due - datetime.utcnow()
        return delta.days
    
    def __repr__(self):
        return f"<ComplianceTask(id={self.id}, name={self.task_name}, due={self.due_date})>"


class ComplianceCalendar(BaseModel, TenantMixin):
    """
    Compliance calendar for a company
    Stores the entire compliance schedule
    """
    
    __tablename__ = "compliance_calendars"
    
    # Calendar Information
    calendar_name = Column(String(255), nullable=False)
    financial_year = Column(String(20), nullable=False)  # e.g., "FY2025-26"
    
    # Company
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", back_populates="compliance_calendars")
    
    # Calendar Data
    calendar_data = Column(JSON, default=dict)  # Full calendar structure
    
    # Status
    is_active = Column(Boolean, default=True)
    is_auto_generated = Column(Boolean, default=True)
    last_updated_by = Column(String(255))
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<ComplianceCalendar(id={self.id}, company_id={self.company_id}, fy={self.financial_year})>"


class ComplianceRule(BaseModel):
    """
    Master compliance rules and regulations
    Used to auto-generate compliance calendars
    """
    
    __tablename__ = "compliance_rules"
    
    # Rule Information
    rule_name = Column(String(255), nullable=False)
    rule_code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    
    # Compliance Details
    compliance_type = Column(SQLEnum(ComplianceType), nullable=False)
    form_name = Column(String(100))
    act_name = Column(String(255))
    section = Column(String(100))
    
    # Applicability
    applicable_to = Column(JSON, default=dict)  # Criteria for applicability
    company_types = Column(JSON, default=list)  # Which company types this applies to
    turnover_threshold = Column(Float)
    state_specific = Column(JSON, default=list)  # State-specific rules
    
    # Frequency and Due Date Logic
    frequency = Column(SQLEnum(ComplianceFrequency), nullable=False)
    due_date_formula = Column(Text)  # Formula to calculate due date
    base_due_day = Column(Integer)  # e.g., 20th of next month
    base_due_month = Column(Integer)  # For annual compliances
    
    # Extensions and Penalties
    extension_allowed = Column(Boolean, default=False)
    typical_extension_days = Column(Integer, default=0)
    penalty_applicable = Column(Boolean, default=True)
    penalty_formula = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    effective_from = Column(Date)
    effective_to = Column(Date)
    
    # Source
    source_url = Column(String(500))
    last_verified_at = Column(DateTime)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    tasks = relationship("ComplianceTask", back_populates="rule")
    
    def __repr__(self):
        return f"<ComplianceRule(id={self.id}, code={self.rule_code}, type={self.compliance_type})>"
