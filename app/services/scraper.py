"""
Web scraping services for government portals
MCA, GST, Income Tax data fetching
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class ScraperException(Exception):
    """Custom exception for scraping errors"""
    pass


class BaseScraperService:
    """Base scraper with common functionality"""
    
    def __init__(self):
        self.timeout = settings.SCRAPER_TIMEOUT
        self.chrome_options = Options()
        
        if settings.SELENIUM_HEADLESS:
            self.chrome_options.add_argument("--headless")
        
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    
    def _get_driver(self) -> webdriver.Chrome:
        """Initialize and return Chrome WebDriver"""
        try:
            service = Service(settings.CHROMEDRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise ScraperException(f"WebDriver initialization failed: {e}")
    
    async def _async_scrape(self, scrape_func, *args, **kwargs):
        """Run synchronous scraping in async context"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, scrape_func, *args, **kwargs)


class MCAScraperService(BaseScraperService):
    """
    Ministry of Corporate Affairs (MCA) Portal Scraper
    Fetches company master data using CIN
    """
    
    def __init__(self):
        super().__init__()
        self.mca_url = settings.MCA_PORTAL_URL
    
    async def fetch_company_data(self, cin: str) -> Dict[str, Any]:
        """
        Fetch company master data from MCA portal
        
        Args:
            cin: Corporate Identification Number (21 characters)
        
        Returns:
            Dictionary containing company master data
        """
        if not cin or len(cin) != 21:
            raise ScraperException("Invalid CIN. Must be 21 characters long.")
        
        cin = cin.upper()
        
        return await self._async_scrape(self._scrape_mca_data, cin)
    
    def _scrape_mca_data(self, cin: str) -> Dict[str, Any]:
        """Synchronous MCA scraping logic"""
        driver = self._get_driver()
        
        try:
            logger.info(f"Fetching MCA data for CIN: {cin}")
            driver.get(self.mca_url)
            
            # Wait for CIN input field
            cin_input = WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "companyCIN"))
            )
            cin_input.send_keys(cin)
            
            # Handle CAPTCHA (in production, use CAPTCHA solving service)
            logger.warning("CAPTCHA handling required - implementing delay")
            import time
            time.sleep(15)  # Simulated CAPTCHA solve time
            
            # Submit form
            submit_button = driver.find_element(By.ID, "companyLLPMasterData_0")
            submit_button.click()
            
            # Wait for results
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Parse results
            page_html = driver.page_source
            return self._parse_mca_html(page_html)
            
        except TimeoutException:
            logger.error(f"Timeout while fetching MCA data for CIN: {cin}")
            raise ScraperException("MCA portal timeout - data not available")
        except Exception as e:
            logger.error(f"Error scraping MCA data: {e}")
            raise ScraperException(f"MCA scraping failed: {e}")
        finally:
            driver.quit()
    
    def _parse_mca_html(self, html: str) -> Dict[str, Any]:
        """Parse MCA HTML response"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {}
        
        # Find main data table
        tables = soup.find_all('table')
        if not tables:
            raise ScraperException("No data tables found in MCA response")
        
        main_table = tables[0]
        rows = main_table.find_all('tr')
        
        # Extract company information
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                key = cols[0].text.strip().lower()
                value = cols[1].text.strip()
                
                if 'company name' in key:
                    data['company_name'] = value
                elif 'cin' in key:
                    data['cin'] = value
                elif 'date of incorporation' in key:
                    data['date_of_incorporation'] = value
                elif 'company status' in key or 'status' in key:
                    data['status'] = value
                elif 'registered address' in key or 'address' in key:
                    data['address'] = value
                elif 'authorized capital' in key:
                    data['authorized_capital'] = value
                elif 'paid up capital' in key:
                    data['paid_up_capital'] = value
        
        # Extract directors information
        data['directors'] = []
        director_table = soup.find('table', {'id': 'director_table'})
        if director_table:
            dir_rows = director_table.find_all('tr')[1:]  # Skip header
            for dir_row in dir_rows:
                dir_cols = dir_row.find_all('td')
                if len(dir_cols) >= 3:
                    data['directors'].append({
                        'din': dir_cols[0].text.strip(),
                        'name': dir_cols[1].text.strip(),
                        'appointment_date': dir_cols[2].text.strip()
                    })
        
        logger.info(f"Successfully parsed MCA data for: {data.get('company_name')}")
        return data


class GSTScraperService(BaseScraperService):
    """
    GST Portal Scraper
    Fetches GST registration details using GSTIN
    """
    
    def __init__(self):
        super().__init__()
        self.gst_url = settings.GST_PORTAL_URL
    
    async def fetch_gst_data(self, gstin: str) -> Dict[str, Any]:
        """
        Fetch GST registration data
        
        Args:
            gstin: GST Identification Number (15 characters)
        
        Returns:
            Dictionary containing GST data
        """
        if not gstin or len(gstin) != 15:
            raise ScraperException("Invalid GSTIN. Must be 15 characters long.")
        
        gstin = gstin.upper()
        
        return await self._async_scrape(self._scrape_gst_data, gstin)
    
    def _scrape_gst_data(self, gstin: str) -> Dict[str, Any]:
        """Synchronous GST scraping logic"""
        driver = self._get_driver()
        
        try:
            logger.info(f"Fetching GST data for GSTIN: {gstin}")
            driver.get(self.gst_url)
            
            # Wait for GSTIN input
            gstin_input = WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "gstin"))
            )
            gstin_input.send_keys(gstin)
            
            # Handle CAPTCHA
            import time
            time.sleep(10)
            
            # Submit
            search_button = driver.find_element(By.ID, "search")
            search_button.click()
            
            # Wait for results
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "result-container"))
            )
            
            page_html = driver.page_source
            return self._parse_gst_html(page_html)
            
        except Exception as e:
            logger.error(f"Error scraping GST data: {e}")
            raise ScraperException(f"GST scraping failed: {e}")
        finally:
            driver.quit()
    
    def _parse_gst_html(self, html: str) -> Dict[str, Any]:
        """Parse GST HTML response"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {}
        
        # Extract GST details (structure varies by portal version)
        result_div = soup.find('div', class_='result-container')
        if result_div:
            data['gstin_status'] = 'Active'  # Parse actual status
            data['trade_name'] = result_div.find(text='Trade Name:')
            data['registration_date'] = result_div.find(text='Registration Date:')
        
        logger.info(f"Successfully parsed GST data")
        return data


class NotificationScraperService:
    """
    Scrapes government notification portals for compliance updates
    """
    
    def __init__(self):
        self.cbic_url = settings.CBIC_NOTIFICATIONS_URL
    
    async def fetch_latest_notifications(self) -> list[Dict[str, Any]]:
        """Fetch latest notifications from CBIC and other portals"""
        try:
            response = requests.get(self.cbic_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            notifications = []
            
            # Parse notification items
            notification_items = soup.find_all('div', class_='notification-item')
            for item in notification_items:
                title = item.find('h3')
                content = item.find('p')
                date = item.find('span', class_='date')
                
                if title and content:
                    notifications.append({
                        'title': title.text.strip(),
                        'content': content.text.strip(),
                        'date': date.text.strip() if date else None,
                        'source': 'CBIC',
                        'url': self.cbic_url
                    })
            
            logger.info(f"Fetched {len(notifications)} notifications")
            return notifications
            
        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
            return []
