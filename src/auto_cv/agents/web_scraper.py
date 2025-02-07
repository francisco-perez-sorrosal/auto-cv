import logging
import time
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, WebDriverException

from auto_cv.cache import JobDescriptionCache

# Load environment variables from .env file
load_dotenv()

@dataclass
class JobPostingExtractor:
    """
    A robust class for extracting job description details from various job posting URLs.
    
    Supports multiple job platforms with fallback mechanisms.
    """
    
    timeout: int = 10
    _driver: Optional[Any] = None
    
    def __post_init__(self):
        """Initialize logging and setup chrome options"""
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        if not self._driver:
            self._driver = self._setup_webdriver()
        
        self._driver.implicitly_wait(self.timeout)
        self.logger.info("WebDriver initialized")
        
        # Initialize job description cache
        self._job_description_cache = JobDescriptionCache()
    
    def _setup_webdriver(self) -> webdriver:
        """
        Setup Chrome webdriver with headless mode and common options
        
        Returns:
            Configured Chrome webdriver
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            self.logger.error(f"Failed to initialize webdriver: {e}")
            raise
    
    def _get_linkedin_credentials(self) -> tuple[str, str]:
        """
        Retrieve LinkedIn credentials from environment variables.
        
        Returns:
            tuple: (username, password)
        
        Raises:
            ValueError: If credentials are not set
        """
        username = os.getenv('LINKEDIN_USERNAME')
        password = os.getenv('LINKEDIN_PASSWORD')
        
        if not username or not password:
            raise ValueError("LinkedIn credentials must be set in .env file")
        return username, password
    
    def _linkedin_login(self, username: str, password: str):
        """
        Perform LinkedIn login with the provided credentials
        
        Args:
            username (str): LinkedIn username
            password (str): LinkedIn password
        """
        
        try:
            # Navigate to LinkedIn login page
            self._driver.get("https://www.linkedin.com/login")
            
            # Wait for page to load
            time.sleep(3)
            
            # Find and fill username field
            username_field = self._driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(username)
            
            # Find and fill password field
            password_field = self._driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit login form
            password_field.submit()
            
            # Wait for potential login challenges
            time.sleep(5)
            
            # Optional: Check if login was successful
            try:
                # Look for an element that exists only after successful login
                self._driver.find_element(By.CSS_SELECTOR, "div.feed-identity-module")
                self.logger.info(f"LinkedIn login successful for user: {username}")
            except Exception:
                self.logger.warning("Login might have failed or requires additional verification")
        
        except Exception as e:
            self.logger.error(f"Failed to perform LinkedIn login: {e}")
            raise
    
    def extract_linkedin_job_description(self, url, username: str = None, password: str = None) -> Dict[str, str]:
        """
        Extract job description from LinkedIn job posting with caching
        
        Args:
            url (str): LinkedIn job posting URL
            username (str, optional): LinkedIn username for login
            password (str, optional): LinkedIn password for login
        
        Returns:
            Dict containing job details or empty dict if extraction fails
        """
        # Check cache first
        cached_job = self._job_description_cache.get(url)
        if cached_job:
            self.logger.info(f"Retrieved job description from cache: {url}")
            return cached_job
        
        # If not in cache, proceed with extraction
        try:
            # Perform login if credentials are provided
            if username and password:
                try:
                    self._linkedin_login(username, password)
                except Exception as e:
                    self.logger.error(f"Login failed: {e}")
                    return {}
            
            # Navigate to the URL
            self._driver.get(url)
            self.logger.info(f"Navigated to {url}")
            
            # Wait for page to load
            time.sleep(5)  # Increased wait time
                        
            # Extract job title with multiple fallback methods
            job_title_selectors = [
                (By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card__job-title"),
                (By.XPATH, "//h1[contains(@class, 'job-title')]")
            ]
            
            job_title = "N/A"
            for selector in job_title_selectors:
                self.logger.info(f"Trying title selector {selector}")
                try:
                    elements = self._driver.find_elements(*selector)
                    if elements:
                        job_title = elements[0].text
                        break
                except Exception as e:
                    self.logger.warning(f"Title selector {selector} failed: {e}")
            
            # Extract company name
            company_selectors = [
                (By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card__company-name"),
                (By.XPATH, "//span[contains(@class, 'company-name')]")
            ]
            
            company_name = "N/A"
            for selector in company_selectors:
                self.logger.info(f"Trying company selector {selector}")
                try:
                    elements = self._driver.find_elements(*selector)
                    if elements:
                        company_name = elements[0].text
                        break
                except Exception as e:
                    self.logger.warning(f"Company selector {selector} failed: {e}")

            # Define multiple potential selectors for job description
            job_desc_selectors = [
                (By.CLASS_NAME, "jobs-description__container"),
                (By.CSS_SELECTOR, "div[class*='description']"),
                (By.ID, "job-details"),
                (By.XPATH, "//div[contains(@class, 'description') or contains(@id, 'description')]")
            ]
            
            job_description = "N/A"            
            # Try multiple selectors to find job description
            for selector in job_desc_selectors:
                self.logger.info(f"Trying selector {selector}")
                try:
                    # Use find_elements to avoid NoSuchElementException
                    elements = self._driver.find_elements(*selector)
                    if elements:
                        job_desc_element = elements[0]
                        job_description = job_desc_element.text
                        break
                except Exception as e:
                    self.logger.warning(f"Selector {selector} failed: {e}")
            
            job_details = {
                "title": job_title.strip(),
                "company": company_name.strip(),
                "description": job_description.strip(),
                "url": url,
                "extracted_at": datetime.now().isoformat()
            }
            
            # Save to cache
            self._job_description_cache.save(job_details)
            
            return job_details
        
        except Exception as e:
            self.logger.error(f"Job description extraction failed: {e}")
            return {}
        finally:
            if self._driver:
                self._driver.quit()
    
    def extract_generic_job_description(self, url: str) -> Dict[str, str]:
        """
        Fallback method to extract job description using requests and BeautifulSoup
        
        Returns:
            Dictionary with job details
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Generic job description extraction (might need customization)
            job_title = soup.find(['h1', 'h2'], class_=['job-title', 'title'])
            company_name = soup.find(['span', 'div'], class_=['company-name', 'employer'])
            job_description = soup.find(['div', 'section'], class_=['job-description', 'description'])
            
            return {
                "title": job_title.text.strip() if job_title else "N/A",
                "company": company_name.text.strip() if company_name else "N/A",
                "description": job_description.text.strip() if job_description else "N/A"
            }
        
        except requests.RequestException as e:
            self.logger.error(f"Request error: {e}")
            return {}
    
    def extract(self, url: str) -> Dict[str, str]:
        """
        Main extraction method with platform-specific logic using pattern matching
        
        Args:
            url (str): The URL to extract job details from
        
        Returns:
            Extracted job details
        """
        match url:
            case url if "linkedin.com/jobs" in url:
                return self.extract_linkedin_job_description(url, *self._get_linkedin_credentials())
            case _:
                return self.extract_generic_job_description(url)

# Example usage
if __name__ == "__main__":
    url = "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=3959722886"
    extractor = JobPostingExtractor()
    job_details = extractor.extract(url)
    print(job_details)
