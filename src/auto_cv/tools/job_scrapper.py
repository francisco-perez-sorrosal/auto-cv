from crewai.tools import BaseTool

from auto_cv.agents.web_scraper import JobPostingExtractor
from llm_foundation import logger

class JobScrapperTool(BaseTool):
    name: str = "Job Scrapper Tool"
    description: str = "Extract job details from a given URL."
        
    def _run(self, url: str) -> dict:
        """
        Extract job details from a given URL.
        """
        extractor = JobPostingExtractor()
        job_details = extractor.extract(url)
        logger.info(f"Job detains:\n{job_details}")
        return job_details