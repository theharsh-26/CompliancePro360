"""
Notification models
"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel, TenantMixin


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"
    PUSH = "push"


class NotificationPriority(str, enum.Enum):
    """Notification priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, enum.Enum):
    """Notification status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class Notification(BaseModel, TenantMixin):
    """
    Notification model for multi-channel alerts
    """
    
    __tablename__ = "notifications"
    
    # Notification Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50))  # compliance_due, filing_reminder, system_alert, etc.
    
    # Priority and Channel
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)
    channels = Column(JSON, default=list)  # List of channels to send through
    
    # Status
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Recipient
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="notifications")
    
    # Related Entities
    related_entity_type = Column(String(50))  # company, compliance_task, etc.
    related_entity_id = Column(Integer)
    
    # Scheduling
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    
    # Action
    action_url = Column(String(500))
    action_label = Column(String(100))
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    logs = relationship("NotificationLog", back_populates="notification", cascade="all, delete-orphan")
    
    def mark_as_read(self):
        """Mark notification as read"""
        from datetime import datetime
        self.status = NotificationStatus.READ
        self.read_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status})>"


class NotificationLog(BaseModel):
    """
    Log of notification delivery attempts
    """
    
    __tablename__ = "notification_logs"
    
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    notification = relationship("Notification", back_populates="logs")
    
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(SQLEnum(NotificationStatus), nullable=False)
    
    attempt_number = Column(Integer, default=1)
    sent_at = Column(DateTime)
    
    # Response from delivery service
    response_code = Column(String(50))
    response_message = Column(Text)
    error_message = Column(Text)
    
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, channel={self.channel}, status={self.status})>"
