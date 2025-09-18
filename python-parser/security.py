"""
Security utilities for safe operations
"""
import re
import urllib.parse
from typing import Dict, Tuple

def validate_github_url(url: str) -> Tuple[bool, str, Dict]:
    """
    Validates and sanitizes GitHub URL for safe cloning
    
    Returns:
        (is_valid, error_message, parsed_info)
    """
    if not url or not isinstance(url, str):
        return False, "URL is required and must be a string", {}
    
    url = url.strip()
    
    # Basic URL format validation
    github_pattern = r'^https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/?$'
    match = re.match(github_pattern, url)
    
    if not match:
        return False, "Invalid GitHub URL format. Expected: https://github.com/username/repository", {}
    
    username, repository = match.groups()
    
    # Additional security checks
    if '..' in username or '..' in repository:
        return False, "Invalid characters in username or repository name", {}
    
    if username.startswith('.') or repository.startswith('.'):
        return False, "Username and repository cannot start with dot", {}
    
    # Remove common suffixes
    if repository.endswith('.git'):
        repository = repository[:-4]
    
    # Parse URL to ensure it's well-formed
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != 'https' or parsed.netloc != 'github.com':
            return False, "Only HTTPS GitHub URLs are allowed", {}
    except Exception:
        return False, "Malformed URL", {}
    
    return True, "", {
        'username': username,
        'repository': repository,
        'clean_url': f"https://github.com/{username}/{repository}.git",
        'display_name': f"{username}/{repository}"
    }

def sanitize_file_path(path: str, base_path: str) -> Tuple[bool, str]:
    """
    Ensures file path is safe and within base directory
    
    Returns:
        (is_safe, sanitized_path)
    """
    import os
    
    try:
        # Normalize and resolve the path
        normalized_path = os.path.normpath(os.path.join(base_path, path))
        abs_base = os.path.abspath(base_path)
        abs_path = os.path.abspath(normalized_path)
        
        # Check if path is within base directory
        if not abs_path.startswith(abs_base):
            return False, "Path traversal detected"
        
        # Additional checks for suspicious patterns
        if '..' in path or path.startswith('/') or ':' in path:
            return False, "Unsafe path pattern detected"
        
        return True, abs_path
    except Exception as e:
        return False, f"Path validation error: {str(e)}"

def validate_environment_limits() -> Dict:
    """
    Validates and returns safe environment limits
    """
    import os
    
    try:
        max_files = min(int(os.getenv('MAX_FILES', '5000')), 10000)  # Cap at 10k
        max_bytes = min(int(os.getenv('MAX_FILE_BYTES', '500000')), 2_000_000)  # Cap at 2MB
        clone_depth = max(1, min(int(os.getenv('GIT_CLONE_DEPTH', '1')), 10))  # 1-10 range
        timeout = min(int(os.getenv('ANALYZE_TIMEOUT', '300')), 600)  # Cap at 10 minutes
        
        return {
            'max_files': max_files,
            'max_bytes': max_bytes,
            'clone_depth': clone_depth,
            'timeout': timeout
        }
    except ValueError as e:
        # Return safe defaults if environment variables are invalid
        return {
            'max_files': 5000,
            'max_bytes': 500000,
            'clone_depth': 1,
            'timeout': 300
        }