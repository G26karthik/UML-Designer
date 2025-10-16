"""
Python Analyzer Module
Analyzes Python source code using AST parsing
"""

import ast
import re
import logging
from typing import Dict, List, Set
from .base_analyzer import BaseAnalyzer
from constants import LANGUAGES, EXTENSION_TO_LANGUAGE

logger = logging.getLogger(__name__)


class PythonAnalyzer(BaseAnalyzer):
    """
    Analyzer for Python source code.
    Uses Python's ast module for parsing and analysis.
    """
    
    def __init__(self):
        super().__init__()
        self.imports = set()
        self.compositions = []
        self.usages = []
    
    def can_analyze(self, file_path: str) -> bool:
        """Check if file is a Python file"""
        return file_path.endswith('.py')
    
    def analyze_file(self, file_path: str, package_path: str = "") -> List[Dict]:
        """
        Analyze a Python file and extract classes, fields, methods.
        
        Args:
            file_path: Path to the Python file
            package_path: Python package/module path
            
        Returns:
            List of class dictionaries
        """
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Extract module-level imports
            self._extract_imports(tree)
            
            # Analyze each class in the file
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_dict = self._analyze_class(node, package_path)
                    if class_dict:
                        classes.append(class_dict)
                        self.add_class_name(class_dict['class'])
            
            self.log_info(f"Analyzed {file_path}: found {len(classes)} classes")
            
        except SyntaxError as e:
            self.log_warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            self.log_error(f"Error analyzing {file_path}: {e}")
        
        return classes
    
    def _extract_imports(self, tree: ast.AST):
        """Extract module-level imports"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.imports.add(node.module.split('.')[0])
    
    def _analyze_class(self, node: ast.ClassDef, package_path: str) -> Dict:
        """
        Analyze a single class node.
        
        Args:
            node: AST ClassDef node
            package_path: Package path for the class
            
        Returns:
            Class dictionary
        """
        class_name = node.name
        
        # Extract bases (inheritance)
        bases = self._extract_bases(node, class_name)
        
        # Extract fields and methods
        fields, methods = self._extract_members(node, class_name)
        
        # Determine stereotype
        stereotype = self._determine_stereotype(node)
        
        return self.create_class_dict(
            class_name=class_name,
            fields=sorted(list(fields)),
            methods=sorted(list(methods)),
            stereotype=stereotype,
            abstract=(stereotype == 'abstract'),
            package=package_path or 'main'
        )
    
    def _extract_bases(self, node: ast.ClassDef, class_name: str) -> List[str]:
        """
        Extract base classes and record inheritance relationships.
        
        Args:
            node: ClassDef node
            class_name: Name of the current class
            
        Returns:
            List of base class names
        """
        bases = []
        
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                bases.append(base_name)
                self.add_relationship(base_name, class_name, 'extends')
            elif isinstance(base, ast.Attribute):
                if isinstance(base.value, ast.Name):
                    base_name = f"{base.value.id}.{base.attr}"
                else:
                    base_name = base.attr
                bases.append(base_name)
                self.add_relationship(base_name, class_name, 'extends')
        
        return bases
    
    def _extract_members(self, node: ast.ClassDef, class_name: str) -> tuple:
        """
        Extract fields and methods from a class.
        
        Args:
            node: ClassDef node
            class_name: Name of the class
            
        Returns:
            Tuple of (fields_set, methods_set)
        """
        fields = set()
        methods = set()
        compositions = set()
        
        for item in node.body:
            # Class-level annotated attributes
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                type_hint = self._get_type_annotation(item.annotation)
                fields.add(f"{item.target.id}: {type_hint}")
            
            # Class-level assignments
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        fields.add(target.id)
            
            # Methods
            elif isinstance(item, ast.FunctionDef):
                methods.add(item.name)
                
                # Analyze method body for instance attributes and relationships
                self._analyze_method_body(item, class_name, fields, compositions)
        
        # Record composition relationships
        for comp in compositions:
            if comp and comp != class_name:
                    self.compositions.append({
                        'from': class_name,
                        'to': comp,
                        'type': 'composition',
                        'source': 'heuristic'
                    })
        
        return fields, methods
    
    def _analyze_method_body(self, method: ast.FunctionDef, class_name: str, 
                            fields: Set, compositions: Set):
        """
        Analyze method body for instance attributes and relationships.
        
        Args:
            method: FunctionDef node
            class_name: Name of the containing class
            fields: Set to add discovered fields to
            compositions: Set to add composition relationships to
        """
        for subnode in ast.walk(method):
            # self.<attr>: Type annotations
            if isinstance(subnode, ast.AnnAssign):
                if isinstance(subnode.target, ast.Attribute):
                    if isinstance(subnode.target.value, ast.Name) and \
                       subnode.target.value.id == 'self':
                        type_hint = self._get_type_annotation(subnode.annotation)
                        fields.add(f"{subnode.target.attr}: {type_hint}")
            
            # self.<attr> = value assignments
            if isinstance(subnode, ast.Assign):
                for tgt in subnode.targets:
                    if isinstance(tgt, ast.Attribute):
                        if isinstance(tgt.value, ast.Name) and tgt.value.id == 'self':
                            fields.add(tgt.attr)
                            
                            # Detect composition when assigning instance to self.attr
                            if isinstance(subnode.value, ast.Call):
                                callee = subnode.value.func
                                if isinstance(callee, ast.Name):
                                    callee_name = callee.id
                                    if self.is_class_known(callee_name) and \
                                       callee_name != class_name:
                                        compositions.add(callee_name)
            
            # Direct instantiation (composition)
            if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
                if self.is_class_known(subnode.func.id) and \
                   subnode.func.id != class_name:
                    compositions.add(subnode.func.id)
            
            # Usage of other known classes
            if isinstance(subnode, ast.Name):
                if self.is_class_known(subnode.id) and subnode.id != class_name:
                        self.usages.append({
                            'from': class_name,
                            'to': subnode.id,
                            'type': 'uses',
                            'source': 'heuristic'
                        })
    
    def _get_type_annotation(self, annotation: ast.AST) -> str:
        """
        Recursively extract type annotation from AST node.
        
        Args:
            annotation: AST node representing type annotation
            
        Returns:
            Type annotation as string
        """
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            if isinstance(annotation.value, ast.Name):
                return f"{annotation.value.id}.{annotation.attr}"
            return annotation.attr
        elif isinstance(annotation, ast.Subscript):
            return self._get_type_annotation(annotation.value)
        else:
            return "Any"
    
    def _determine_stereotype(self, node: ast.ClassDef) -> str:
        """
        Determine the stereotype of a class.
        
        Args:
            node: ClassDef node
            
        Returns:
            Stereotype string ('class', 'abstract', 'interface')
        """
        # Check for ABC (Abstract Base Class)
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ('ABC', 'ABCMeta'):
                return 'abstract'
        
        # Check for @abstractmethod decorators
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in getattr(item, 'decorator_list', []):
                    if isinstance(decorator, ast.Name) and \
                       decorator.id == 'abstractmethod':
                        return 'abstract'
        
        return 'class'
    
    def detect_relationships(self, all_classes: List[Dict]) -> List[Dict]:
        """
        Detect relationships between classes.
        
        Args:
            all_classes: List of all analyzed classes
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        # Add inheritance relationships (already captured)
        relationships.extend(self.relationships)
        
        # Add composition relationships
        relationships.extend(self.compositions)
        
        # Add usage relationships (deduplicated)
        seen_usages = set()
        for usage in self.usages:
            key = (usage['from'], usage['to'], usage['type'])
            if key not in seen_usages:
                seen_usages.add(key)
                relationships.append(usage)
        
        # Add dependencies from imports
        for imp in self.imports:
            if any(cls['class'] == imp for cls in all_classes):
                relationships.append({
                    'from': imp,
                    'to': imp,
                    'type': 'dependency',
                    'source': 'heuristic'
                })
        
        return relationships
    
    def extract_endpoints(self, file_path: str) -> List[Dict]:
        """
        Extract Flask/Django endpoints from Python source code.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of endpoint dictionaries
        """
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            # Flask routes: @app.route('/path') or @bp.route('/path')
            flask_pattern = r'@\s*(?:app|bp)\.route\(\s*[\'\"]([^\'\"]+)[\'\"](?:,\s*methods\s*=\s*\[([^\]]+)\])?'
            for match in re.finditer(flask_pattern, source):
                path = match.group(1)
                methods = match.group(2) if match.group(2) else 'GET'
                endpoints.append({
                    'path': path,
                    'methods': [m.strip().strip('\'"') for m in methods.split(',')],
                    'framework': 'flask'
                })
            
            # Django paths: path('route', view)
            django_pattern = r'path\(\s*[\'\"]([^\'\"]+)[\'\"]'
            for match in re.finditer(django_pattern, source):
                path = match.group(1)
                endpoints.append({
                    'path': path,
                    'methods': ['GET', 'POST'],
                    'framework': 'django'
                })
            
            # FastAPI: @app.get('/path'), @app.post('/path'), etc.
            fastapi_pattern = r'@app\.(get|post|put|delete|patch)\(\s*[\'\"]([^\'\"]+)[\'\"]'
            for match in re.finditer(fastapi_pattern, source):
                method = match.group(1).upper()
                path = match.group(2)
                endpoints.append({
                    'path': path,
                    'methods': [method],
                    'framework': 'fastapi'
                })
        
        except Exception as e:
            self.log_error(f"Error extracting endpoints from {file_path}: {e}")
        
        return endpoints
