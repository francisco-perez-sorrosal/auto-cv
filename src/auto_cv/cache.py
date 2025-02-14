import logging
import os
from pathlib import Path
import jsonlines

class BasicInMemoryCache:
    """
    Manages caching of json objects to prevent redundant actions
    """
    
    def __init__(self, 
                app_name: str, 
                cache_subdir: str, 
                cache_file: str, 
                cache_key_name: str,
                base_cache_dir: str | None = None):
        """
        Initialize the job description cache
        
        Args:
            app_name (str): Name of the application
            cache_subdir (str): Subdirectory for cache storage
            cache_file (str): Name of the cache file
            cache_key_name (str): Name of the key to use for finding elements in the cache
            base_cache_dir (str, optional): Base directory for cache storage
        """
        # Store the cache key name
        self.cache_key_name = cache_key_name
        
        # Use a default cache directory if not provided
        if base_cache_dir is None:
            base_cache_dir = os.path.expanduser("~")
        
        cache_dir = os.path.join(
            base_cache_dir, 
            f".{app_name}", 
            cache_subdir
        )
        
        # Ensure cache directory exists
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache file path
        self.cache_file = self.cache_dir / cache_file
        
        # In-memory cache for faster lookups
        self._load_cache()

    def _load_cache(self) -> dict[str, dict]:
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
                    # Use the specified cache key name to create the cache index
                    cache_index = obj.get(self.cache_key_name)
                    if cache_index:
                        self._cache[cache_index] = obj
        except Exception as e:
            logging.error(f"Error loading cache: {e}")
        
        return self._cache
    
    def get(self, key_value: str) -> dict | None:
        """
        Retrieve a cached item by its key
        
        Args:
            key_value (str): Key to look up in the cache
        
        Returns:
            Optional[dict]: Cached item or None if not found
        """
        return self._cache.get(key_value)
    

    def put(self, structure: dict) -> bool:
        """
        Save an item to cache using the specified cache key name
        
        Args:
            structure (dict): Item details to be cached
        
        Returns:
            bool: True if item was added to cache, False if item already exists
        """
        try:
            # Get the cache index using the specified cache key name
            cache_index = structure.get(self.cache_key_name)
            
            if not cache_index:
                logging.warning(f"No value found for cache key name '{self.cache_key_name}'")
                return False
            
            # Check if the item already exists in the cache
            if self.exists(cache_index):
                logging.warning(f"Item with key {cache_index} already exists in cache. Skipping...")
                return False
            
            # Update in-memory cache
            self._cache[cache_index] = structure
            
            # Append to JSONL file
            with jsonlines.open(self.cache_file, mode='a') as writer:
                writer.write(structure)
            
            logging.info(f"Cached new item with key: {cache_index}")
            return True
        
        except Exception as e:
            logging.error(f"Error saving to cache: {e}")
            return False
                        
    def exists(self, key_value: str) -> bool:
        """
        Check if an item exists in the cache based on the specified cache key
        
        Args:
            key_value (str): Value of the cache key to look up
        
        Returns:
            bool: True if item exists in cache, False otherwise
        """
        return key_value in self._cache
