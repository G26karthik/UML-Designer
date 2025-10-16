"""
C/C++ Analyzer Module
Analyzes C and C++ source code using regex patterns
"""

import re
import logging
from typing import Dict, List, Set
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class CppAnalyzer(BaseAnalyzer):
    """
    Analyzer for C and C++ source code.
    Uses regex-based parsing for struct/class extraction.
    """
    
    def __init__(self):
        super().__init__()
        self.includes = set()
        self.compositions = []
        self.usages = []
    
    def can_analyze(self, file_path: str) -> bool:
        """Check if file is C/C++ file"""
        return file_path.endswith(('.c', '.cpp', '.cc', '.cxx', '.h', '.hpp'))
    
    def analyze_file(self, file_path: str, package_path: str = "") -> List[Dict]:
        """
        Analyze a C/C++ file and extract classes, structs, fields, methods.
        
        Args:
            file_path: Path to the C/C++ file
            package_path: Namespace path
            
        Returns:
            List of class/struct dictionaries
        """
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            # Remove comments
            source = self._remove_comments(source)
            
            # Extract includes
            self._extract_includes(source)
            
            # Analyze classes
            classes.extend(self._analyze_classes(source, package_path))
            
            # Analyze structs
            classes.extend(self._analyze_structs(source, package_path))
            
            self.log_info(f"Analyzed {file_path}: found {len(classes)} classes/structs")
            
        except Exception as e:
            self.log_error(f"Error analyzing {file_path}: {e}")
        
        return classes
    
    def _remove_comments(self, source: str) -> str:
        """Remove C/C++ comments from source"""
        # Remove single-line comments
        source = re.sub(r'//.*?$', '', source, flags=re.MULTILINE)
        # Remove multi-line comments
        source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)
        return source
    
    def _extract_includes(self, source: str):
        """Extract #include statements"""
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        for match in re.finditer(include_pattern, source):
            header = match.group(1)
            # Extract just the filename without .h/.hpp
            header_name = header.split('/')[-1].split('.')[0]
            self.includes.add(header_name)
    
    def _analyze_classes(self, source: str, package_path: str) -> List[Dict]:
        """Extract and analyze all classes in the source"""
        classes = []
        
        # Class pattern: class ClassName [: public BaseClass] {
        class_pattern = r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([^{]+))?\s*{'
        
        for match in re.finditer(class_pattern, source):
            class_name = match.group(1)
            self.add_class_name(class_name)
            
            # Extract base classes
            if match.group(2):
                self._extract_inheritance(match.group(2), class_name)
            
            # Extract class body
            class_content = self._extract_class_content(source, match.start())
            
            # Extract fields and methods
            fields, methods = self._extract_members(class_content, class_name, is_class=True)
            
            # Heuristic analysis
            self._heuristic_analysis(class_content, class_name, fields)
            
            class_dict = self.create_class_dict(
                class_name=class_name,
                fields=sorted(list(fields)),
                methods=sorted(list(methods)),
                stereotype='class',
                abstract=False,
                package=package_path
            )
            
            classes.append(class_dict)
        
        return classes
    
    def _analyze_structs(self, source: str, package_path: str) -> List[Dict]:
        """Extract and analyze all structs in the source"""
        structs = []
        
        # Struct pattern: struct StructName {
        struct_pattern = r'\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)\s*{'
        
        for match in re.finditer(struct_pattern, source):
            struct_name = match.group(1)
            self.add_class_name(struct_name)
            
            # Extract struct body
            struct_content = self._extract_class_content(source, match.start())
            
            # Extract fields only (structs typically don't have methods in C)
            fields, methods = self._extract_members(struct_content, struct_name, is_class=False)
            
            struct_dict = self.create_class_dict(
                class_name=struct_name,
                fields=sorted(list(fields)),
                methods=sorted(list(methods)),
                stereotype='class',
                abstract=False,
                package=package_path
            )
            
            structs.append(struct_dict)
        
        return structs
    
    def _extract_inheritance(self, inheritance_str: str, class_name: str):
        """
        Extract base classes from inheritance string.
        
        Args:
            inheritance_str: Inheritance declaration (e.g., "public Base1, private Base2")
            class_name: Name of the current class
        """
        # Split by comma
        parts = inheritance_str.split(',')
        
        for part in parts:
            # Remove access specifiers (public, private, protected, virtual)
            clean_part = re.sub(r'\b(public|private|protected|virtual)\b', '', part).strip()
            
            if clean_part:
                base_name = clean_part.split()[-1]  # Get last word (the base class name)
                if base_name:
                    self.add_relationship(base_name, class_name, 'extends')
    
    def _extract_members(self, content: str, class_name: str, is_class: bool) -> tuple:
        """
        Extract fields and methods from class/struct body.
        
        Args:
            content: Class/struct body text
            class_name: Name of the class/struct
            is_class: True if class, False if struct
            
        Returns:
            Tuple of (fields_set, methods_set)
        """
        fields = set()
        methods = set()
        
        # Extract fields: Type fieldName; or Type* fieldName;
        field_pattern = r'\b([A-Za-z_][A-Za-z0-9_]*[\s*&]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;'
        for match in re.finditer(field_pattern, content):
            field_type = match.group(1).strip()
            field_name = match.group(2)
            
            # Filter out likely non-fields
            if field_name not in {'public', 'private', 'protected', 'static', 'const', 'virtual'}:
                fields.add(f"{field_name}: {field_type}")
                
                # Track composition
                clean_type = field_type.replace('*', '').replace('&', '').strip()
                if clean_type != class_name:
                    self.compositions.append({
                        'from': class_name,
                        'to': clean_type,
                        'type': 'composition',
                        'source': 'heuristic'
                    })
        
        if is_class:
            # Extract methods: ReturnType methodName(...) or ReturnType methodName(...) const
            method_pattern = r'\b([A-Za-z_][A-Za-z0-9_]*[\s*&]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)'
            for match in re.finditer(method_pattern, content):
                method_name = match.group(2)
                
                # Filter out likely non-methods
                if method_name not in {'if', 'while', 'for', 'switch', 'return', 'sizeof', 
                                      'public', 'private', 'protected', 'static', 'const', 'virtual'}:
                    methods.add(method_name)
        
        return fields, methods
    
    def _heuristic_analysis(self, class_content: str, class_name: str, fields: Set):
        """
        Perform heuristic analysis to detect relationships.
        
        Args:
            class_content: Class body text
            class_name: Name of the class
            fields: Set to add discovered fields to
        """
        # new OtherClass() or new OtherClass
        for match in re.finditer(r'\bnew\s+([A-Za-z_][A-Za-z0-9_]*)', class_content):
            other_class = match.group(1)
            if other_class != class_name:
                self.usages.append({
                    'from': class_name,
                    'to': other_class,
                    'type': 'uses',
                    'source': 'heuristic'
                })
        
        # OtherClass::method() (static calls)
        for match in re.finditer(
            r'\b([A-Za-z_][A-Za-z0-9_]*)\s*::\s*[A-Za-z_][A-Za-z0-9_]*\s*\(',
            class_content
        ):
            other_class = match.group(1)
            if other_class != class_name:
                self.usages.append({
                    'from': class_name,
                    'to': other_class,
                    'type': 'uses',
                    'source': 'heuristic'
                })
        
        # object.method() where object might be of another class
        for match in re.finditer(
            r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\(',
            class_content
        ):
            other_class = match.group(1)
            if other_class != class_name and other_class not in {'this', 'std', 'cout', 'cin'}:
                self.usages.append({
                    'from': class_name,
                    'to': other_class,
                    'type': 'uses',
                    'source': 'heuristic'
                })
    
    def _extract_class_content(self, source: str, start_pos: int) -> str:
        """
        Extract class/struct body by matching braces.
        
        Args:
            source: Source code
            start_pos: Position to start from
            
        Returns:
            Class body text
        """
        # Find opening brace
        brace_start = source.find('{', start_pos)
        if brace_start == -1:
            return ""
        
        # Match braces
        brace_count = 1
        pos = brace_start + 1
        
        while pos < len(source) and brace_count > 0:
            if source[pos] == '{':
                brace_count += 1
            elif source[pos] == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count == 0:
            return source[brace_start:pos]
        
        return ""
    
    def detect_relationships(self, all_classes: List[Dict]) -> List[Dict]:
        """
        Detect relationships between classes.
        
        Args:
            all_classes: List of all analyzed classes
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        known_classes = {cls['class'] for cls in all_classes}
        
        # Add inheritance relationships
        relationships.extend(self.relationships)
        
        # Add validated composition relationships
        for comp in self.compositions:
            if comp['to'] in known_classes and comp['to'] != comp['from']:
                relationships.append(comp)
        
        # Add usage relationships (deduplicated)
        seen_usages = set()
        for usage in self.usages:
            if usage['to'] in known_classes and usage['to'] != usage['from']:
                key = (usage['from'], usage['to'], usage['type'])
                if key not in seen_usages:
                    seen_usages.add(key)
                    relationships.append(usage)
        
        # Add dependencies from includes
        for inc in self.includes:
            if inc in known_classes:
                relationships.append({
                    'from': inc,
                    'to': inc,
                    'type': 'dependency',
                    'source': 'heuristic'
                })
        
        return relationships
    
    def extract_endpoints(self, file_path: str) -> List[Dict]:
        """
        C/C++ typically don't have web endpoints.
        Returns empty list.
        """
        return []
