"""
File Utility Module
Provides file system operations for code analysis
"""

import os
import logging
from typing import List, Optional
from constants import (
    SKIP_DIRECTORIES,
    SKIP_FILE_PATTERNS,
    FILE_LIMITS,
    EXTENSION_TO_LANGUAGE,
)

logger = logging.getLogger(__name__)


class FileUtils:
    """Utility class for file system operations"""
    
    @staticmethod
    def should_skip_directory(dir_name: str) -> bool:
        """
        Check if directory should be skipped during analysis.
        
        Args:
            dir_name: Directory name
            
        Returns:
            True if should skip, False otherwise
        """
        return dir_name in SKIP_DIRECTORIES or dir_name.startswith('.')
    
    @staticmethod
    def should_skip_file(file_name: str) -> bool:
        """
        Check if file should be skipped during analysis.
        
        Args:
            file_name: File name
            
        Returns:
            True if should skip, False otherwise
        """
        # Check against SKIP_FILE_PATTERNS
        import fnmatch
        for pattern in SKIP_FILE_PATTERNS:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        
        # Skip hidden files
        if file_name.startswith('.'):
            return True
        
        # Skip backup files
        if file_name.endswith(('~', '.bak', '.backup', '.old')):
            return True
        
        return False
    
    @staticmethod
    def is_valid_source_file(
        file_path: str,
        supported_extensions: Optional[List[str]],
        max_file_size: Optional[int] = None
    ) -> bool:
        """
        Check if file is a valid source code file.
        
        Args:
            file_path: Path to the file
            supported_extensions: List of supported extensions
            
        Returns:
            True if valid source file, False otherwise
        """
        # Check extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        extensions = supported_extensions or list(EXTENSION_TO_LANGUAGE.keys())
        if ext not in extensions:
            return False
        
        # Check file size
        try:
            file_size = os.path.getsize(file_path)
            max_size = max_file_size if max_file_size is not None else FILE_LIMITS.get('MAX_FILE_BYTES', 500000)
            if file_size > max_size:
                logger.warning(f"Skipping large file: {file_path} ({file_size} bytes)")
                return False
        except OSError:
            return False
        
        return True
    
    @staticmethod
    def find_source_files(
        root_dir: str,
        supported_extensions: Optional[List[str]] = None,
        max_files: int = 1000,
        max_file_size: Optional[int] = None
    ) -> List[str]:
        """
        Recursively find all source files in directory.
        
        Args:
            root_dir: Root directory to search
            supported_extensions: List of supported file extensions
            max_files: Maximum number of files to return
            
        Returns:
            List of file paths
        """
        extensions = supported_extensions or list(EXTENSION_TO_LANGUAGE.keys())
        source_files = []
        
        try:
            for root, dirs, files in os.walk(root_dir):
                # Filter out directories to skip
                dirs[:] = [d for d in dirs if not FileUtils.should_skip_directory(d)]
                
                # Process files
                for file in files:
                    # Check if we've reached max files
                    if len(source_files) >= max_files:
                        logger.warning(f"Reached maximum file limit: {max_files}")
                        return source_files
                    
                    # Skip unwanted files
                    if FileUtils.should_skip_file(file):
                        continue
                    
                    # Build full path
                    file_path = os.path.join(root, file)
                    
                    # Check if valid source file
                    if FileUtils.is_valid_source_file(file_path, extensions, max_file_size):
                        source_files.append(file_path)
            
            logger.info(f"Found {len(source_files)} source files in {root_dir}")
            return source_files
            
        except Exception as e:
            logger.error(f"Error finding source files: {e}")
            return source_files
    
    @staticmethod
    def get_package_path(file_path: str, root_dir: str) -> str:
        """
        Get package/module path for a file.
        
        Args:
            file_path: Full path to the file
            root_dir: Root directory of the project
            
        Returns:
            Package path (e.g., "com.example.project")
        """
        try:
            # Get relative path
            rel_path = os.path.relpath(file_path, root_dir)
            
            # Remove file name and extension
            dir_path = os.path.dirname(rel_path)
            
            # Convert path separators to dots
            package = dir_path.replace(os.sep, '.')
            
            # Remove leading/trailing dots
            package = package.strip('.')
            
            return package or 'main'
            
        except Exception as e:
            logger.error(f"Error getting package path: {e}")
            return 'main'
    
    @staticmethod
    def read_file_safe(file_path: str, encoding: str = 'utf-8') -> str:
        """
        Safely read file contents with error handling.
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            
        Returns:
            File contents or empty string on error
        """
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""
    
    @staticmethod
    def ensure_directory(dir_path: str):
        """
        Ensure directory exists, create if it doesn't.
        
        Args:
            dir_path: Path to directory
        """
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        Get file extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            File extension with dot (e.g., '.py')
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower()
    
    @staticmethod
    def get_relative_path(file_path: str, base_dir: str) -> str:
        """
        Get relative path from base directory.
        
        Args:
            file_path: Full file path
            base_dir: Base directory
            
        Returns:
            Relative path
        """
        try:
            return os.path.relpath(file_path, base_dir)
        except Exception:
            return file_path
    
    @staticmethod
    def group_files_by_language(
        files: List[str],
        extension_map: Optional[dict] = None
    ) -> dict:
        """
        Group files by programming language.
        
        Args:
            files: List of file paths
            extension_map: Mapping of extensions to languages
            
        Returns:
            Dictionary mapping language to list of files
        """
        grouped = {}
        
        mapping = extension_map or EXTENSION_TO_LANGUAGE

        for file in files:
            ext = FileUtils.get_file_extension(file)
            language = mapping.get(ext, 'unknown')
            
            if language not in grouped:
                grouped[language] = []
            grouped[language].append(file)
        
        return grouped
    
    @staticmethod
    def calculate_directory_stats(root_dir: str) -> dict:
        """
        Calculate statistics about directory.
        
        Args:
            root_dir: Root directory
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_files': 0,
            'total_dirs': 0,
            'total_size': 0,
            'file_types': {}
        }
        
        try:
            for root, dirs, files in os.walk(root_dir):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                stats['total_dirs'] += len(dirs)
                stats['total_files'] += len(files)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stats['total_size'] += os.path.getsize(file_path)
                        
                        ext = FileUtils.get_file_extension(file)
                        stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                    except OSError:
                        continue
        
        except Exception as e:
            logger.error(f"Error calculating directory stats: {e}")
        
        return stats
