# utils.py
import re

def format_filename(name):
    """Sanitize and format filenames."""
    # Remove any invalid characters and replace spaces with underscores
    return re.sub(r'[^\w\-_\. ]', '_', name).strip()

def remove_extension(file_name, extension='.html'):
    """Remove a specific extension from a filename."""
    if file_name.endswith(extension):
        return file_name[:-len(extension)]
    return file_name
