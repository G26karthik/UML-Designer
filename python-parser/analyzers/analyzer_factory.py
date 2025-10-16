"""
Analyzer Factory Module
Factory pattern to select and create appropriate language analyzers
"""

import logging
from typing import Dict, List, Optional
from .base_analyzer import BaseAnalyzer
from .python_analyzer import PythonAnalyzer
from .java_analyzer import JavaAnalyzer
from .csharp_analyzer import CSharpAnalyzer
from .typescript_analyzer import TypeScriptAnalyzer
from .cpp_analyzer import CppAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerFactory:
    """
    Factory class to create and manage language-specific analyzers.
    Uses Strategy pattern to select appropriate analyzer based on file extension.
    """
    
    # Map file extensions to analyzer classes
    ANALYZER_MAP = {
        '.py': PythonAnalyzer,
        '.java': JavaAnalyzer,
        '.cs': CSharpAnalyzer,
        '.ts': TypeScriptAnalyzer,
        '.tsx': TypeScriptAnalyzer,
        '.js': TypeScriptAnalyzer,
        '.jsx': TypeScriptAnalyzer,
        '.cpp': CppAnalyzer,
        '.cc': CppAnalyzer,
        '.cxx': CppAnalyzer,
        '.c': CppAnalyzer,
        '.h': CppAnalyzer,
        '.hpp': CppAnalyzer,
    }
    
    def __init__(self):
        """Initialize factory with analyzer instances"""
        self.analyzers: Dict[str, BaseAnalyzer] = {}
        self._initialize_analyzers()
    
    def _initialize_analyzers(self):
        """Create instances of all analyzers"""
        self.analyzers = {
            'python': PythonAnalyzer(),
            'java': JavaAnalyzer(),
            'csharp': CSharpAnalyzer(),
            'typescript': TypeScriptAnalyzer(),
            'cpp': CppAnalyzer(),
        }
        logger.info(f"Initialized {len(self.analyzers)} language analyzers")
    
    def get_analyzer(self, file_path: str) -> Optional[BaseAnalyzer]:
        """
        Get the appropriate analyzer for a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Analyzer instance if supported, None otherwise
        """
        # Get file extension
        extension = self._get_extension(file_path)
        
        # Get analyzer class
        analyzer_class = self.ANALYZER_MAP.get(extension)
        
        if analyzer_class:
            # Get language key
            for lang, analyzer in self.analyzers.items():
                if isinstance(analyzer, analyzer_class):
                    return analyzer
        
        logger.debug(f"No analyzer found for file: {file_path}")
        return None
    
    def can_analyze(self, file_path: str) -> bool:
        """
        Check if factory has an analyzer for the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file can be analyzed, False otherwise
        """
        extension = self._get_extension(file_path)
        return extension in self.ANALYZER_MAP
    
    def _get_extension(self, file_path: str) -> str:
        """
        Extract file extension from path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File extension with dot (e.g., '.py')
        """
        import os
        _, ext = os.path.splitext(file_path)
        return ext.lower()
    
    def analyze_file(self, file_path: str, package_path: str = "") -> List[Dict]:
        """
        Analyze a file using the appropriate analyzer.
        
        Args:
            file_path: Path to the file to analyze
            package_path: Package/module path
            
        Returns:
            List of class dictionaries
        """
        analyzer = self.get_analyzer(file_path)
        
        if not analyzer:
            logger.warning(f"No analyzer available for: {file_path}")
            return []
        
        try:
            return analyzer.analyze_file(file_path, package_path)
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return []
    
    def detect_all_relationships(self, all_classes: List[Dict]) -> List[Dict]:
        """
        Collect relationships from all analyzers.
        
        Args:
            all_classes: List of all analyzed classes
            
        Returns:
            Combined list of all relationships
        """
        all_relationships = []
        
        for analyzer in self.analyzers.values():
            relationships = analyzer.detect_relationships(all_classes)
            all_relationships.extend(relationships)
        
        # Deduplicate relationships
        unique_rels = []
        seen = set()
        
        for rel in all_relationships:
            key = (rel.get('from'), rel.get('to'), rel.get('type'))
            if key not in seen:
                seen.add(key)
                unique_rels.append(rel)
        
        logger.info(f"Detected {len(unique_rels)} unique relationships")
        return unique_rels
    
    def extract_all_endpoints(self, file_paths: List[str]) -> List[Dict]:
        """
        Extract endpoints from all supported files.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            Combined list of all endpoints
        """
        all_endpoints = []
        
        for file_path in file_paths:
            analyzer = self.get_analyzer(file_path)
            if analyzer:
                endpoints = analyzer.extract_endpoints(file_path)
                all_endpoints.extend(endpoints)
        
        logger.info(f"Extracted {len(all_endpoints)} endpoints")
        return all_endpoints
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of supported extensions
        """
        return list(self.ANALYZER_MAP.keys())
    
    def get_analyzer_stats(self) -> Dict:
        """
        Get statistics about all analyzers.
        
        Returns:
            Dictionary with analyzer statistics
        """
        stats = {}
        
        for lang, analyzer in self.analyzers.items():
            stats[lang] = {
                'classes_found': len(analyzer.class_names),
                'relationships': len(analyzer.relationships),
            }
        
        return stats
    
    def reset_all_analyzers(self):
        """Reset all analyzers to fresh state"""
        self._initialize_analyzers()
        logger.info("All analyzers reset")
