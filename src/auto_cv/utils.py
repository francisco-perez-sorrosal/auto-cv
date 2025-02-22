from datetime import datetime
from typing import Any

def make_serializable(structure: dict[str, Any]) -> dict[str, Any]:
        """
        Convert complex objects to JSON-serializable format
        
        Args:
            structure (dict): Original structure to be serialized
        
        Returns:
            dict: Serializable version of the structure
        """
        def serialize_value(value):
            if isinstance(value, datetime):
                return value.isoformat()
            return value
        
        return {k: serialize_value(v) for k, v in structure.items()}


def find_files_with_extension(directory: str, extension: str = ".pdf") -> list[str]:
    """
    Find all files with a particular extension from a directory
    
    Args:
        directory (str): Starting directory to search
        extension (str, optional): File extension to be searched. Defaults to ".pdf".
    
    Returns:
        list: List of absolute root paths of files found
    """
    import os
    from glob import glob

    files = []
    for path in glob(f"{directory}/**/*{extension}", recursive=True):
        files.append(os.path.abspath(path))

    return files
