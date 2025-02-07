import logging
from typing import Optional, Dict, Any
import os
import hashlib
from pathlib import Path
import jsonlines

class JobDescriptionCache:
    """
    Manages caching of job descriptions to prevent redundant scraping
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the job description cache
        
        Args:
            cache_dir (str, optional): Directory to store cached job descriptions
        """
        # Use a default cache directory if not provided
        if cache_dir is None:
            cache_dir = os.path.join(
                os.path.expanduser("~"), 
                ".auto-cv", 
                "job_description_cache"
            )
        
        # Ensure cache directory exists
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache file path
        self.cache_file = self.cache_dir / "job_descriptions.jsonl"
        
        # In-memory cache for faster lookups
        self._load_cache()
    
    def _generate_url_hash(self, url: str) -> str:
        """
        Generate a unique hash for a given URL
        
        Args:
            url (str): Job description URL
        
        Returns:
            str: Unique hash identifier
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    def _load_cache(self) -> dict:
        """
        Load existing cache from JSONL file
        
        Returns:
            dict: Cached job descriptions
        """
        self._cache = {}
        
        if not self.cache_file.exists():
            return self._cache
        
        try:
            with jsonlines.open(self.cache_file, mode='r') as reader:
                for obj in reader:
                    self._cache[obj.get('url_hash')] = obj
        except Exception as e:
            logging.error(f"Error loading cache: {e}")
        
        return self._cache
    
    def get(self, url: str) -> dict:
        """
        Retrieve a cached job description
        
        Args:
            url (str): Job description URL
        
        Returns:
            dict: Cached job description or None
        """
        url_hash = self._generate_url_hash(url)
        return self._cache.get(url_hash)
    
    def save(self, job_description: dict) -> None:
        """
        Save a job description to cache
        
        Args:
            job_description (dict): Job description details
        """
        try:
            url_hash = self._generate_url_hash(job_description['url'])
            job_description['url_hash'] = url_hash
            
            # Update in-memory cache
            self._cache[url_hash] = job_description
            
            # Append to JSONL file
            with jsonlines.open(self.cache_file, mode='a') as writer:
                writer.write(job_description)
            
            logging.info(f"Cached job description: {url_hash}")
        
        except Exception as e:
            logging.error(f"Error saving to cache: {e}")
    
    def exists(self, url: str) -> bool:
        """
        Check if a job description is already cached
        
        Args:
            url (str): Job description URL
        
        Returns:
            bool: True if cached, False otherwise
        """
        url_hash = self._generate_url_hash(url)
        return url_hash in self._cache
