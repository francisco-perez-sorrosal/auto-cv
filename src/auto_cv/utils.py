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
