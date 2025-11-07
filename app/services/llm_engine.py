"""
LLM Reasoning Engine for Compliance Intelligence
Interprets government notifications and updates compliance rules
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import openai
from anthropic import Anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMReasoningEngine:
    """
    AI-powered reasoning engine for compliance management
    Uses LLM APIs to interpret notifications and extract compliance information
    """
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        
        # Initialize API clients
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        elif self.provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def extract_due_date_from_notification(
        self,
        notification_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract compliance due date information from government notification
        
        Args:
            notification_text: Text of the government notification
        
        Returns:
            Dictionary with form_name, new_due_date, and reason
        """
        prompt = self._build_due_date_extraction_prompt(notification_text)
        
        try:
            response = await self._call_llm(prompt)
            extracted_data = self._parse_llm_response(response)
            
            if extracted_data and self._validate_extracted_data(extracted_data):
                logger.info(f"Successfully extracted due date: {extracted_data}")
                return extracted_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting due date: {e}")
            return None
    
    async def analyze_compliance_applicability(
        self,
        company_data: Dict[str, Any],
        compliance_rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine if a compliance rule applies to a specific company
        
        Args:
            company_data: Company information
            compliance_rule: Compliance rule details
        
        Returns:
            Analysis with applicability decision and reasoning
        """
        prompt = self._build_applicability_prompt(company_data, compliance_rule)
        
        try:
            response = await self._call_llm(prompt)
            analysis = json.loads(response)
            
            return {
                "applicable": analysis.get("applicable", False),
                "confidence": analysis.get("confidence", 0.0),
                "reasoning": analysis.get("reasoning", ""),
                "risk_level": analysis.get("risk_level", "medium")
            }
            
        except Exception as e:
            logger.error(f"Error analyzing applicability: {e}")
            return {
                "applicable": False,
                "confidence": 0.0,
                "reasoning": f"Analysis failed: {e}",
                "risk_level": "unknown"
            }
    
    async def predict_filing_delay_risk(
        self,
        company_history: List[Dict[str, Any]],
        upcoming_compliance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict likelihood of filing delay using historical data
        
        Args:
            company_history: Historical compliance data
            upcoming_compliance: Upcoming compliance task
        
        Returns:
            Risk prediction with probability and recommendations
        """
        prompt = self._build_risk_prediction_prompt(company_history, upcoming_compliance)
        
        try:
            response = await self._call_llm(prompt)
            prediction = json.loads(response)
            
            return {
                "delay_probability": prediction.get("delay_probability", 0.0),
                "risk_level": prediction.get("risk_level", "medium"),
                "risk_factors": prediction.get("risk_factors", []),
                "recommendations": prediction.get("recommendations", []),
                "confidence": prediction.get("confidence", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error predicting risk: {e}")
            return {
                "delay_probability": 0.5,
                "risk_level": "medium",
                "risk_factors": [],
                "recommendations": [],
                "confidence": 0.0
            }
    
    async def interpret_circular(self, circular_text: str) -> Dict[str, Any]:
        """
        Interpret government circular and extract key information
        
        Args:
            circular_text: Full text of the circular
        
        Returns:
            Structured interpretation of the circular
        """
        prompt = f"""
        You are an expert Indian tax and compliance analyst. Analyze the following government circular
        and extract key information in JSON format.
        
        Circular Text:
        {circular_text}
        
        Extract and return ONLY a valid JSON object with these fields:
        {{
            "circular_number": "...",
            "date": "YYYY-MM-DD",
            "subject": "...",
            "affected_compliances": ["..."],
            "key_changes": ["..."],
            "effective_from": "YYYY-MM-DD",
            "action_required": "...",
            "summary": "..."
        }}
        """
        
        try:
            response = await self._call_llm(prompt)
            interpretation = json.loads(response)
            return interpretation
        except Exception as e:
            logger.error(f"Error interpreting circular: {e}")
            return {}
    
    def _build_due_date_extraction_prompt(self, notification_text: str) -> str:
        """Build prompt for due date extraction"""
        return f"""
        You are an expert Indian tax compliance analyst with deep knowledge of GST, Income Tax, 
        MCA, PF, ESI, and PT regulations.
        
        Analyze the following government notification and extract compliance due date information.
        
        Notification:
        {notification_text}
        
        Extract and return ONLY a valid JSON object with these exact fields:
        {{
            "form_name": "exact form name (e.g., GSTR-3B, GSTR-1, Form 24Q)",
            "compliance_type": "gst|income_tax|tds|mca|pf|esi|pt",
            "new_due_date": "YYYY-MM-DD",
            "original_due_date": "YYYY-MM-DD or null",
            "period": "period this applies to (e.g., October 2025, Q2 FY2025-26)",
            "is_extension": true or false,
            "reason": "brief reason for change",
            "applicable_to": "who this applies to (e.g., all taxpayers, specific turnover)",
            "confidence": 0.0 to 1.0
        }}
        
        If no clear due date information is found, return null.
        Return ONLY the JSON object, no additional text.
        """
    
    def _build_applicability_prompt(
        self,
        company_data: Dict[str, Any],
        compliance_rule: Dict[str, Any]
    ) -> str:
        """Build prompt for applicability analysis"""
        return f"""
        Determine if the following compliance rule applies to this company.
        
        Company Data:
        {json.dumps(company_data, indent=2)}
        
        Compliance Rule:
        {json.dumps(compliance_rule, indent=2)}
        
        Analyze and return ONLY a valid JSON object:
        {{
            "applicable": true or false,
            "confidence": 0.0 to 1.0,
            "reasoning": "detailed explanation",
            "risk_level": "low|medium|high|critical",
            "conditions_met": ["list of conditions satisfied"],
            "conditions_not_met": ["list of conditions not satisfied"]
        }}
        """
    
    def _build_risk_prediction_prompt(
        self,
        company_history: List[Dict[str, Any]],
        upcoming_compliance: Dict[str, Any]
    ) -> str:
        """Build prompt for risk prediction"""
        return f"""
        Predict the likelihood of filing delay for an upcoming compliance based on historical data.
        
        Historical Compliance Data:
        {json.dumps(company_history[-10:], indent=2)}
        
        Upcoming Compliance:
        {json.dumps(upcoming_compliance, indent=2)}
        
        Analyze patterns and return ONLY a valid JSON object:
        {{
            "delay_probability": 0.0 to 1.0,
            "risk_level": "low|medium|high|critical",
            "risk_factors": ["list of identified risk factors"],
            "recommendations": ["list of actionable recommendations"],
            "confidence": 0.0 to 1.0,
            "historical_pattern": "description of observed pattern"
        }}
        """
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API based on configured provider"""
        try:
            if self.provider == "openai":
                return await self._call_openai(prompt)
            elif self.provider == "anthropic":
                return await self._call_anthropic(prompt)
            else:
                # Fallback to mock response for development
                return self._mock_llm_response(prompt)
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return self._mock_llm_response(prompt)
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert Indian compliance analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        message = self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    def _mock_llm_response(self, prompt: str) -> str:
        """Mock LLM response for development/testing"""
        if "due date" in prompt.lower() and "gstr-3b" in prompt.lower():
            return json.dumps({
                "form_name": "GSTR-3B",
                "compliance_type": "gst",
                "new_due_date": "2025-11-25",
                "original_due_date": "2025-11-20",
                "period": "October 2025",
                "is_extension": True,
                "reason": "Extension due to technical issues on GST portal",
                "applicable_to": "All registered taxpayers",
                "confidence": 0.95
            })
        
        return json.dumps({
            "error": "Mock response - LLM API not configured"
        })
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response and extract JSON"""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return data
            return None
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON: {response}")
            return None
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> bool:
        """Validate extracted due date data"""
        required_fields = ["form_name", "new_due_date"]
        
        if not all(field in data for field in required_fields):
            return False
        
        # Validate date format
        try:
            datetime.strptime(data["new_due_date"], "%Y-%m-%d")
            return True
        except ValueError:
            return False
