"""
Java Analyzer Module
Analyzes Java source code using javalang library
"""

import re
import logging
import javalang  # type: ignore
from typing import Dict, List, Set
from .base_analyzer import BaseAnalyzer
from constants import LANGUAGES

logger = logging.getLogger(__name__)


class JavaAnalyzer(BaseAnalyzer):
    """
    Analyzer for Java source code.
    Uses javalang library for parsing and analysis.
    """
    
    def __init__(self):
        super().__init__()
        self.imports = set()
        self.compositions = []
        self.usages = []
        self.java_packages = set()
        self.usecases = []
        self.state_transitions = []
        self.sequence_calls = []
    
    def can_analyze(self, file_path: str) -> bool:
        """Check if file is a Java file"""
        return file_path.endswith('.java')
    
    def analyze_file(self, file_path: str, package_path: str = "") -> List[Dict]:
        """
        Analyze a Java file and extract classes, interfaces, fields, methods.
        
        Args:
            file_path: Path to the Java file
            package_path: Java package path
            
        Returns:
            List of class/interface dictionaries
        """
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = javalang.parse.parse(source)
            
            # Extract package declaration
            package = self._extract_package(tree)
            if package:
                self.java_packages.add(package)
            
            # Extract imports
            self._extract_imports(tree)
            
            # Analyze each class/interface in the file
            for path_nodes, cls in tree.filter(javalang.tree.ClassDeclaration):
                class_dict = self._analyze_class(cls, tree, source, package or package_path)
                if class_dict:
                    classes.append(class_dict)
                    self.add_class_name(class_dict['class'])
            
            # Analyze interfaces
            for path_nodes, intf in tree.filter(javalang.tree.InterfaceDeclaration):
                interface_dict = self._analyze_interface(intf, tree, package or package_path)
                if interface_dict:
                    classes.append(interface_dict)
                    self.add_class_name(interface_dict['class'])
            
            self.log_info(f"Analyzed {file_path}: found {len(classes)} classes/interfaces")
            
        except javalang.parser.JavaSyntaxError as e:
            self.log_warning(f"Java syntax error in {file_path}: {e}")
        except Exception as e:
            self.log_error(f"Error analyzing {file_path}: {e}")
        
        return classes
    
    def _extract_package(self, tree: javalang.tree.CompilationUnit) -> str:
        """Extract package declaration from parse tree"""
        for path_node, pkg in tree.filter(javalang.tree.PackageDeclaration):
            return pkg.name
        return None
    
    def _extract_imports(self, tree: javalang.tree.CompilationUnit):
        """Extract imports from parse tree"""
        for path_node, imp in tree.filter(javalang.tree.Import):
            if hasattr(imp, 'path'):
                # Store first part of package path
                self.imports.add(imp.path.split('.')[0])
    
    def _analyze_class(self, cls: javalang.tree.ClassDeclaration, tree: javalang.tree.CompilationUnit,
                      source: str, package: str) -> Dict:
        """
        Analyze a single class.
        
        Args:
            cls: ClassDeclaration node
            tree: Full compilation unit tree
            source: Source code string
            package: Package name
            
        Returns:
            Class dictionary
        """
        class_name = cls.name
        
        # Extract inheritance
        self._extract_inheritance(cls, class_name)
        
        # Extract implements
        self._extract_implements(cls, class_name)
        
        # Extract fields and compositions
        fields, compositions, state_fields = self._extract_fields(cls, tree, class_name)
        
        # Extract methods and use cases
        methods, usecases = self._extract_methods(cls, tree, class_name, state_fields)
        
        # Heuristic analysis for additional relationships
        self._heuristic_analysis(source, class_name, fields, compositions)
        
        # Determine modifiers and stereotype
        modifiers = set(getattr(cls, 'modifiers', []))
        is_abstract = 'abstract' in modifiers
        
        return self.create_class_dict(
            class_name=class_name,
            fields=sorted(list(fields)),
            methods=sorted(list(methods)),
            stereotype='abstract' if is_abstract else 'class',
            abstract=is_abstract,
            package=package
        )
    
    def _analyze_interface(self, intf: javalang.tree.InterfaceDeclaration, 
                          tree: javalang.tree.CompilationUnit, package: str) -> Dict:
        """
        Analyze a single interface.
        
        Args:
            intf: InterfaceDeclaration node
            tree: Full compilation unit tree
            package: Package name
            
        Returns:
            Interface dictionary
        """
        interface_name = intf.name
        
        # Extract extends (interfaces can extend other interfaces)
        if intf.extends:
            for ext in intf.extends:
                self.add_relationship(ext.name, interface_name, 'extends')
        
        # Extract methods (all are abstract in interfaces)
        methods = set()
        for method_path, method in tree.filter(javalang.tree.MethodDeclaration):
            enclosing_interface = None
            for path_node in reversed(method_path):
                if isinstance(path_node, javalang.tree.InterfaceDeclaration):
                    enclosing_interface = path_node.name
                    break
            
            if enclosing_interface == interface_name:
                methods.add(method.name)
        
        return self.create_class_dict(
            class_name=interface_name,
            fields=[],
            methods=sorted(list(methods)),
            stereotype='interface',
            abstract=True,
            package=package
        )
    
    def _extract_inheritance(self, cls: javalang.tree.ClassDeclaration, class_name: str):
        """Extract class inheritance (extends)"""
        if cls.extends:
            base_name = cls.extends.name
            self.add_relationship(base_name, class_name, 'extends')
    
    def _extract_implements(self, cls: javalang.tree.ClassDeclaration, class_name: str):
        """Extract interface implementations"""
        if cls.implements:
            for impl in cls.implements:
                impl_name = impl.name
                self.add_relationship(impl_name, class_name, 'implements')
    
    def _extract_fields(self, cls: javalang.tree.ClassDeclaration, 
                       tree: javalang.tree.CompilationUnit, class_name: str) -> tuple:
        """
        Extract fields from a class.
        
        Args:
            cls: ClassDeclaration node
            tree: Full compilation unit tree
            class_name: Name of the class
            
        Returns:
            Tuple of (fields_set, compositions_set, state_fields_set)
        """
        fields = set()
        compositions = set()
        state_fields = set()
        
        for field_path, field in tree.filter(javalang.tree.FieldDeclaration):
            # Find enclosing class
            enclosing_class = None
            for path_node in reversed(field_path):
                if isinstance(path_node, javalang.tree.ClassDeclaration):
                    enclosing_class = path_node.name
                    break
            
            if enclosing_class == class_name:
                for declarator in field.declarators:
                    field_name = declarator.name
                    field_type = field.type.name if hasattr(field.type, 'name') else str(field.type)
                    
                    fields.add(f"{field_name}: {field_type}")
                    
                    # Track state fields for state diagrams
                    if any(s in field_name.lower() for s in ['state', 'status', 'mode']):
                        state_fields.add(field_name)
                    
                    # Potential composition (will be validated later)
                    compositions.add(field_type)
        
        return fields, compositions, state_fields
    
    def _extract_methods(self, cls: javalang.tree.ClassDeclaration,
                        tree: javalang.tree.CompilationUnit, class_name: str,
                        state_fields: Set) -> tuple:
        """
        Extract methods from a class.
        
        Args:
            cls: ClassDeclaration node
            tree: Full compilation unit tree
            class_name: Name of the class
            state_fields: Set of state field names
            
        Returns:
            Tuple of (methods_set, usecases_list)
        """
        methods = set()
        usecases = []
        
        for method_path, method in tree.filter(javalang.tree.MethodDeclaration):
            # Find enclosing class
            enclosing_class = None
            for path_node in reversed(method_path):
                if isinstance(path_node, javalang.tree.ClassDeclaration):
                    enclosing_class = path_node.name
                    break
            
            if enclosing_class == class_name:
                methods.add(method.name)
                
                # Extract use cases from public methods in controllers
                if 'public' in method.modifiers and self._is_controller_class(class_name):
                    usecases.append({
                        'actor': 'User',
                        'action': method.name,
                        'controller': class_name
                    })
                    self.usecases.append({
                        'actor': 'User',
                        'action': method.name,
                        'controller': class_name
                    })
                
                # Extract state transitions
                if method.body:
                    for stmt in method.body:
                        if hasattr(stmt, 'expression') and hasattr(stmt.expression, 'member'):
                            member = stmt.expression.member
                            if member in state_fields:
                                self.state_transitions.append({
                                    'class': class_name,
                                    'state_field': member,
                                    'action': method.name
                                })
                
                # Extract method calls for sequence diagrams
                if method.body:
                    for stmt in method.body:
                        if hasattr(stmt, 'expression') and hasattr(stmt.expression, 'qualifier'):
                            callee = stmt.expression.qualifier
                            self.sequence_calls.append({
                                'caller': class_name,
                                'callee': callee,
                                'method': method.name
                            })
                
                # Extract parameter types for usage relationships
                for param in method.parameters or []:
                    param_type = getattr(param, 'type', None)
                    if param_type and hasattr(param_type, 'name'):
                        param_type = param_type.name
                    if param_type:
                        self.usages.append({
                            'from': class_name,
                            'to': param_type,
                            'type': 'uses'
                        })
        
        return methods, usecases
    
    def _is_controller_class(self, class_name: str) -> bool:
        """Check if class name suggests it's a controller/main class"""
        controller_patterns = ['Controller', 'Main', 'Game', 'Maze', 'Handler', 'Manager']
        return any(pattern in class_name for pattern in controller_patterns)
    
    def _heuristic_analysis(self, source: str, class_name: str, 
                           fields: Set, compositions: Set):
        """
        Perform heuristic analysis on source code to detect additional relationships.
        
        Args:
            source: Java source code
            class_name: Name of the class
            fields: Set to add discovered fields to
            compositions: Set to add composition relationships to
        """
        try:
            class_text = self._extract_class_content(source, class_name)
            if not class_text:
                return
            
            # Detect: this.field = new OtherClass()
            for match in re.finditer(
                r'\bthis\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(',
                class_text
            ):
                field_name, field_type = match.group(1), match.group(2)
                fields.add(f"{field_name}: {field_type}")
                if field_type != class_name:
                    compositions.add(field_type)
                    self.compositions.append({
                        'from': class_name,
                        'to': field_type,
                        'type': 'composition',
                        'source': 'heuristic'
                    })
            
            # Detect: new OtherClass() (local instantiation)
            for match in re.finditer(r'\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', class_text):
                other_class = match.group(1)
                if other_class != class_name:
                    self.usages.append({
                        'from': class_name,
                        'to': other_class,
                        'type': 'uses',
                        'source': 'heuristic'
                    })
            
            # Detect: OtherClass.method() (static calls)
            for match in re.finditer(
                r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\(',
                class_text
            ):
                other_class = match.group(1)
                if other_class != class_name and other_class != 'this' and other_class != 'super':
                    self.usages.append({
                        'from': class_name,
                        'to': other_class,
                        'type': 'uses',
                        'source': 'heuristic'
                    })
            
            # Detect: OtherClass var = ...; or OtherClass var;
            for match in re.finditer(
                r'\b([A-Za-z_][A-Za-z0-9_]*)\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:[=;])',
                class_text
            ):
                type_name = match.group(1)
                if type_name != class_name and not type_name in ['int', 'long', 'float', 'double', 
                                                                   'boolean', 'char', 'byte', 'short',
                                                                   'String', 'void']:
                    self.usages.append({
                        'from': class_name,
                        'to': type_name,
                        'type': 'uses',
                        'source': 'heuristic'
                    })
        
        except Exception as e:
            self.log_warning(f"Heuristic analysis failed for {class_name}: {e}")
    
    def _extract_class_content(self, source: str, class_name: str) -> str:
        """
        Extract the textual body of a Java class by matching braces.
        
        Args:
            source: Java source code
            class_name: Name of the class to extract
            
        Returns:
            Class body text
        """
        # Find class declaration
        class_pattern = rf'\bclass\s+{re.escape(class_name)}\b'
        match = re.search(class_pattern, source)
        
        if not match:
            return None
        
        start_pos = match.end()
        
        # Find opening brace
        brace_start = source.find('{', start_pos)
        if brace_start == -1:
            return None
        
        # Match braces to find class body
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
        
        return None
    
    def detect_relationships(self, all_classes: List[Dict]) -> List[Dict]:
        """
        Detect relationships between classes.
        
        Args:
            all_classes: List of all analyzed classes
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        # Add inheritance/implements relationships
        relationships.extend(self.relationships)
        
        # Add validated composition relationships
        known_classes = {cls['class'] for cls in all_classes}
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
        Extract Spring Boot endpoints from Java source code.
        
        Args:
            file_path: Path to the Java file
            
        Returns:
            List of endpoint dictionaries
        """
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            # Spring Boot: @RequestMapping, @GetMapping, @PostMapping, etc.
            spring_patterns = [
                (r'@GetMapping\(\s*[\'\"]([^\'\"]+)[\'\"]', 'GET'),
                (r'@PostMapping\(\s*[\'\"]([^\'\"]+)[\'\"]', 'POST'),
                (r'@PutMapping\(\s*[\'\"]([^\'\"]+)[\'\"]', 'PUT'),
                (r'@DeleteMapping\(\s*[\'\"]([^\'\"]+)[\'\"]', 'DELETE'),
                (r'@PatchMapping\(\s*[\'\"]([^\'\"]+)[\'\"]', 'PATCH'),
                (r'@RequestMapping\(\s*[\'\"]([^\'\"]+)[\'\"]', 'GET'),
            ]
            
            for pattern, method in spring_patterns:
                for match in re.finditer(pattern, source):
                    path = match.group(1)
                    endpoints.append({
                        'path': path,
                        'methods': [method],
                        'framework': 'spring'
                    })
        
        except Exception as e:
            self.log_error(f"Error extracting endpoints from {file_path}: {e}")
        
        return endpoints
