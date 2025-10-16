"""
Base Analyzer Module
Provides abstract base class for all language-specific analyzers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """
    Abstract base class for language-specific code analyzers.
    All language analyzers should inherit from this class.
    """
    
    def __init__(self):
        """Initialize the analyzer"""
        self.logger = logger
        self.class_names = set()
        self.relationships = []
    
    @abstractmethod
    def can_analyze(self, file_path: str) -> bool:
        """
        Check if this analyzer can handle the given file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            True if this analyzer can handle the file, False otherwise
        """
        pass
    
    @abstractmethod
    def analyze_file(self, file_path: str, package_path: str = "") -> Dict:
        """
        Analyze a single file and extract classes, fields, methods.
        
        Args:
            file_path: Path to the file to analyze
            package_path: Package or namespace path
            
        Returns:
            Dictionary containing extracted class information:
            {
                'class': 'ClassName',
                'fields': ['field1: Type', 'field2'],
                'methods': ['method1', 'method2'],
                'stereotype': 'class|interface|abstract',
                'abstract': False,
                'package': 'package.name'
            }
        """
        pass
    
    @abstractmethod
    def detect_relationships(self, all_classes: List[Dict]) -> List[Dict]:
        """
        Detect relationships between classes.
        
        Args:
            all_classes: List of all analyzed classes
            
        Returns:
            List of relationship dictionaries:
            [{
                'from': 'ClassA',
                'to': 'ClassB',
                'type': 'extends|implements|uses|composition|aggregation',
                'source': 'heuristic'
            }]
        """
        pass
    
    def normalize_type_name(self, name: str) -> str:
        """
        Normalize type name by removing generics, arrays, and namespace separators.
        
        Args:
            name: Raw type name string
            
        Returns:
            Normalized type name
        """
        import re
        
        if not name:
            return name
        
        # Strip generics and arrays
        n = re.sub(r'<[^>]*>', '', str(name))
        n = n.replace('[]', '')
        
        # Remove namespace separators
        if '::' in n:
            n = n.split('::')[-1]
        if '.' in n:
            n = n.split('.')[-1]
        
        return n.strip()
    
    def is_class_known(self, class_name: str) -> bool:
        """
        Check if a class name is in the list of known classes.
        
        Args:
            class_name: Name of the class to check
            
        Returns:
            True if class is known, False otherwise
        """
        return class_name in self.class_names
    
    def add_class_name(self, class_name: str):
        """
        Add a class name to the list of known classes.
        
        Args:
            class_name: Name of the class to add
        """
        self.class_names.add(class_name)
    
    def add_relationship(self, from_class: str, to_class: str, rel_type: str):
        """
        Add a relationship to the list of relationships.
        
        Args:
            from_class: Source class name
            to_class: Target class name
            rel_type: Type of relationship (extends, implements, uses, etc.)
        """
        self.relationships.append({
            'from': from_class,
            'to': to_class,
            'type': rel_type,
            'source': 'heuristic'
        })
    
    def get_language_name(self) -> str:
        """
        Get the language name for this analyzer.
        
        Returns:
            Language name (e.g., 'python', 'java', 'csharp')
        """
        return self.__class__.__name__.replace('Analyzer', '').lower()
    
    def log_info(self, message: str, **kwargs):
        """Log an info message"""
        self.logger.info(f"[{self.get_language_name()}] {message}", extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log an error message"""
        self.logger.error(f"[{self.get_language_name()}] {message}", extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log a warning message"""
        self.logger.warning(f"[{self.get_language_name()}] {message}", extra=kwargs)
    
    def create_class_dict(self, 
                         class_name: str,
                         fields: List[str] = None,
                         methods: List[str] = None,
                         stereotype: str = 'class',
                         abstract: bool = False,
                         package: str = '') -> Dict:
        """
        Create a standardized class dictionary.
        
        Args:
            class_name: Name of the class
            fields: List of field definitions
            methods: List of method names
            stereotype: Class stereotype (class, interface, abstract, etc.)
            abstract: Whether the class is abstract
            package: Package or namespace name
            
        Returns:
            Standardized class dictionary
        """
        return {
            'class': class_name,
            'fields': fields or [],
            'methods': methods or [],
            'stereotype': stereotype,
            'abstract': abstract,
            'package': package
        }
