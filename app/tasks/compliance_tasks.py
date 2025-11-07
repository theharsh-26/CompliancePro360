"""
Celery tasks for compliance management
"""

import logging
from celery import Task
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import get_db_context
from app.services.compliance_engine import ComplianceEngine
from app.models.company import Company

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = next(get_db_context())
        return self._db


@celery_app.task(name="app.tasks.compliance_tasks.check_due_date_updates")
def check_due_date_updates():
    """
    Scheduled task to check for due date updates from government notifications
    Runs daily at 4 AM IST
    """
    logger.info("Starting due date update check task...")
    
    try:
        with get_db_context() as db:
            engine = ComplianceEngine()
            import asyncio
            asyncio.run(engine.check_for_due_date_updates(db))
        
        logger.info("Due date update check completed successfully")
        return {"status": "success", "message": "Due date updates checked"}
    
    except Exception as e:
        logger.error(f"Error in due date update check: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.compliance_tasks.calculate_all_compliance_scores")
def calculate_all_compliance_scores():
    """
    Calculate compliance scores for all companies
    Runs daily at 5 AM IST
    """
    logger.info("Starting compliance score calculation for all companies...")
    
    try:
        with get_db_context() as db:
            companies = db.query(Company).filter(Company.company_status == "Active").all()
            engine = ComplianceEngine()
            
            scores_updated = 0
            for company in companies:
                try:
                    import asyncio
                    score = asyncio.run(engine.calculate_compliance_score(company.id, db))
                    logger.info(f"Updated score for company {company.id}: {score}")
                    scores_updated += 1
                except Exception as e:
                    logger.error(f"Error calculating score for company {company.id}: {e}")
        
        logger.info(f"Compliance scores updated for {scores_updated} companies")
        return {"status": "success", "companies_updated": scores_updated}
    
    except Exception as e:
        logger.error(f"Error in compliance score calculation: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.compliance_tasks.predict_all_risks")
def predict_all_risks():
    """
    Predict compliance risks for all companies using ML/AI
    Runs weekly on Monday at 6 AM IST
    """
    logger.info("Starting risk prediction for all companies...")
    
    try:
        with get_db_context() as db:
            companies = db.query(Company).filter(Company.company_status == "Active").all()
            engine = ComplianceEngine()
            
            risks_analyzed = 0
            for company in companies:
                try:
                    import asyncio
                    risk_analysis = asyncio.run(engine.predict_compliance_risks(company.id, db))
                    
                    # Update company risk level
                    company.risk_level = risk_analysis['overall_risk_level']
                    db.commit()
                    
                    logger.info(f"Risk analysis completed for company {company.id}: {risk_analysis['overall_risk_level']}")
                    risks_analyzed += 1
                except Exception as e:
                    logger.error(f"Error predicting risk for company {company.id}: {e}")
        
        logger.info(f"Risk predictions completed for {risks_analyzed} companies")
        return {"status": "success", "companies_analyzed": risks_analyzed}
    
    except Exception as e:
        logger.error(f"Error in risk prediction: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.compliance_tasks.sync_all_company_data")
def sync_all_company_data():
    """
    Sync company master data from government portals
    Runs weekly on Sunday at 3 AM IST
    """
    logger.info("Starting company data sync from government portals...")
    
    try:
        from app.services.scraper import MCAScraperService, GSTScraperService
        
        with get_db_context() as db:
            companies = db.query(Company).filter(
                Company.company_status == "Active"
            ).limit(100).all()  # Limit to avoid rate limiting
            
            mca_scraper = MCAScraperService()
            gst_scraper = GSTScraperService()
            
            synced_count = 0
            for company in companies:
                try:
                    # Sync MCA data
                    if company.cin:
                        import asyncio
                        mca_data = asyncio.run(mca_scraper.fetch_company_data(company.cin))
                        company.directors = mca_data.get('directors', company.directors)
                        company.company_status = mca_data.get('status', company.company_status)
                    
                    # Sync GST data
                    if company.gstin:
                        import asyncio
                        gst_data = asyncio.run(gst_scraper.fetch_gst_data(company.gstin))
                    
                    from datetime import datetime
                    company.last_synced_at = datetime.utcnow()
                    db.commit()
                    
                    synced_count += 1
                    logger.info(f"Synced data for company {company.id}")
                    
                except Exception as e:
                    logger.error(f"Error syncing data for company {company.id}: {e}")
        
        logger.info(f"Data sync completed for {synced_count} companies")
        return {"status": "success", "companies_synced": synced_count}
    
    except Exception as e:
        logger.error(f"Error in company data sync: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.compliance_tasks.generate_calendar_for_company")
def generate_calendar_for_company(company_id: int, financial_year: str):
    """
    Generate compliance calendar for a specific company
    Can be triggered on-demand
    """
    logger.info(f"Generating compliance calendar for company {company_id}, FY {financial_year}")
    
    try:
        with get_db_context() as db:
            engine = ComplianceEngine()
            import asyncio
            calendar = asyncio.run(
                engine.generate_compliance_calendar(company_id, financial_year, db)
            )
        
        logger.info(f"Compliance calendar generated successfully for company {company_id}")
        return {
            "status": "success",
            "calendar_id": calendar.id,
            "tasks_generated": len(calendar.calendar_data.get('tasks', []))
        }
    
    except Exception as e:
        logger.error(f"Error generating calendar for company {company_id}: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
