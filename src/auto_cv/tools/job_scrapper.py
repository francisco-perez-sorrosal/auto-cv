from crewai.tools import BaseTool

from auto_cv.cache import BasicInMemoryCache
from auto_cv.tools.web_scraper import JobPostingExtractor
from llm_foundation import logger

class JobScrapperTool(BaseTool):
    name: str = "Job Scrapper Tool"
    description: str = "Extract job details from a given URL."
        
    def _run(self, url: str) -> dict:
        """
        Extract job details from a given URL.
        """
        
        extractor = JobPostingExtractor()
        job_details, cache_hit = extractor.extract_raw_info_from(url)
        logger.info(f"Job detains (cache hit: {cache_hit}):\n{job_details}")
        return job_details
