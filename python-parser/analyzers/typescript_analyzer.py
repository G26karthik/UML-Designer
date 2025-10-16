"""
TypeScript/JavaScript Analyzer Module
Analyzes TypeScript and JavaScript source code using regex patterns
"""

import re
import logging
from typing import Dict, List, Set
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class TypeScriptAnalyzer(BaseAnalyzer):
    """
    Analyzer for TypeScript and JavaScript source code.
    Uses regex-based parsing for ES6+ class syntax.
    """
    
    def __init__(self):
        super().__init__()
        self.imports = set()
        self.compositions = []
        self.usages = []
        self.modules = set()
    
    def can_analyze(self, file_path: str) -> bool:
        """Check if file is TypeScript or JavaScript"""
        return file_path.endswith(('.ts', '.tsx', '.js', '.jsx'))
    
    def analyze_file(self, file_path: str, package_path: str = "") -> List[Dict]:
        """
        Analyze a TypeScript/JavaScript file and extract classes, fields, methods.
        
        Args:
            file_path: Path to the TypeScript/JavaScript file
            package_path: Module path
            
        Returns:
            List of class dictionaries
        """
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            # Extract imports
            self._extract_imports(source)

            # Analyze interfaces first so they're registered for relationship validation
            classes.extend(self._analyze_interfaces(source, package_path))

            # Analyze ES6 classes
            classes.extend(self._analyze_classes(source, package_path))
            
            self.log_info(f"Analyzed {file_path}: found {len(classes)} classes")
            
        except Exception as e:
            self.log_error(f"Error analyzing {file_path}: {e}")
        
        return classes
    
    def _extract_imports(self, source: str):
        """Extract require() and import statements"""
        # require('module')
        require_pattern = r'require\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        for match in re.finditer(require_pattern, source):
            module = match.group(1).split('/')[0]
            self.imports.add(module)
            self.modules.add(module)
        
        # import ... from 'module'
        import_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(import_pattern, source):
            module = match.group(1).split('/')[0]
            self.imports.add(module)
            self.modules.add(module)
    
    def _analyze_classes(self, source: str, package_path: str) -> List[Dict]:
        """Extract and analyze all classes in the source"""
        classes = []
        
        # ES6 class pattern: class ClassName [extends BaseClass] {
        class_pattern = (
            r'\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)'
            r'\s*(?:extends\s+([A-Za-z_$][A-Za-z0-9_$.]*))?'
            r'\s*(?:implements\s+([A-Za-z_$][A-Za-z0-9_$,\s.]*))?'
            r'\s*{'
        )
        
        for match in re.finditer(class_pattern, source):
            class_name = match.group(1)
            self.add_class_name(class_name)
            
            # Extract base class
            base_class = match.group(2)
            if base_class:
                base_clean = base_class.split('.')[-1]
                self.add_relationship(base_clean, class_name, 'extends')

            implements_clause = match.group(3)
            if implements_clause:
                for iface in re.split(r'\s*,\s*', implements_clause.strip()):
                    iface_clean = iface.split('.')[-1]
                    if iface_clean:
                        self.add_relationship(iface_clean, class_name, 'implements')
            
            # Extract class body
            class_content = self._extract_class_content(source, match.start())
            
            # Extract fields and methods
            fields, methods = self._extract_members(class_content, class_name)
            
            # Heuristic analysis for relationships
            self._heuristic_analysis(class_content, class_name, fields)
            
            class_dict = self.create_class_dict(
                class_name=class_name,
                fields=sorted(list(fields)),
                methods=sorted(list(methods)),
                stereotype='class',
                abstract=False,
                package=package_path or 'main'
            )
            
            classes.append(class_dict)
        
        return classes

    def _analyze_interfaces(self, source: str, package_path: str) -> List[Dict]:
        """Extract TypeScript interface definitions."""
        interfaces = []

        interface_pattern = (
            r'\binterface\s+([A-Za-z_$][A-Za-z0-9_$]*)'
            r'\s*(?:extends\s+([A-Za-z_$][A-Za-z0-9_$,\s.]*))?'
            r'\s*{'
        )

        for match in re.finditer(interface_pattern, source):
            interface_name = match.group(1)
            self.add_class_name(interface_name)

            extends_clause = match.group(2)
            if extends_clause:
                for base_iface in re.split(r'\s*,\s*', extends_clause.strip()):
                    base_clean = base_iface.split('.')[-1]
                    if base_clean:
                        self.add_relationship(base_clean, interface_name, 'extends')

            interface_content = self._extract_class_content(source, match.start())

            fields = set()
            methods = set()

            # Property signatures: name: Type;
            for prop in re.finditer(
                r'([A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*([A-Za-z_$][A-Za-z0-9_$<>,\s\[\]]*)\s*;',
                interface_content
            ):
                fields.add(f"{prop.group(1)}: {prop.group(2).strip()}")

            # Method signatures: name(params): ReturnType;
            for method in re.finditer(
                r'([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^;{]*\)\s*[:;]',
                interface_content
            ):
                methods.add(method.group(1))

            interfaces.append(self.create_class_dict(
                class_name=interface_name,
                fields=sorted(list(fields)),
                methods=sorted(list(methods)),
                stereotype='interface',
                abstract=False,
                package=package_path or 'main'
            ))

        return interfaces
    
    def _extract_members(self, class_content: str, class_name: str) -> tuple:
        """
        Extract fields and methods from class body.
        
        Args:
            class_content: Class body text
            class_name: Name of the class
            
        Returns:
            Tuple of (fields_set, methods_set)
        """
        fields = set()
        methods = set()
        
        # Extract constructor parameters as fields
        constructor_match = re.search(r'constructor\s*\(([^)]*)\)', class_content)
        if constructor_match:
            params = constructor_match.group(1)
            # TypeScript: param: Type or JavaScript: param
            param_pattern = r'([A-Za-z_$][A-Za-z0-9_$]*)\s*(?::\s*[^,)]+)?'
            param_names = re.findall(param_pattern, params)
            fields.update(param_names)
        
        # Extract methods
        # Method pattern: methodName(...) or async methodName(...)
        method_pattern = r'\b(?:async\s+)?([A-Za-z_$][A-Za-z0-9_$]*)\s*\('
        for match in re.finditer(method_pattern, class_content):
            method_name = match.group(1)
            # Filter out keywords and common JS functions
            if method_name not in {'if', 'for', 'while', 'switch', 'catch', 'function'}:
                methods.add(method_name)
        
        # Remove constructor from methods
        methods.discard('constructor')
        
        # Extract TypeScript property declarations
        # private/public/protected name: Type
        property_pattern = r'\b(?:private|public|protected|readonly)?\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*([A-Za-z_$][A-Za-z0-9_$<>\[\]|]+)'
        for match in re.finditer(property_pattern, class_content):
            prop_name = match.group(1)
            prop_type = match.group(2)
            fields.add(f"{prop_name}: {prop_type}")
        
        return fields, methods
    
    def _heuristic_analysis(self, class_content: str, class_name: str, fields: Set):
        """
        Perform heuristic analysis to detect relationships.
        
        Args:
            class_content: Class body text
            class_name: Name of the class
            fields: Set to add discovered fields to
        """
        # this.field = new OtherClass()
        for match in re.finditer(
            r'\bthis\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*new\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(',
            class_content
        ):
            field_name, field_type = match.group(1), match.group(2)
            fields.add(f"{field_name}: {field_type}")
            if field_type != class_name:
                self.compositions.append({
                    'from': class_name,
                    'to': field_type,
                    'type': 'composition',
                    'source': 'heuristic'
                })
        
        # this.field = expr; (capture field name if not present)
        for match in re.finditer(r'\bthis\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*[^;]+;', class_content):
            field_name = match.group(1)
            if not any(str(f).startswith(field_name + ":") or str(f) == field_name for f in fields):
                fields.add(field_name)
        
        # new OtherClass()
        for match in re.finditer(r'\bnew\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(', class_content):
            other_class = match.group(1)
            if other_class != class_name:
                self.usages.append({
                    'from': class_name,
                    'to': other_class,
                    'type': 'uses',
                    'source': 'heuristic'
                })
        
        # OtherClass.method() (static calls)
        for match in re.finditer(
            r'\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\.\s*[A-Za-z_$][A-Za-z0-9_$]*\s*\(',
            class_content
        ):
            other_class = match.group(1)
            if other_class != class_name and other_class not in {'this', 'super', 'console', 'Math', 'Date', 'JSON'}:
                self.usages.append({
                    'from': class_name,
                    'to': other_class,
                    'type': 'uses',
                    'source': 'heuristic'
                })
    
    def _extract_class_content(self, source: str, start_pos: int) -> str:
        """
        Extract class body by matching braces.
        
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
        Extract Express/NestJS endpoints from TypeScript/JavaScript source code.
        
        Args:
            file_path: Path to the TypeScript/JavaScript file
            
        Returns:
            List of endpoint dictionaries
        """
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            # Express: app.get('/path', ...), router.get('/path', ...)
            express_patterns = [
                (r'(?:app|router)\.get\(\s*[\'\"]([^\'\"]+)[\'\"]', 'GET'),
                (r'(?:app|router)\.post\(\s*[\'\"]([^\'\"]+)[\'\"]', 'POST'),
                (r'(?:app|router)\.put\(\s*[\'\"]([^\'\"]+)[\'\"]', 'PUT'),
                (r'(?:app|router)\.delete\(\s*[\'\"]([^\'\"]+)[\'\"]', 'DELETE'),
                (r'(?:app|router)\.patch\(\s*[\'\"]([^\'\"]+)[\'\"]', 'PATCH'),
            ]
            
            for pattern, method in express_patterns:
                for match in re.finditer(pattern, source):
                    path = match.group(1)
                    endpoints.append({
                        'path': path,
                        'methods': [method],
                        'framework': 'express'
                    })
            
            # NestJS: @Get('path'), @Post('path'), etc.
            nestjs_patterns = [
                (r'@Get\(\s*[\'\"]([^\'\"]+)[\'\"]', 'GET'),
                (r'@Post\(\s*[\'\"]([^\'\"]+)[\'\"]', 'POST'),
                (r'@Put\(\s*[\'\"]([^\'\"]+)[\'\"]', 'PUT'),
                (r'@Delete\(\s*[\'\"]([^\'\"]+)[\'\"]', 'DELETE'),
                (r'@Patch\(\s*[\'\"]([^\'\"]+)[\'\"]', 'PATCH'),
            ]
            
            for pattern, method in nestjs_patterns:
                for match in re.finditer(pattern, source):
                    path = match.group(1)
                    endpoints.append({
                        'path': path,
                        'methods': [method],
                        'framework': 'nestjs'
                    })
        
        except Exception as e:
            self.log_error(f"Error extracting endpoints from {file_path}: {e}")
        
        return endpoints
