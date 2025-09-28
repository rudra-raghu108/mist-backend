"""
Web Scraping Service for SRM Guide Bot
Scrapes SRM website and student portal for data
"""

import asyncio
import logging
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import SystemConfig, Base
from app.core.database import get_db

logger = logging.getLogger(__name__)


class SRMScrapingService:
    """Service for scraping SRM website and student portal"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': settings.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.scraped_data = {
            'programs': [],
            'facilities': [],
            'events': [],
            'news': [],
            'admissions': [],
            'placements': [],
            'campus_info': [],
            'student_portal_data': []
        }
    
    async def initialize_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=connector
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape_srm_main_website(self) -> Dict[str, Any]:
        """Scrape main SRM website for comprehensive data"""
        try:
            await self.initialize_session()
            
            # Scrape main pages
            await self._scrape_programs()
            await self._scrape_facilities()
            await self._scrape_events()
            await self._scrape_news()
            await self._scrape_admissions()
            await self._scrape_placements()
            await self._scrape_campus_info()
            
            # Save scraped data to database
            await self._save_scraped_data()
            
            logger.info(f"Successfully scraped {len(self.scraped_data)} categories from SRM main website")
            return self.scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping SRM main website: {str(e)}")
            return {}
    
    async def _scrape_programs(self):
        """Scrape academic programs information"""
        try:
            urls = [
                f"{settings.SRM_MAIN_URL}/academics/engineering",
                f"{settings.SRM_MAIN_URL}/academics/medical",
                f"{settings.SRM_MAIN_URL}/academics/management",
                f"{settings.SRM_MAIN_URL}/academics/science",
                f"{settings.SRM_MAIN_URL}/academics/law",
                f"{settings.SRM_MAIN_URL}/academics/arts"
            ]
            
            for url in urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract program information
                            programs = self._extract_programs_from_page(soup, url)
                            self.scraped_data['programs'].extend(programs)
                            
                except Exception as e:
                    logger.error(f"Error scraping programs from {url}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in _scrape_programs: {str(e)}")
    
    def _extract_programs_from_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract program information from a page"""
        programs = []
        
        try:
            # Look for program cards, lists, or tables
            program_elements = soup.find_all(['div', 'li', 'tr'], class_=re.compile(r'program|course|degree', re.I))
            
            for element in program_elements:
                program = {
                    'name': '',
                    'duration': '',
                    'description': '',
                    'specializations': [],
                    'fees': '',
                    'eligibility': '',
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                # Extract program name
                name_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
                if name_elem:
                    program['name'] = name_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = element.find(['p', 'span', 'div'])
                if desc_elem:
                    program['description'] = desc_elem.get_text(strip=True)
                
                # Extract other details
                text_content = element.get_text()
                
                # Look for duration patterns
                duration_match = re.search(r'(\d+)\s*(year|semester|month)', text_content, re.I)
                if duration_match:
                    program['duration'] = f"{duration_match.group(1)} {duration_match.group(2)}s"
                
                # Look for fee patterns
                fee_match = re.search(r'₹?\s*(\d+(?:,\d+)*)\s*(?:LPA|per\s*year|annum)', text_content, re.I)
                if fee_match:
                    program['fees'] = f"₹{fee_match.group(1)}"
                
                if program['name']:
                    programs.append(program)
            
        except Exception as e:
            logger.error(f"Error extracting programs: {str(e)}")
        
        return programs
    
    async def _scrape_facilities(self):
        """Scrape campus facilities information"""
        try:
            urls = [
                f"{settings.SRM_MAIN_URL}/campus-life/facilities",
                f"{settings.SRM_MAIN_URL}/campus-life/hostels",
                f"{settings.SRM_MAIN_URL}/campus-life/sports"
            ]
            
            for url in urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            facilities = self._extract_facilities_from_page(soup, url)
                            self.scraped_data['facilities'].extend(facilities)
                            
                except Exception as e:
                    logger.error(f"Error scraping facilities from {url}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in _scrape_facilities: {str(e)}")
    
    def _extract_facilities_from_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract facilities information from a page"""
        facilities = []
        
        try:
            facility_elements = soup.find_all(['div', 'section'], class_=re.compile(r'facility|amenity|infrastructure', re.I))
            
            for element in facility_elements:
                facility = {
                    'name': '',
                    'description': '',
                    'location': '',
                    'features': [],
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                # Extract facility name
                name_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if name_elem:
                    facility['name'] = name_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = element.find(['p', 'span'])
                if desc_elem:
                    facility['description'] = desc_elem.get_text(strip=True)
                
                # Extract features
                feature_elements = element.find_all(['li', 'span'])
                for feat_elem in feature_elements:
                    feature_text = feat_elem.get_text(strip=True)
                    if feature_text and len(feature_text) > 5:
                        facility['features'].append(feature_text)
                
                if facility['name']:
                    facilities.append(facility)
            
        except Exception as e:
            logger.error(f"Error extracting facilities: {str(e)}")
        
        return facilities
    
    async def _scrape_events(self):
        """Scrape campus events and activities"""
        try:
            urls = [
                f"{settings.SRM_MAIN_URL}/campus-life/events",
                f"{settings.SRM_MAIN_URL}/news-events"
            ]
            
            for url in urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            events = self._extract_events_from_page(soup, url)
                            self.scraped_data['events'].extend(events)
                            
                except Exception as e:
                    logger.error(f"Error scraping events from {url}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in _scrape_events: {str(e)}")
    
    def _extract_events_from_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract events information from a page"""
        events = []
        
        try:
            event_elements = soup.find_all(['div', 'article'], class_=re.compile(r'event|news|activity', re.I))
            
            for element in event_elements:
                event = {
                    'title': '',
                    'description': '',
                    'date': '',
                    'location': '',
                    'category': '',
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                # Extract event title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_elem:
                    event['title'] = title_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = element.find(['p', 'span'])
                if desc_elem:
                    event['description'] = desc_elem.get_text(strip=True)
                
                # Extract date
                date_elem = element.find(['time', 'span'], class_=re.compile(r'date|time', re.I))
                if date_elem:
                    event['date'] = date_elem.get_text(strip=True)
                
                if event['title']:
                    events.append(event)
            
        except Exception as e:
            logger.error(f"Error extracting events: {str(e)}")
        
        return events
    
    async def _scrape_news(self):
        """Scrape news and announcements"""
        try:
            urls = [
                f"{settings.SRM_MAIN_URL}/news",
                f"{settings.SRM_MAIN_URL}/announcements"
            ]
            
            for url in urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            news = self._extract_news_from_page(soup, url)
                            self.scraped_data['news'].extend(news)
                            
                except Exception as e:
                    logger.error(f"Error scraping news from {url}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in _scrape_news: {str(e)}")
    
    def _extract_news_from_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract news information from a page"""
        news_items = []
        
        try:
            news_elements = soup.find_all(['div', 'article'], class_=re.compile(r'news|announcement|update', re.I))
            
            for element in news_elements:
                news = {
                    'title': '',
                    'content': '',
                    'date': '',
                    'category': '',
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                # Extract news title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_elem:
                    news['title'] = title_elem.get_text(strip=True)
                
                # Extract content
                content_elem = element.find(['p', 'span', 'div'])
                if content_elem:
                    news['content'] = content_elem.get_text(strip=True)
                
                # Extract date
                date_elem = element.find(['time', 'span'], class_=re.compile(r'date|time', re.I))
                if date_elem:
                    news['date'] = date_elem.get_text(strip=True)
                
                if news['title']:
                    news_items.append(news)
            
        except Exception as e:
            logger.error(f"Error extracting news: {str(e)}")
        
        return news_items
    
    async def _scrape_admissions(self):
        """Scrape admissions information"""
        try:
            urls = [
                f"{settings.SRM_MAIN_URL}/admissions",
                f"{settings.SRM_MAIN_URL}/admissions/engineering",
                f"{settings.SRM_MAIN_URL}/admissions/medical"
            ]
            
            for url in urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            admissions = self._extract_admissions_from_page(soup, url)
                            self.scraped_data['admissions'].extend(admissions)
                            
                except Exception as e:
                    logger.error(f"Error scraping admissions from {url}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in _scrape_admissions: {str(e)}")
    
    def _extract_admissions_from_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract admissions information from a page"""
        admissions = []
        
        try:
            admission_elements = soup.find_all(['div', 'section'], class_=re.compile(r'admission|requirement|process', re.I))
            
            for element in admission_elements:
                admission = {
                    'program': '',
                    'requirements': [],
                    'process': '',
                    'deadlines': '',
                    'fees': '',
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                # Extract program name
                program_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if program_elem:
                    admission['program'] = program_elem.get_text(strip=True)
                
                # Extract requirements
                req_elements = element.find_all(['li', 'p'])
                for req_elem in req_elements:
                    req_text = req_elem.get_text(strip=True)
                    if req_text and len(req_text) > 10:
                        admission['requirements'].append(req_text)
                
                # Extract process
                process_elem = element.find(['div', 'section'], class_=re.compile(r'process|steps', re.I))
                if process_elem:
                    admission['process'] = process_elem.get_text(strip=True)
                
                if admission['program']:
                    admissions.append(admission)
            
        except Exception as e:
            logger.error(f"Error extracting admissions: {str(e)}")
        
        return admissions
    
    async def _scrape_placements(self):
        """Scrape placement information"""
        try:
            urls = [
                f"{settings.SRM_MAIN_URL}/placements",
                f"{settings.SRM_MAIN_URL}/careers"
            ]
            
            for url in urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            placements = self._extract_placements_from_page(soup, url)
                            self.scraped_data['placements'].extend(placements)
                            
                except Exception as e:
                    logger.error(f"Error scraping placements from {url}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in _scrape_placements: {str(e)}")
    
    def _extract_placements_from_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract placement information from a page"""
        placements = []
        
        try:
            placement_elements = soup.find_all(['div', 'section'], class_=re.compile(r'placement|career|recruiter', re.I))
            
            for element in placement_elements:
                placement = {
                    'year': '',
                    'statistics': {},
                    'companies': [],
                    'average_package': '',
                    'highest_package': '',
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                # Extract year
                year_match = re.search(r'20\d{2}', element.get_text())
                if year_match:
                    placement['year'] = year_match.group()
                
                # Extract statistics
                stat_elements = element.find_all(['div', 'span'], class_=re.compile(r'stat|number|percentage', re.I))
                for stat_elem in stat_elements:
                    stat_text = stat_elem.get_text(strip=True)
                    if re.search(r'\d+', stat_text):
                        placement['statistics'][stat_text] = stat_text
                
                # Extract companies
                company_elements = element.find_all(['div', 'span', 'img'])
                for company_elem in company_elements:
                    company_text = company_elem.get_text(strip=True)
                    if company_text and len(company_text) > 2:
                        placement['companies'].append(company_text)
                
                if placement['year'] or placement['statistics']:
                    placements.append(placement)
            
        except Exception as e:
            logger.error(f"Error extracting placements: {str(e)}")
        
        return placements
    
    async def _scrape_campus_info(self):
        """Scrape general campus information"""
        try:
            urls = [
                f"{settings.SRM_MAIN_URL}/about",
                f"{settings.SRM_MAIN_URL}/campus-life"
            ]
            
            for url in urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            campus_info = self._extract_campus_info_from_page(soup, url)
                            self.scraped_data['campus_info'].extend(campus_info)
                            
                except Exception as e:
                    logger.error(f"Error scraping campus info from {url}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in _scrape_campus_info: {str(e)}")
    
    def _extract_campus_info_from_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract campus information from a page"""
        campus_info = []
        
        try:
            info_elements = soup.find_all(['div', 'section'], class_=re.compile(r'about|campus|info', re.I))
            
            for element in info_elements:
                info = {
                    'title': '',
                    'description': '',
                    'category': '',
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                # Extract title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_elem:
                    info['title'] = title_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = element.find(['p', 'span'])
                if desc_elem:
                    info['description'] = desc_elem.get_text(strip=True)
                
                if info['title'] or info['description']:
                    campus_info.append(info)
            
        except Exception as e:
            logger.error(f"Error extracting campus info: {str(e)}")
        
        return campus_info
    
    async def scrape_student_portal(self, username: str, password: str) -> Dict[str, Any]:
        """Scrape student portal data (requires login)"""
        try:
            await self.initialize_session()
            
            # Login to student portal
            login_success = await self._login_to_portal(username, password)
            
            if login_success:
                # Scrape various sections
                await self._scrape_academic_info()
                await self._scrape_financial_info()
                await self._scrape_attendance_info()
                await self._scrape_results_info()
                
                logger.info(f"Successfully scraped student portal data for {username}")
                return self.scraped_data['student_portal_data']
            else:
                logger.error(f"Failed to login to student portal for {username}")
                return {}
                
        except Exception as e:
            logger.error(f"Error scraping student portal: {str(e)}")
            return {}
    
    async def _login_to_portal(self, username: str, password: str) -> bool:
        """Login to SRM student portal"""
        try:
            login_url = f"{settings.SRM_PORTAL_BASE_URL}/students/loginManager/youLogin.jsp"
            
            # Get login page to extract any required tokens
            async with self.session.get(login_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract any hidden fields
                    hidden_fields = {}
                    for hidden in soup.find_all('input', type='hidden'):
                        hidden_fields[hidden.get('name', '')] = hidden.get('value', '')
                    
                    # Prepare login data
                    login_data = {
                        'netid': username,
                        'password': password,
                        **hidden_fields
                    }
                    
                    # Submit login form
                    async with self.session.post(login_url, data=login_data) as login_response:
                        if login_response.status == 200:
                            # Check if login was successful
                            response_text = await login_response.text()
                            if 'dashboard' in response_text.lower() or 'welcome' in response_text.lower():
                                return True
                            else:
                                logger.error("Login failed - invalid credentials or captcha required")
                                return False
                        else:
                            logger.error(f"Login request failed with status {login_response.status}")
                            return False
                else:
                    logger.error(f"Failed to access login page: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False
    
    async def _scrape_academic_info(self):
        """Scrape academic information from student portal"""
        try:
            academic_urls = [
                f"{settings.SRM_PORTAL_BASE_URL}/students/academic",
                f"{settings.SRM_PORTAL_BASE_URL}/students/schedule"
            ]
            
            for url in academic_urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            academic_data = self._extract_academic_data(soup, url)
                            self.scraped_data['student_portal_data'].extend(academic_data)
                            
                except Exception as e:
                    logger.error(f"Error scraping academic info from {url}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in _scrape_academic_info: {str(e)}")
    
    def _extract_academic_data(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract academic data from portal page"""
        academic_data = []
        
        try:
            # Look for academic information
            academic_elements = soup.find_all(['div', 'table'], class_=re.compile(r'academic|course|schedule', re.I))
            
            for element in academic_elements:
                data = {
                    'type': 'academic',
                    'content': element.get_text(strip=True),
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                academic_data.append(data)
            
        except Exception as e:
            logger.error(f"Error extracting academic data: {str(e)}")
        
        return academic_data
    
    async def _scrape_financial_info(self):
        """Scrape financial information from student portal"""
        try:
            financial_url = f"{settings.SRM_PORTAL_BASE_URL}/students/financial"
            
            async with self.session.get(financial_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    financial_data = self._extract_financial_data(soup, financial_url)
                    self.scraped_data['student_portal_data'].extend(financial_data)
                    
        except Exception as e:
            logger.error(f"Error in _scrape_financial_info: {str(e)}")
    
    def _extract_financial_data(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract financial data from portal page"""
        financial_data = []
        
        try:
            # Look for financial information
            financial_elements = soup.find_all(['div', 'table'], class_=re.compile(r'financial|fee|payment', re.I))
            
            for element in financial_elements:
                data = {
                    'type': 'financial',
                    'content': element.get_text(strip=True),
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                financial_data.append(data)
            
        except Exception as e:
            logger.error(f"Error extracting financial data: {str(e)}")
        
        return financial_data
    
    async def _scrape_attendance_info(self):
        """Scrape attendance information from student portal"""
        try:
            attendance_url = f"{settings.SRM_PORTAL_BASE_URL}/students/attendance"
            
            async with self.session.get(attendance_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    attendance_data = self._extract_attendance_data(soup, attendance_url)
                    self.scraped_data['student_portal_data'].extend(attendance_data)
                    
        except Exception as e:
            logger.error(f"Error in _scrape_attendance_info: {str(e)}")
    
    def _extract_attendance_data(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract attendance data from portal page"""
        attendance_data = []
        
        try:
            # Look for attendance information
            attendance_elements = soup.find_all(['div', 'table'], class_=re.compile(r'attendance|present', re.I))
            
            for element in attendance_elements:
                data = {
                    'type': 'attendance',
                    'content': element.get_text(strip=True),
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                attendance_data.append(data)
            
        except Exception as e:
            logger.error(f"Error extracting attendance data: {str(e)}")
        
        return attendance_data
    
    async def _scrape_results_info(self):
        """Scrape results information from student portal"""
        try:
            results_url = f"{settings.SRM_PORTAL_BASE_URL}/students/results"
            
            async with self.session.get(results_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results_data = self._extract_results_data(soup, results_url)
                    self.scraped_data['student_portal_data'].extend(results_data)
                    
        except Exception as e:
            logger.error(f"Error in _scrape_results_info: {str(e)}")
    
    def _extract_results_data(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract results data from portal page"""
        results_data = []
        
        try:
            # Look for results information
            results_elements = soup.find_all(['div', 'table'], class_=re.compile(r'result|grade|mark', re.I))
            
            for element in results_elements:
                data = {
                    'type': 'results',
                    'content': element.get_text(strip=True),
                    'source_url': url,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                results_data.append(data)
            
        except Exception as e:
            logger.error(f"Error extracting results data: {str(e)}")
        
        return results_data
    
    async def _save_scraped_data(self):
        """Save scraped data to database"""
        try:
            db = next(get_db())
            
            # Save each category of scraped data
            for category, data_list in self.scraped_data.items():
                if data_list:
                    # Create a system config entry for this category
                    config_key = f"scraped_data_{category}"
                    config_value = json.dumps(data_list, default=str)
                    
                    # Check if config already exists
                    existing_config = db.query(SystemConfig).filter(SystemConfig.key == config_key).first()
                    
                    if existing_config:
                        existing_config.value = config_value
                        existing_config.updated_at = datetime.utcnow()
                    else:
                        new_config = SystemConfig(
                            key=config_key,
                            value=config_value,
                            description=f"Scraped {category} data from SRM website",
                            is_active=True
                        )
                        db.add(new_config)
                    
                    logger.info(f"Saved {len(data_list)} {category} records to database")
            
            db.commit()
            logger.info("Successfully saved all scraped data to database")
            
        except Exception as e:
            logger.error(f"Error saving scraped data: {str(e)}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    async def get_scraped_data_for_ai(self) -> str:
        """Get formatted scraped data for AI training"""
        try:
            db = next(get_db())
            
            ai_training_data = []
            
            # Get all scraped data from database
            scraped_configs = db.query(SystemConfig).filter(
                SystemConfig.key.like('scraped_data_%')
            ).all()
            
            for config in scraped_configs:
                try:
                    data = json.loads(config.value)
                    category = config.key.replace('scraped_data_', '')
                    
                    # Format data for AI training
                    formatted_data = self._format_data_for_ai(data, category)
                    ai_training_data.append(formatted_data)
                    
                except json.JSONDecodeError:
                    logger.error(f"Error parsing JSON for {config.key}")
                    continue
            
            db.close()
            
            # Combine all formatted data
            combined_data = "\n\n".join(ai_training_data)
            return combined_data
            
        except Exception as e:
            logger.error(f"Error getting scraped data for AI: {str(e)}")
            return ""
    
    def _format_data_for_ai(self, data: List[Dict], category: str) -> str:
        """Format scraped data for AI training"""
        formatted_lines = [f"=== {category.upper()} INFORMATION ==="]
        
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if key not in ['source_url', 'scraped_at'] and value:
                        if isinstance(value, list):
                            formatted_lines.append(f"{key}: {', '.join(value)}")
                        else:
                            formatted_lines.append(f"{key}: {value}")
                formatted_lines.append("---")
        
        return "\n".join(formatted_lines)
    
    async def schedule_scraping(self):
        """Schedule regular scraping"""
        while True:
            try:
                logger.info("Starting scheduled scraping...")
                await self.scrape_srm_main_website()
                
                # Wait for next scraping interval
                await asyncio.sleep(settings.SCRAPING_INTERVAL_HOURS * 3600)
                
            except Exception as e:
                logger.error(f"Error in scheduled scraping: {str(e)}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying


# Create singleton instance
scraping_service = SRMScrapingService()
