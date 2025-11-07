"""
Compliance Engine - Core business logic for compliance management
Handles calendar generation, due date updates, and intelligent scheduling
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.company import Company
from app.models.compliance import (
    ComplianceTask,
    ComplianceCalendar,
    ComplianceRule,
    ComplianceType,
    ComplianceStatus,
    CompliancePriority,
    ComplianceFrequency
)
from app.services.llm_engine import LLMReasoningEngine
from app.services.scraper import NotificationScraperService
from app.core.database import get_db_context

logger = logging.getLogger(__name__)


class ComplianceEngine:
    """
    Main compliance engine for automated compliance management
    """
    
    def __init__(self):
        self.llm_engine = LLMReasoningEngine()
        self.notification_scraper = NotificationScraperService()
    
    async def generate_compliance_calendar(
        self,
        company_id: int,
        financial_year: str,
        db: Session
    ) -> ComplianceCalendar:
        """
        Generate comprehensive compliance calendar for a company
        
        Args:
            company_id: Company ID
            financial_year: Financial year (e.g., "FY2025-26")
            db: Database session
        
        Returns:
            Generated compliance calendar
        """
        logger.info(f"Generating compliance calendar for company {company_id}, FY {financial_year}")
        
        # Get company details
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        # Get applicable compliance rules
        applicable_rules = await self._get_applicable_rules(company, db)
        
        # Generate tasks for each rule
        tasks = []
        for rule in applicable_rules:
            rule_tasks = self._generate_tasks_from_rule(
                company,
                rule,
                financial_year
            )
            tasks.extend(rule_tasks)
        
        # Create calendar
        calendar = ComplianceCalendar(
            calendar_name=f"{company.company_name} - {financial_year}",
            financial_year=financial_year,
            company_id=company_id,
            tenant_id=company.tenant_id,
            is_active=True,
            is_auto_generated=True,
            calendar_data={"tasks": [task.to_dict() for task in tasks]}
        )
        
        db.add(calendar)
        
        # Add tasks to database
        for task in tasks:
            db.add(task)
        
        db.commit()
        
        logger.info(f"Generated {len(tasks)} compliance tasks for company {company_id}")
        return calendar
    
    async def check_for_due_date_updates(self, db: Session):
        """
        Main scheduled job to check for due date updates from government notifications
        """
        logger.info("Running scheduled due date update check...")
        
        # Fetch latest notifications
        notifications = await self.notification_scraper.fetch_latest_notifications()
        
        if not notifications:
            logger.info("No new notifications found")
            return
        
        logger.info(f"Processing {len(notifications)} notifications")
        
        updates_applied = 0
        
        for notification in notifications:
            # Check if notification contains due date information
            if self._is_due_date_notification(notification):
                # Use LLM to extract due date information
                extracted_data = await self.llm_engine.extract_due_date_from_notification(
                    notification['content']
                )
                
                if extracted_data and extracted_data.get('new_due_date'):
                    # Apply due date update to relevant tasks
                    updated_count = await self._apply_due_date_update(
                        extracted_data,
                        db
                    )
                    updates_applied += updated_count
        
        logger.info(f"Applied {updates_applied} due date updates")
    
    async def calculate_compliance_score(
        self,
        company_id: int,
        db: Session
    ) -> int:
        """
        Calculate compliance score for a company (0-100)
        
        Args:
            company_id: Company ID
            db: Database session
        
        Returns:
            Compliance score (0-100)
        """
        # Get all compliance tasks for the company
        tasks = db.query(ComplianceTask).filter(
            ComplianceTask.company_id == company_id
        ).all()
        
        if not tasks:
            return 100  # No tasks = perfect score
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == ComplianceStatus.COMPLETED])
        overdue_tasks = len([t for t in tasks if t.is_overdue()])
        missed_tasks = len([t for t in tasks if t.status == ComplianceStatus.MISSED])
        
        # Calculate score
        completion_rate = completed_tasks / total_tasks
        penalty_for_overdue = (overdue_tasks / total_tasks) * 20
        penalty_for_missed = (missed_tasks / total_tasks) * 30
        
        score = int((completion_rate * 100) - penalty_for_overdue - penalty_for_missed)
        score = max(0, min(100, score))  # Clamp between 0 and 100
        
        # Update company score
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            company.compliance_score = score
            db.commit()
        
        return score
    
    async def predict_compliance_risks(
        self,
        company_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Use ML/AI to predict compliance risks for a company
        
        Args:
            company_id: Company ID
            db: Database session
        
        Returns:
            Risk prediction analysis
        """
        # Get company historical data
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        # Get historical compliance tasks
        historical_tasks = db.query(ComplianceTask).filter(
            ComplianceTask.company_id == company_id
        ).order_by(ComplianceTask.due_date.desc()).limit(50).all()
        
        # Get upcoming tasks
        upcoming_tasks = db.query(ComplianceTask).filter(
            and_(
                ComplianceTask.company_id == company_id,
                ComplianceTask.status == ComplianceStatus.PENDING,
                ComplianceTask.due_date >= datetime.utcnow()
            )
        ).order_by(ComplianceTask.due_date).limit(10).all()
        
        # Prepare data for ML prediction
        company_history = [
            {
                "task_name": task.task_name,
                "due_date": task.due_date.isoformat(),
                "status": task.status.value,
                "was_overdue": task.is_overdue(),
                "days_to_complete": (task.actual_filing_date - task.due_date).days if task.actual_filing_date else None
            }
            for task in historical_tasks
        ]
        
        # Predict risk for each upcoming task
        risk_predictions = []
        for task in upcoming_tasks:
            prediction = await self.llm_engine.predict_filing_delay_risk(
                company_history,
                {
                    "task_name": task.task_name,
                    "due_date": task.due_date.isoformat(),
                    "compliance_type": task.compliance_type.value,
                    "priority": task.priority.value
                }
            )
            
            risk_predictions.append({
                "task_id": task.id,
                "task_name": task.task_name,
                "due_date": task.due_date.isoformat(),
                **prediction
            })
        
        # Calculate overall risk level
        avg_delay_prob = sum(p['delay_probability'] for p in risk_predictions) / len(risk_predictions) if risk_predictions else 0
        
        overall_risk = "low"
        if avg_delay_prob > 0.7:
            overall_risk = "critical"
        elif avg_delay_prob > 0.5:
            overall_risk = "high"
        elif avg_delay_prob > 0.3:
            overall_risk = "medium"
        
        return {
            "company_id": company_id,
            "overall_risk_level": overall_risk,
            "average_delay_probability": avg_delay_prob,
            "high_risk_tasks": [p for p in risk_predictions if p['delay_probability'] > 0.6],
            "predictions": risk_predictions,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    async def _get_applicable_rules(
        self,
        company: Company,
        db: Session
    ) -> List[ComplianceRule]:
        """Get compliance rules applicable to a company"""
        # Get all active rules
        all_rules = db.query(ComplianceRule).filter(
            ComplianceRule.is_active == True
        ).all()
        
        applicable_rules = []
        
        for rule in all_rules:
            # Check applicability using LLM
            company_data = {
                "company_type": company.company_type,
                "turnover": company.metadata.get("turnover"),
                "state": company.state,
                "gstin": company.gstin,
                "cin": company.cin
            }
            
            analysis = await self.llm_engine.analyze_compliance_applicability(
                company_data,
                {
                    "rule_name": rule.rule_name,
                    "compliance_type": rule.compliance_type.value,
                    "applicable_to": rule.applicable_to,
                    "company_types": rule.company_types,
                    "turnover_threshold": rule.turnover_threshold
                }
            )
            
            if analysis.get("applicable", False):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    def _generate_tasks_from_rule(
        self,
        company: Company,
        rule: ComplianceRule,
        financial_year: str
    ) -> List[ComplianceTask]:
        """Generate compliance tasks from a rule"""
        tasks = []
        
        # Parse financial year
        fy_start_year = int(financial_year.split("-")[0].replace("FY", ""))
        fy_start = datetime(fy_start_year, 4, 1)  # April 1st
        fy_end = datetime(fy_start_year + 1, 3, 31)  # March 31st
        
        # Generate tasks based on frequency
        if rule.frequency == ComplianceFrequency.MONTHLY:
            current_date = fy_start
            while current_date <= fy_end:
                due_date = self._calculate_due_date(current_date, rule)
                task = self._create_task(company, rule, current_date, due_date)
                tasks.append(task)
                current_date += timedelta(days=32)
                current_date = current_date.replace(day=1)
        
        elif rule.frequency == ComplianceFrequency.QUARTERLY:
            quarters = [
                (datetime(fy_start_year, 4, 1), datetime(fy_start_year, 6, 30)),
                (datetime(fy_start_year, 7, 1), datetime(fy_start_year, 9, 30)),
                (datetime(fy_start_year, 10, 1), datetime(fy_start_year, 12, 31)),
                (datetime(fy_start_year + 1, 1, 1), datetime(fy_start_year + 1, 3, 31))
            ]
            for quarter_start, quarter_end in quarters:
                due_date = self._calculate_due_date(quarter_end, rule)
                task = self._create_task(company, rule, quarter_start, due_date)
                tasks.append(task)
        
        elif rule.frequency == ComplianceFrequency.ANNUALLY:
            due_date = self._calculate_due_date(fy_end, rule)
            task = self._create_task(company, rule, fy_start, due_date)
            tasks.append(task)
        
        return tasks
    
    def _calculate_due_date(self, period_end: datetime, rule: ComplianceRule) -> datetime:
        """Calculate due date based on rule"""
        if rule.base_due_day:
            # Due on specific day of next month
            next_month = period_end + timedelta(days=32)
            due_date = next_month.replace(day=rule.base_due_day)
        else:
            # Default: 20 days after period end
            due_date = period_end + timedelta(days=20)
        
        return due_date
    
    def _create_task(
        self,
        company: Company,
        rule: ComplianceRule,
        period_start: datetime,
        due_date: datetime
    ) -> ComplianceTask:
        """Create a compliance task"""
        period_str = period_start.strftime("%B %Y")
        
        return ComplianceTask(
            task_name=f"{rule.form_name} - {period_str}",
            task_code=rule.rule_code,
            description=rule.description,
            compliance_type=rule.compliance_type,
            form_name=rule.form_name,
            act_name=rule.act_name,
            period=period_str,
            period_start_date=period_start.date(),
            period_end_date=(period_start + timedelta(days=30)).date(),
            due_date=due_date,
            status=ComplianceStatus.PENDING,
            priority=CompliancePriority.MEDIUM,
            source_of_due_date="system",
            company_id=company.id,
            rule_id=rule.id,
            tenant_id=company.tenant_id
        )
    
    def _is_due_date_notification(self, notification: Dict[str, Any]) -> bool:
        """Check if notification contains due date information"""
        keywords = ["due date", "extension", "extended", "deadline", "filing date"]
        content = notification.get('content', '').lower()
        return any(keyword in content for keyword in keywords)
    
    async def _apply_due_date_update(
        self,
        extracted_data: Dict[str, Any],
        db: Session
    ) -> int:
        """Apply due date update to relevant compliance tasks"""
        form_name = extracted_data.get('form_name')
        new_due_date_str = extracted_data.get('new_due_date')
        period = extracted_data.get('period')
        
        if not form_name or not new_due_date_str:
            return 0
        
        new_due_date = datetime.strptime(new_due_date_str, "%Y-%m-%d")
        
        # Find matching tasks
        query = db.query(ComplianceTask).filter(
            ComplianceTask.form_name.ilike(f"%{form_name}%"),
            ComplianceTask.status == ComplianceStatus.PENDING
        )
        
        if period:
            query = query.filter(ComplianceTask.period == period)
        
        tasks = query.all()
        
        # Update tasks
        for task in tasks:
            if task.due_date < new_due_date:
                task.extended_due_date = new_due_date
                task.source_of_due_date = "llm_auto"
                task.due_date_update_reason = extracted_data.get('reason', 'Auto-updated from notification')
        
        db.commit()
        
        logger.info(f"Updated {len(tasks)} tasks for {form_name}")
        return len(tasks)
