"""
C# Analyzer Module
Analyzes C# source code using regex patterns
"""

import re
import logging
from typing import Dict, List, Set
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class CSharpAnalyzer(BaseAnalyzer):
    """
    Analyzer for C# source code.
    Uses regex-based parsing for C# syntax.
    """
    
    def __init__(self):
        super().__init__()
        self.imports = set()
        self.compositions = []
        self.usages = []
        self.namespaces = set()
    
    def can_analyze(self, file_path: str) -> bool:
        """Check if file is a C# file"""
        return file_path.endswith('.cs')
    
    def analyze_file(self, file_path: str, package_path: str = "") -> List[Dict]:
        """
        Analyze a C# file and extract classes, interfaces, fields, methods.
        
        Args:
            file_path: Path to the C# file
            package_path: C# namespace path
            
        Returns:
            List of class/interface dictionaries
        """
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            # Extract namespace
            namespace = self._extract_namespace(source)
            if namespace:
                self.namespaces.add(namespace)
            
            # Extract using statements
            self._extract_imports(source)
            
            # Analyze classes
            classes.extend(self._analyze_classes(source, namespace or package_path))
            
            # Analyze interfaces
            classes.extend(self._analyze_interfaces(source, namespace or package_path))
            
            self.log_info(f"Analyzed {file_path}: found {len(classes)} classes/interfaces")
            
        except Exception as e:
            self.log_error(f"Error analyzing {file_path}: {e}")
        
        return classes
    
    def _extract_namespace(self, source: str) -> str:
        """Extract namespace from C# source"""
        match = re.search(r'\bnamespace\s+([A-Za-z_][A-Za-z0-9_.]*)', source)
        return match.group(1) if match else None
    
    def _extract_imports(self, source: str):
        """Extract using statements"""
        using_pattern = r'\busing\s+([A-Za-z_][A-Za-z0-9_.]*)\s*;'
        for match in re.finditer(using_pattern, source):
            self.imports.add(match.group(1).split('.')[0])
    
    def _analyze_classes(self, source: str, namespace: str) -> List[Dict]:
        """Extract and analyze all classes in the source"""
        classes = []
        
        # Class pattern: [modifiers] class ClassName [: BaseClass, IInterface1, IInterface2] {
        class_pattern = r'\b(?:public|private|protected|internal|abstract|static|sealed)?\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([^{]+))?\s*{'
        
        for match in re.finditer(class_pattern, source):
            class_name = match.group(1)
            self.add_class_name(class_name)
            
            # Extract bases and interfaces
            bases = []
            if match.group(2):
                bases = self._extract_bases(match.group(2), class_name)
            
            # Extract class body
            class_content = self._extract_class_content(source, match.start())
            
            # Extract fields
            fields = self._extract_fields(class_content, class_name)
            
            # Extract methods
            methods = self._extract_methods(class_content)
            
            # Heuristic analysis for relationships
            self._heuristic_analysis(class_content, class_name, fields)
            
            # Determine stereotype
            is_abstract = 'abstract' in match.group(0)
            
            class_dict = self.create_class_dict(
                class_name=class_name,
                fields=sorted(list(fields)),
                methods=sorted(list(methods)),
                stereotype='abstract' if is_abstract else 'class',
                abstract=is_abstract,
                package=namespace
            )
            
            classes.append(class_dict)
        
        return classes
    
    def _analyze_interfaces(self, source: str, namespace: str) -> List[Dict]:
        """Extract and analyze all interfaces in the source"""
        interfaces = []
        
        # Interface pattern: [modifiers] interface IName [: IBase1, IBase2] {
        interface_pattern = r'\b(?:public|private|protected|internal)?\s*interface\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([^{]+))?\s*{'
        
        for match in re.finditer(interface_pattern, source):
            interface_name = match.group(1)
            self.add_class_name(interface_name)
            
            # Extract base interfaces
            if match.group(2):
                base_interfaces = [b.strip() for b in match.group(2).split(',')]
                for base in base_interfaces:
                    base_clean = base.split('.')[-1].strip()
                    if base_clean:
                        self.add_relationship(base_clean, interface_name, 'extends')
            
            # Extract interface body
            interface_content = self._extract_class_content(source, match.start())
            
            # Extract methods
            methods = self._extract_methods(interface_content)
            
            interface_dict = self.create_class_dict(
                class_name=interface_name,
                fields=[],
                methods=sorted(list(methods)),
                stereotype='interface',
                abstract=True,
                package=namespace
            )
            
            interfaces.append(interface_dict)
        
        return interfaces
    
    def _extract_bases(self, bases_str: str, class_name: str) -> List[str]:
        """
        Extract base classes and interfaces from inheritance declaration.
        
        Args:
            bases_str: Inheritance string (e.g., "BaseClass, IInterface1, IInterface2")
            class_name: Name of the current class
            
        Returns:
            List of base class/interface names
        """
        bases = []
        
        for part in bases_str.split(','):
            clean_part = part.strip()
            # Remove generic parameters
            base_name = re.sub(r'<[^>]*>', '', clean_part).strip()
            base_name = base_name.split('.')[-1]
            
            if base_name:
                bases.append(base_name)
                
                # Interfaces typically start with 'I' in C#
                if base_name.startswith('I') and base_name[1].isupper():
                    self.add_relationship(base_name, class_name, 'implements')
                else:
                    self.add_relationship(base_name, class_name, 'extends')
        
        return bases
    
    def _extract_fields(self, class_content: str, class_name: str) -> Set[str]:
        """
        Extract fields from class body.
        
        Args:
            class_content: Class body text
            class_name: Name of the class
            
        Returns:
            Set of field strings
        """
        fields = set()
        
        # Field pattern: [modifiers] Type fieldName [= value];
        field_pattern = r'\b(?:public|private|protected|internal|static|readonly)\s+([A-Za-z_][A-Za-z0-9_<>\[\],\s]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*[^;]+)?\s*;'
        
        for match in re.finditer(field_pattern, class_content):
            field_type = match.group(1).strip()
            field_name = match.group(2)
            fields.add(f"{field_name}: {field_type}")
            
            # Track composition candidate
            clean_type = re.sub(r'<[^>]*>', '', field_type).strip()
            clean_type = clean_type.split('.')[-1]
            if clean_type and clean_type != class_name:
                    self.compositions.append({
                        'from': class_name,
                        'to': clean_type,
                        'type': 'composition',
                        'source': 'heuristic'
                    })
        
        return fields
    
    def _extract_methods(self, class_content: str) -> Set[str]:
        """
        Extract methods from class body.
        
        Args:
            class_content: Class body text
            
        Returns:
            Set of method names
        """
        methods = set()
        
        # Method pattern: [modifiers] ReturnType MethodName(
        method_pattern = r'\b(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*[A-Za-z_][A-Za-z0-9_<>\[\],\s]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
        
        # C# keywords to filter out
        keywords = {'if', 'for', 'while', 'switch', 'try', 'catch', 'foreach', 'using', 'lock'}
        
        for match in re.finditer(method_pattern, class_content):
            method_name = match.group(1)
            if method_name not in keywords:
                methods.add(method_name)
        
        return methods
    
    def _heuristic_analysis(self, class_content: str, class_name: str, fields: Set):
        """
        Perform heuristic analysis to detect additional relationships.
        
        Args:
            class_content: Class body text
            class_name: Name of the class
            fields: Set to add discovered fields to
        """
        # this.field = new Type()
        for match in re.finditer(
            r'\bthis\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_.]*)\s*\(',
            class_content
        ):
            field_name, field_type = match.group(1), match.group(2)
            fields.add(f"{field_name}: {field_type}")
            
            type_clean = re.sub(r'<[^>]*>', '', field_type).split('.')[-1]
            if type_clean and type_clean != class_name:
                    self.compositions.append({
                        'from': class_name,
                        'to': type_clean,
                        'type': 'composition',
                        'source': 'heuristic'
                    })
        
        # this.field = expr; (capture field name if not present)
        for match in re.finditer(r'\bthis\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*[^;]+;', class_content):
            field_name = match.group(1)
            if not any(str(f).startswith(field_name + ":") or str(f) == field_name for f in fields):
                fields.add(field_name)
        
        # new Type() anywhere in class
        for match in re.finditer(r'\bnew\s+([A-Za-z_][A-Za-z0-9_.]*)\s*\(', class_content):
            type_name = match.group(1)
            type_clean = re.sub(r'<[^>]*>', '', type_name).split('.')[-1]
            if type_clean and type_clean != class_name:
                self.usages.append({
                    'from': class_name,
                    'to': type_clean,
                    'type': 'uses',
                    'source': 'heuristic'
                })
        
        # Static calls: Type.Method(
        for match in re.finditer(
            r'\b([A-Za-z_][A-Za-z0-9_.]*)\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\(',
            class_content
        ):
            type_name = match.group(1)
            type_clean = type_name.split('.')[-1]
            if type_clean and type_clean != class_name and type_clean != 'this':
                self.usages.append({
                    'from': class_name,
                    'to': type_clean,
                    'type': 'uses',
                    'source': 'heuristic'
                })
        
        # Local variable declarations: Type var = ...; or Type var;
        for match in re.finditer(
            r'\b([A-Za-z_][A-Za-z0-9_.<>\[\]]*)\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:[=;])',
            class_content
        ):
            type_name = match.group(1)
            type_clean = re.sub(r'<[^>]*>', '', type_name).split('.')[-1]
            if type_clean and type_clean != class_name:
                self.usages.append({
                    'from': class_name,
                    'to': type_clean,
                    'type': 'uses',
                    'source': 'heuristic'
                })
    
    def _extract_class_content(self, source: str, start_pos: int) -> str:
        """
        Extract class/interface body by matching braces.
        
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
        
        # Add inheritance/implements relationships
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
        
        # Add dependencies from imports
        for imp in self.imports:
            if imp in known_classes:
                relationships.append({
                    'from': imp,
                    'to': imp,
                    'type': 'dependency',
                    'source': 'heuristic'
                })
        
        return relationships
    
    def extract_endpoints(self, file_path: str) -> List[Dict]:
        """
        Extract ASP.NET endpoints from C# source code.
        
        Args:
            file_path: Path to the C# file
            
        Returns:
            List of endpoint dictionaries
        """
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            # ASP.NET Core: [HttpGet("route")], [HttpPost("route")], etc.
            aspnet_patterns = [
                (r'\[HttpGet\(\s*[\'\"]([^\'\"]+)[\'\"]', 'GET'),
                (r'\[HttpPost\(\s*[\'\"]([^\'\"]+)[\'\"]', 'POST'),
                (r'\[HttpPut\(\s*[\'\"]([^\'\"]+)[\'\"]', 'PUT'),
                (r'\[HttpDelete\(\s*[\'\"]([^\'\"]+)[\'\"]', 'DELETE'),
                (r'\[HttpPatch\(\s*[\'\"]([^\'\"]+)[\'\"]', 'PATCH'),
                (r'\[Route\(\s*[\'\"]([^\'\"]+)[\'\"]', 'GET'),
            ]
            
            for pattern, method in aspnet_patterns:
                for match in re.finditer(pattern, source):
                    path = match.group(1)
                    endpoints.append({
                        'path': path,
                        'methods': [method],
                        'framework': 'aspnet'
                    })
        
        except Exception as e:
            self.log_error(f"Error extracting endpoints from {file_path}: {e}")
        
        return endpoints
