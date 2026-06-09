# ==========================================
# MODULE: UTILITY FUNCTIONS
# PURPOSE: Common helper functions
# ==========================================

from typing import Dict, Any, List
from datetime import datetime
import json
from pathlib import Path
import os
from app.config import get_settings, get_upload_dir


# ==========================================
# FILE UTILITIES
# PURPOSE: Handle file operations
# ==========================================

def save_uploaded_file(file_content: bytes, filename: str, subfolder: str = "") -> str:
    """
    Save uploaded file to disk.
    
    Args:
        file_content: File content bytes
        filename: Original filename
        subfolder: Subfolder within upload directory
    
    Returns:
        Path to saved file
    """
    settings = get_settings()
    upload_dir = get_upload_dir()
    
    if subfolder:
        file_dir = upload_dir / subfolder
        file_dir.mkdir(parents=True, exist_ok=True)
    else:
        file_dir = upload_dir
    
    # Generate unique filename to avoid collisions
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
    safe_filename = timestamp + filename
    file_path = file_dir / safe_filename
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    return str(file_path)


def delete_file(file_path: str) -> bool:
    """
    Delete a file from disk.
    
    Args:
        file_path: Path to file to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
    except Exception:
        pass
    
    return False


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
    
    Returns:
        File size in bytes, 0 if file not found
    """
    try:
        return Path(file_path).stat().st_size
    except Exception:
        return 0


# ==========================================
# JSON UTILITIES
# PURPOSE: Handle JSON serialization
# ==========================================

def json_to_dict(json_str: str) -> Dict[str, Any]:
    """
    Convert JSON string to dictionary.
    
    Args:
        json_str: JSON string
    
    Returns:
        Dictionary, empty dict if invalid
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return {}


def dict_to_json(data: Dict[str, Any]) -> str:
    """
    Convert dictionary to JSON string.
    
    Args:
        data: Dictionary to convert
    
    Returns:
        JSON string
    """
    return json.dumps(data, default=str)


# ==========================================
# PAGINATION UTILITIES
# PURPOSE: Handle pagination
# ==========================================

def get_pagination_params(skip: int = 0, limit: int = 50) -> tuple:
    """
    Validate and return pagination parameters.
    
    Args:
        skip: Number of items to skip
        limit: Number of items to return
    
    Returns:
        (skip, limit) tuple with validated values
    """
    # Ensure skip is non-negative
    skip = max(0, skip)
    
    # Ensure limit is between 1 and 100
    limit = max(1, min(100, limit))
    
    return skip, limit


def paginate_list(items: List[Any], skip: int = 0, limit: int = 50) -> tuple:
    """
    Paginate a list.
    
    Args:
        items: List of items to paginate
        skip: Number of items to skip
        limit: Number of items to return
    
    Returns:
        (paginated_items, total_count) tuple
    """
    skip, limit = get_pagination_params(skip, limit)
    total = len(items)
    paginated = items[skip:skip + limit]
    
    return paginated, total


# ==========================================
# TEXT UTILITIES
# PURPOSE: Text processing
# ==========================================

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_number(num: float, decimal_places: int = 2) -> str:
    """
    Format number with specified decimal places.
    
    Args:
        num: Number to format
        decimal_places: Number of decimal places
    
    Returns:
        Formatted number string
    """
    return f"{num:.{decimal_places}f}"


# ==========================================
# DATE/TIME UTILITIES
# PURPOSE: Date and time operations
# ==========================================

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return ""
    
    return dt.strftime(format_str)


def days_since(dt: datetime) -> int:
    """
    Calculate days since a datetime.
    
    Args:
        dt: Datetime object
    
    Returns:
        Number of days since
    """
    if dt is None:
        return 0
    
    delta = datetime.utcnow() - dt
    return delta.days


# ==========================================
# STATISTICS UTILITIES
# PURPOSE: Calculate statistics
# ==========================================

def calculate_percentage(value: float, total: float) -> float:
    """
    Calculate percentage.
    
    Args:
        value: Current value
        total: Total value
    
    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0
    
    return (value / total) * 100


def calculate_average(values: List[float]) -> float:
    """
    Calculate average of values.
    
    Args:
        values: List of numeric values
    
    Returns:
        Average value
    """
    if not values:
        return 0.0
    
    return sum(values) / len(values)


def get_growth_rate(current: float, previous: float) -> float:
    """
    Calculate growth rate as percentage.
    
    Args:
        current: Current value
        previous: Previous value
    
    Returns:
        Growth rate percentage
    """
    if previous == 0:
        return 0.0
    
    return ((current - previous) / abs(previous)) * 100
