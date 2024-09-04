# utils.py
import re

def format_filename(name):
    """Sanitize and format filenames."""
    # Remove any invalid characters and replace spaces with underscores
    return re.sub(r'[^\w\-_\. ]', '_', name).strip()
