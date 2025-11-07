"""
Companies management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_ca
from app.models.user import User
from app.models.company import Company
from app.services.scraper import MCAScraperService, GSTScraperService

router = APIRouter()


class CompanyCreate(BaseModel):
    cin: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    company_name: str
    auto_fetch_data: bool = True


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    registered_address: Optional[str] = None
    corporate_address: Optional[str] = None


class CompanyResponse(BaseModel):
    id: int
    company_name: str
    cin: Optional[str]
    pan: Optional[str]
    gstin: Optional[str]
    compliance_score: int
    risk_level: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_ca),
    db: Session = Depends(get_db)
):
    """
    List all companies managed by the CA
    """
    query = db.query(Company).filter(
        Company.tenant_id == current_user.tenant_id
    )
    
    # If CA practitioner, show only their companies
    if current_user.role.value == "ca_practitioner":
        query = query.filter(Company.ca_user_id == current_user.id)
    
    companies = query.offset(skip).limit(limit).all()
    return companies


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    request: CompanyCreate,
    current_user: User = Depends(require_ca),
    db: Session = Depends(get_db)
):
    """
    Add new company with auto-fetch from government portals
    """
    # Check if company already exists
    if request.cin:
        existing = db.query(Company).filter(Company.cin == request.cin).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company with this CIN already exists"
            )
    
    # Auto-fetch data from MCA if CIN provided
    master_data = {}
    if request.cin and request.auto_fetch_data:
        try:
            scraper = MCAScraperService()
            master_data = await scraper.fetch_company_data(request.cin)
        except Exception as e:
            # Log error but continue with manual data
            pass
    
    # Auto-fetch GST data if GSTIN provided
    if request.gstin and request.auto_fetch_data:
        try:
            gst_scraper = GSTScraperService()
            gst_data = await gst_scraper.fetch_gst_data(request.gstin)
            master_data.update(gst_data)
        except Exception as e:
            pass
    
    # Create company
    company = Company(
        company_name=master_data.get("company_name", request.company_name),
        cin=request.cin,
        pan=request.pan,
        gstin=request.gstin,
        tenant_id=current_user.tenant_id,
        tenant_id_fk=current_user.tenant_id_fk,
        ca_user_id=current_user.id,
        registered_address=master_data.get("address"),
        date_of_incorporation=master_data.get("date_of_incorporation"),
        company_status=master_data.get("status"),
        directors=master_data.get("directors", []),
        data_source="mca" if master_data else "manual"
    )
    
    db.add(company)
    db.commit()
    db.refresh(company)
    
    # TODO: Generate compliance calendar for the company
    # from app.services.compliance_engine import generate_compliance_calendar
    # await generate_compliance_calendar(company.id, db)
    
    return company


@router.get("/{company_id}", response_model=dict)
async def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed company information
    """
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.tenant_id == current_user.tenant_id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check access rights
    if current_user.role.value == "ca_practitioner" and company.ca_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if current_user.role.value == "company_user" and company.company_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get compliance tasks
    from app.models.compliance import ComplianceTask
    tasks = db.query(ComplianceTask).filter(
        ComplianceTask.company_id == company_id
    ).all()
    
    return {
        "company": company.to_dict(include_sensitive=True),
        "compliance_tasks": [task.to_dict() for task in tasks],
        "total_tasks": len(tasks),
        "pending_tasks": len([t for t in tasks if t.status.value == "pending"]),
        "overdue_tasks": len([t for t in tasks if t.is_overdue()])
    }


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    request: CompanyUpdate,
    current_user: User = Depends(require_ca),
    db: Session = Depends(get_db)
):
    """
    Update company information
    """
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.tenant_id == current_user.tenant_id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check access rights
    if current_user.role.value == "ca_practitioner" and company.ca_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    db.commit()
    db.refresh(company)
    
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    current_user: User = Depends(require_ca),
    db: Session = Depends(get_db)
):
    """
    Delete company (soft delete recommended in production)
    """
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.tenant_id == current_user.tenant_id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check access rights
    if current_user.role.value == "ca_practitioner" and company.ca_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    db.delete(company)
    db.commit()
    
    return None


@router.post("/{company_id}/sync-data")
async def sync_company_data(
    company_id: int,
    current_user: User = Depends(require_ca),
    db: Session = Depends(get_db)
):
    """
    Sync company data from government portals
    """
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.tenant_id == current_user.tenant_id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    synced_data = {}
    
    # Sync MCA data
    if company.cin:
        try:
            scraper = MCAScraperService()
            mca_data = await scraper.fetch_company_data(company.cin)
            synced_data["mca"] = mca_data
            
            # Update company
            company.registered_address = mca_data.get("address", company.registered_address)
            company.directors = mca_data.get("directors", company.directors)
            company.company_status = mca_data.get("status", company.company_status)
        except Exception as e:
            synced_data["mca_error"] = str(e)
    
    # Sync GST data
    if company.gstin:
        try:
            gst_scraper = GSTScraperService()
            gst_data = await gst_scraper.fetch_gst_data(company.gstin)
            synced_data["gst"] = gst_data
        except Exception as e:
            synced_data["gst_error"] = str(e)
    
    company.last_synced_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Data sync completed",
        "synced_data": synced_data
    }
