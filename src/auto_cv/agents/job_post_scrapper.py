import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

@dataclass
class JobPostingExtractor:
    """
    A robust class for extracting job description details from various job posting URLs.
    
    Supports multiple job platforms with fallback mechanisms.
    """
    
    url: str
    timeout: int = 10
    _driver: Optional[Any] = None
    
    def __post_init__(self):
        """Initialize logging and setup chrome options"""
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
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
    
    def extract_linkedin_job_description(self) -> Dict[str, str]:
        """
        Extract job description from LinkedIn job posting
        
        Returns:
            Dictionary with job details
        """
        if not self._driver:
            self._driver = self._setup_webdriver()
        
        try:
            self._driver.get(self.url)
            
            # Wait for job description to load
            job_desc_element = WebDriverWait(self._driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-description__container"))
            )
            
            job_title = self._driver.find_element(By.CLASS_NAME, "t-24").text
            company_name = self._driver.find_element(By.CLASS_NAME, "t-16").text
            job_description = job_desc_element.text
            
            return {
                "title": job_title,
                "company": company_name,
                "description": job_description
            }
        
        except TimeoutException:
            self.logger.error(f"Timeout while loading job description for {self.url}")
            return {}
        except WebDriverException as e:
            self.logger.error(f"WebDriver error: {e}")
            return {}
        finally:
            if self._driver:
                self._driver.quit()
    
    def extract_generic_job_description(self) -> Dict[str, str]:
        """
        Fallback method to extract job description using requests and BeautifulSoup
        
        Returns:
            Dictionary with job details
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=self.timeout)
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
    
    def extract(self) -> Dict[str, str]:
        """
        Main extraction method with platform-specific logic
        
        Returns:
            Extracted job details
        """
        if "linkedin.com/jobs" in self.url:
            return self.extract_linkedin_job_description()
        else:
            return self.extract_generic_job_description()

# Example usage
if __name__ == "__main__":
    url = "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=3959722886"
    extractor = JobPostingExtractor(url)
    job_details = extractor.extract()
    print(job_details)