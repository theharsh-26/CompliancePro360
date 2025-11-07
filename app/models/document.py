"""
Document management models
"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, Boolean, BigInteger
from sqlalchemy.orm import relationship
from .base import BaseModel, TenantMixin


class Document(BaseModel, TenantMixin):
    """
    Document storage and management
    """
    
    __tablename__ = "documents"
    
    # Document Information
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(100))  # certificate, return, acknowledgment, etc.
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)  # in bytes
    mime_type = Column(String(100))
    
    # Document Details
    description = Column(Text)
    document_number = Column(String(100))  # e.g., certificate number
    issue_date = Column(Date)
    expiry_date = Column(Date)
    
    # Relationships
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", back_populates="documents")
    
    compliance_task_id = Column(Integer, ForeignKey("compliance_tasks.id"))
    compliance_task = relationship("ComplianceTask", back_populates="documents")
    
    # Version Control
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    parent_document_id = Column(Integer, ForeignKey("documents.id"))
    
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    
    # Security
    is_encrypted = Column(Boolean, default=True)
    access_level = Column(String(50), default="private")  # private, company, public
    
    # Metadata
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # Upload Information
    uploaded_by = Column(String(255))
    
    def __repr__(self):
        return f"<Document(id={self.id}, name={self.document_name})>"


class DocumentVersion(BaseModel):
    """
    Document version history
    """
    
    __tablename__ = "document_versions"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    document = relationship("Document", back_populates="versions")
    
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    
    change_description = Column(Text)
    changed_by = Column(String(255))
    
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<DocumentVersion(id={self.id}, doc_id={self.document_id}, version={self.version_number})>"
