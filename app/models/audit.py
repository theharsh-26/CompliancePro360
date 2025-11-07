"""
Audit trail model for compliance and security
"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from .base import BaseModel, TenantMixin


class AuditLog(BaseModel, TenantMixin):
    """
    Comprehensive audit trail for all user actions
    """
    
    __tablename__ = "audit_logs"
    
    # Action Information
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, view, etc.
    entity_type = Column(String(100), nullable=False)  # user, company, compliance_task, etc.
    entity_id = Column(Integer)
    
    # User Information
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="audit_logs")
    user_email = Column(String(255))
    user_role = Column(String(50))
    
    # Request Information
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    request_method = Column(String(10))  # GET, POST, PUT, DELETE
    request_path = Column(String(500))
    
    # Changes
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    changes = Column(JSON)  # Diff of changes
    
    # Status
    status = Column(String(20))  # success, failure, error
    error_message = Column(Text)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, entity={self.entity_type})>"
