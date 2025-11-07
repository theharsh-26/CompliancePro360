"""
Analytics and metrics models
"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Float, Date
from sqlalchemy.orm import relationship
from .base import BaseModel, TenantMixin


class ComplianceMetrics(BaseModel, TenantMixin):
    """
    Compliance metrics and KPIs for companies
    """
    
    __tablename__ = "compliance_metrics"
    
    # Company
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", back_populates="metrics")
    
    # Period
    period = Column(String(50), nullable=False)  # e.g., "2025-11", "Q2-2025"
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Compliance Statistics
    total_compliances = Column(Integer, default=0)
    completed_compliances = Column(Integer, default=0)
    pending_compliances = Column(Integer, default=0)
    overdue_compliances = Column(Integer, default=0)
    missed_compliances = Column(Integer, default=0)
    
    # Percentages
    completion_rate = Column(Float, default=0.0)  # Percentage
    on_time_filing_rate = Column(Float, default=0.0)
    
    # Compliance Score
    compliance_score = Column(Integer, default=100)
    previous_score = Column(Integer)
    score_change = Column(Integer)
    
    # Risk Metrics
    risk_level = Column(String(20))  # low, medium, high, critical
    risk_factors = Column(JSON, default=list)
    
    # Financial Impact
    penalties_incurred = Column(Float, default=0.0)
    interest_paid = Column(Float, default=0.0)
    
    # Trends
    trend_data = Column(JSON, default=dict)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<ComplianceMetrics(id={self.id}, company_id={self.company_id}, period={self.period})>"


class RiskScore(BaseModel, TenantMixin):
    """
    AI/ML-based risk scoring for companies
    """
    
    __tablename__ = "risk_scores"
    
    # Company
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", back_populates="risk_scores")
    
    # Risk Score
    overall_risk_score = Column(Float, nullable=False)  # 0-100
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Component Scores
    compliance_risk = Column(Float)
    financial_risk = Column(Float)
    operational_risk = Column(Float)
    regulatory_risk = Column(Float)
    
    # Risk Factors
    risk_factors = Column(JSON, default=list)
    high_risk_areas = Column(JSON, default=list)
    
    # Predictions
    predicted_delays = Column(JSON, default=list)  # ML predictions
    recommended_actions = Column(JSON, default=list)
    
    # Model Information
    model_version = Column(String(50))
    model_confidence = Column(Float)
    calculated_at = Column(DateTime, nullable=False)
    
    # Historical Comparison
    previous_score = Column(Float)
    score_trend = Column(String(20))  # improving, declining, stable
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<RiskScore(id={self.id}, company_id={self.company_id}, score={self.overall_risk_score})>"
