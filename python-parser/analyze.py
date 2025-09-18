import os
import re
import ast
import javalang
import logging
import json
import requests
from dotenv import load_dotenv

load_dotenv()


"""
analyze.py
Module for analyzing codebases and generating UML schema in JSON format.
Supports Python, Java, C#, JavaScript, TypeScript, C++, and C.
Detects classes, relations, design patterns, and architectural layers.
"""

# Return stubbed schema when true (for offline testing)
STUB_LLM = os.getenv('STUB_LLM', 'false').lower() in ('1', 'true', 'yes')

# Enhanced prompt to steer the model to return the exact JSON shape we need with better accuracy
PROMPT = '''You are an expert software architect and UML diagram generator. Given a codebase or a natural language prompt describing a system, produce ONLY valid JSON (no markdown fences, no prose) matching this schema:

{
    "python": [{"class": "Name", "fields": ["f1: Type"], "methods": ["m1", "m2"], "stereotype": "class|interface|abstract", "abstract": false, "package": "module.path"}],
    "java": [{"class": "Name", "fields": ["f1: Type"], "methods": ["m1", "m2"], "stereotype": "class|interface|abstract", "abstract": false, "package": "com.example"}],
    "csharp": [{"class": "Name", "fields": ["f1: Type"], "methods": ["m1", "m2"], "stereotype": "class|interface|abstract", "abstract": false, "namespace": "Namespace"}],
    "javascript": [{"class": "Name", "fields": ["f1: Type"], "methods": ["m1", "m2"], "stereotype": "class", "abstract": false}],
    "typescript": [{"class": "Name", "fields": ["f1: Type"], "methods": ["m1", "m2"], "stereotype": "class|interface", "abstract": false}],
    "cpp": [{"class": "Name", "fields": ["f1: Type"], "methods": ["m1", "m2"], "stereotype": "class|struct", "abstract": false}],
    "c": [{"class": "Name", "fields": ["f1: Type"], "methods": ["m1", "m2"], "stereotype": "struct", "abstract": false}],
    "relations": [{"from": "ClassA", "to": "ClassB", "type": "extends|implements|uses|composition|aggregation|dependency|association", "source": "heuristic|ai"}],
    "patterns": [{"type": "singleton|factory|observer|strategy|decorator", "classes": ["Class1", "Class2"]}],
    "layers": [{"name": "presentation|business|data", "classes": ["Class1", "Class2"]}]
}

INSTRUCTIONS:
1. If given a natural language prompt, infer classes, fields, methods, and relationships as if designing the system from scratch. Use best practices for naming and structure.
2. Always include ALL classes described or implied, even if not directly related.
3. Fields should include type information when available (e.g., "name: String", "age: int").
4. Methods should be method names only (no parentheses or parameters).
5. Stereotypes: use "interface" for interfaces, "abstract" for abstract classes, "class" for concrete classes.
6. Relations: use "extends" for inheritance, "implements" for interface implementation, "composition" for strong ownership, "aggregation" for weak ownership, "uses" for method parameters/return types, "dependency" for imports/references, "association" for general links.
7. Add "patterns" array for detected design patterns (e.g., singleton, factory, observer).
8. Add "layers" array for architectural layer detection (presentation=controllers/views, business=services/managers, data=models/repositories).
9. Cross-language relationships should be detected when classes interact across language boundaries.
10. If unsure about a relationship type, use "association" as fallback.
11. Do not include any prose, explanations, or markdown fences—return ONLY valid JSON.
12.Always think step-by-step before answering to ensure completeness and accuracy.
13.Think and act as a humman software architect with years of experience.
14. Understand the full context before Creating UML Diagram and make sure to take a Human's perspective on how he will create this UML Diagram.

EXAMPLES:
Prompt: "A library system with books, members, and loans. Members can borrow books."
Output:
{
    "python": [
        {"class": "Book", "fields": ["title: String", "author: String", "isbn: String"], "methods": ["borrow", "return"], "stereotype": "class", "abstract": false, "package": "library"},
        {"class": "Member", "fields": ["name: String", "memberId: String"], "methods": ["borrowBook", "returnBook"], "stereotype": "class", "abstract": false, "package": "library"},
        {"class": "Loan", "fields": ["book: Book", "member: Member", "dueDate: Date"], "methods": ["renew", "close"], "stereotype": "class", "abstract": false, "package": "library"}
    ],
    "relations": [
        {"from": "Member", "to": "Book", "type": "uses", "source": "ai"},
        {"from": "Loan", "to": "Book", "type": "composition", "source": "ai"},
        {"from": "Loan", "to": "Member", "type": "composition", "source": "ai"}
    ]
}

Prompt: "An e-commerce platform with products, customers, orders, and payment processing."
Output:
{
    "python": [
        {"class": "Product", "fields": ["name: String", "price: Float", "sku: String"], "methods": ["updateStock"], "stereotype": "class", "abstract": false, "package": "shop"},
        {"class": "Customer", "fields": ["name: String", "email: String"], "methods": ["placeOrder"], "stereotype": "class", "abstract": false, "package": "shop"},
        {"class": "Order", "fields": ["customer: Customer", "products: List[Product]", "total: Float"], "methods": ["addProduct", "checkout"], "stereotype": "class", "abstract": false, "package": "shop"},
        {"class": "PaymentProcessor", "fields": ["provider: String"], "methods": ["processPayment"], "stereotype": "class", "abstract": false, "package": "shop"}
    ],
    "relations": [
        {"from": "Order", "to": "Product", "type": "aggregation", "source": "ai"},
        {"from": "Order", "to": "Customer", "type": "association", "source": "ai"},
        {"from": "Order", "to": "PaymentProcessor", "type": "uses", "source": "ai"}
    ]
}
'''


def _norm_type_name(name: str) -> str:

    """
    Normalize type name by removing generics, arrays, and namespace separators.

    Args:
        name (str): Raw type name string.

    Returns:
        str: Normalized type name.
    """
    if not name:
        return name
    # strip generics and arrays
    n = re.sub(r'<[^>]*>', '', str(name))
    n = n.replace('[]', '')
    # namespace separators
    if '::' in n:
        n = n.split('::')[-1]
    if '.' in n:
        n = n.split('.')[-1]
    return n.strip()


def _analyze_python_file(full_path, package_path, result, class_info, all_class_names,
                        inheritance_rels, composition_rels, dependency_rels, usage_rels, py_modules):
    """
    Enhanced Python file analysis using AST.
    Parses Python source code to extract classes, fields, methods, imports, and relationships.
    Updates result dicts for UML schema generation.

    Args:
        full_path (str): Path to the Python file.
        package_path (str): Python package/module path.
        result (dict): Main result dictionary for schema.
        class_info (dict): Class metadata accumulator.
        all_class_names (set): Set of all discovered class names.
        inheritance_rels (list): List to accumulate inheritance relationships.
        composition_rels (list): List to accumulate composition relationships.
        dependency_rels (list): List to accumulate dependency relationships.
        usage_rels (list): List to accumulate usage relationships.
        py_modules (set): Set of imported Python modules.
    """
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        tree = ast.parse(source)

        # Extract module-level imports for dependencies
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        # Analyze classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                all_class_names.add(class_name)

                # Extract bases (inheritance)
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_name = base.id
                        bases.append(base_name)
                        inheritance_rels.append({'from': base_name, 'to': class_name, 'type': 'extends'})
                    elif isinstance(base, ast.Attribute):
                        base_name = f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else base.attr
                        bases.append(base_name)
                        inheritance_rels.append({'from': base_name, 'to': class_name, 'type': 'extends'})

                # Extract fields and methods
                fields = set()
                methods = set()
                compositions = set()

                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        # Class-level annotated attribute
                        type_hint = _get_type_annotation(item.annotation)
                        fields.add(f"{item.target.id}: {type_hint}")
                    elif isinstance(item, ast.Assign):
                        # Class-level assignments
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                fields.add(target.id)
                    elif isinstance(item, ast.FunctionDef):
                        methods.add(item.name)

                        # Analyze method body for instance attributes, compositions, and dependencies
                        for subnode in ast.walk(item):
                            # self.<attr> annotated: capture as field with type when possible
                            if isinstance(subnode, ast.AnnAssign) and isinstance(subnode.target, ast.Attribute):
                                if isinstance(subnode.target.value, ast.Name) and subnode.target.value.id == 'self':
                                    type_hint = _get_type_annotation(subnode.annotation)
                                    fields.add(f"{subnode.target.attr}: {type_hint}")
                            # self.<attr> = ... assignments captured as fields
                            if isinstance(subnode, ast.Assign):
                                for tgt in subnode.targets:
                                    if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == 'self':
                                        # add instance attribute name
                                        fields.add(tgt.attr)
                                        # detect composition when assigning instance of known class to self.attr
                                        if isinstance(subnode.value, ast.Call):
                                            callee = subnode.value.func
                                            callee_name = callee.id if isinstance(callee, ast.Name) else None
                                            if callee_name and callee_name in all_class_names and callee_name != class_name:
                                                compositions.add(callee_name)
                            # Direct instantiation: treat as composition only if known class
                            if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
                                if subnode.func.id in all_class_names and subnode.func.id != class_name:
                                    compositions.add(subnode.func.id)
                            # Usage of other known classes
                            if isinstance(subnode, ast.Name) and subnode.id in all_class_names and subnode.id != class_name:
                                usage_rels.append({'from': class_name, 'to': subnode.id, 'type': 'uses'})

                # Store class info
                stereotype = 'abstract' if any(isinstance(item, ast.FunctionDef) and
                                             getattr(item, 'decorator_list', []) for item in node.body) else 'class'

                class_entry = {
                    'class': class_name,
                    'fields': sorted(list(fields)),
                    'methods': sorted(list(methods)),
                    'stereotype': stereotype,
                    'abstract': stereotype == 'abstract',
                    'package': package_path or 'main'
                }

                result['python'].append(class_entry)
                class_info[class_name] = {
                    'lang': 'python',
                    'fields': fields,
                    'methods': methods,
                    'bases': bases,
                    'stereotype': stereotype,
                    'package': package_path
                }

                # Add compositions
                for comp in compositions:
                    if comp and comp != class_name:
                        composition_rels.append({'from': class_name, 'to': comp, 'type': 'composition'})

                # Add dependencies from imports
                for imp in imports:
                    if imp in all_class_names and imp != class_name:
                        dependency_rels.append({'from': class_name, 'to': imp, 'type': 'dependency'})

        # Extract Flask/Django endpoints
        _extract_python_endpoints(source, result)

    except Exception as e:
        logging.warning(f"Error analyzing Python file {full_path}: {e}")


def _get_type_annotation(annotation):
    """
    Recursively extract type annotation from AST node.

    Args:
        annotation (ast.AST): AST node representing type annotation.

    Returns:
        str: Type annotation as string.
    """
    if isinstance(annotation, ast.Name):
        return annotation.id
    elif isinstance(annotation, ast.Attribute):
        return f"{annotation.value.id}.{annotation.attr}" if isinstance(annotation.value, ast.Name) else annotation.attr
    elif isinstance(annotation, ast.Subscript):
        return _get_type_annotation(annotation.value)
    else:
        return "Any"


def _extract_python_endpoints(source, result):
    """
    Extract Flask and Django endpoints from Python source code.

    Args:
        source (str): Python source code as string.
        result (dict): Main result dictionary for schema, updated with endpoints.
    """
    # Flask routes
    for match in re.finditer(r'@\s*(?:app|bp)\.route\(\s*([\'\"])\s*([^\'\"]+)\1\s*(?:,\s*methods\s*=\s*\[([^\]]+)\])?', source):
        path = match.group(2)
        methods_raw = match.group(3) or 'GET'
        methods = re.findall(r'[A-Za-z]+', methods_raw.upper()) or ['GET']
        for method in methods:
            result['endpoints'].append({
                'framework': 'flask',
                'method': method,
                'path': path,
                'class': None
            })

    # Django URL patterns
    for match in re.finditer(r'path\(\s*([\'\"])\s*([^\'\"]+)\1\s*,\s*([^,]+)', source):
        path = match.group(2)
        view_func = match.group(3).strip()
        result['endpoints'].append({
            'framework': 'django',
            'method': 'GET',
            'path': path,
            'class': view_func
        })


def _analyze_java_file(full_path, package_path, result, class_info, all_class_names,
                      inheritance_rels, composition_rels, dependency_rels, usage_rels, java_packages):
    """Enhanced Java file analysis using javalang"""
    import logging
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        tree = javalang.parse.parse(source)

        # Extract package
        package = None
        for path_node, pkg in tree.filter(javalang.tree.PackageDeclaration):
            package = pkg.name
            break

        # Extract imports for dependencies
        imports = set()
        for path_node, imp in tree.filter(javalang.tree.Import):
            if hasattr(imp, 'path'):
                imports.add(imp.path.split('.')[0])

        # Analyze classes
        for path_nodes, cls in tree.filter(javalang.tree.ClassDeclaration):
            class_name = cls.name
            all_class_names.add(class_name)

            # Inheritance
            if cls.extends:
                base_name = cls.extends.name
                inheritance_rels.append({'from': base_name, 'to': class_name, 'type': 'extends'})

            # Implements
            if cls.implements:
                for impl in cls.implements:
                    impl_name = impl.name
                    inheritance_rels.append({'from': impl_name, 'to': class_name, 'type': 'implements'})

            # Fields and compositions
            fields = set()
            compositions = set()
            state_fields = set()

            for field_path, field in tree.filter(javalang.tree.FieldDeclaration):
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
                        # Track state fields
                        if any(s in field_name.lower() for s in ['state', 'status', 'mode']):
                            state_fields.add(field_name)
                        # Composition candidate (validated later against discovered classes)
                        compositions.add(field_type)

            # Methods and use case extraction
            methods = set()
            usecases = []
            state_transitions = []
            method_calls = []
            for method_path, method in tree.filter(javalang.tree.MethodDeclaration):
                enclosing_class = None
                for path_node in reversed(method_path):
                    if isinstance(path_node, javalang.tree.ClassDeclaration):
                        enclosing_class = path_node.name
                        break
                if enclosing_class == class_name:
                    methods.add(method.name)
                    # Use case: treat public methods in main/game/controller classes as actions
                    if ('public' in method.modifiers and (
                        'Controller' in class_name or class_name.endswith('Controller') or
                        'Maze' in class_name or 'Game' in class_name or 'Main' in class_name)):
                        usecases.append({
                            'actor': 'User',
                            'action': method.name,
                            'controller': class_name
                        })
                    # State transitions: look for assignments to state fields
                    if method.body:
                        for stmt in method.body:
                            if hasattr(stmt, 'expression') and hasattr(stmt.expression, 'member'):
                                member = stmt.expression.member
                                if member in state_fields:
                                    state_transitions.append({
                                        'class': class_name,
                                        'state_field': member,
                                        'action': method.name
                                    })
                    # Method calls for sequence/activity diagrams
                    if method.body:
                        for stmt in method.body:
                            if hasattr(stmt, 'expression') and hasattr(stmt.expression, 'qualifier'):
                                callee = stmt.expression.qualifier
                                method_calls.append({
                                    'caller': class_name,
                                    'callee': callee,
                                    'method': method.name
                                })
                    for param in method.parameters or []:
                        param_type = getattr(param, 'type', None)
                        if param_type and hasattr(param_type, 'name'):
                            param_type = param_type.name
                        if param_type:
                            usage_rels.append({'from': class_name, 'to': param_type, 'type': 'uses'})

            # Heuristic enrichment by scanning class body text for compositions/usages
            try:
                class_text = _extract_java_class_content(source, class_name)
            except Exception:
                class_text = None
            if class_text:
                # Detect this.field = new OtherClass()
                for m in re.finditer(r'\bthis\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', class_text):
                    fld, rhs = m.group(1), m.group(2)
                    fields.add(f"{fld}: {rhs}")
                    if rhs != class_name:
                        compositions.add(rhs)
                # Detect local instantiations: new OtherClass()
                for m in re.finditer(r'\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', class_text):
                    rhs = m.group(1)
                    if rhs != class_name:
                        usage_rels.append({'from': class_name, 'to': rhs, 'type': 'uses'})
                # Detect static calls: OtherClass.method(
                for m in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\(', class_text):
                    qual = m.group(1)
                    if qual != class_name:
                        usage_rels.append({'from': class_name, 'to': qual, 'type': 'uses'})
                # Detect local variable declarations: OtherClass var = ...; or OtherClass var;
                for m in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:[=;])', class_text):
                    tname = m.group(1)
                    if tname != class_name:
                        usage_rels.append({'from': class_name, 'to': tname, 'type': 'uses'})

            modifiers = set(getattr(cls, 'modifiers', []))
            stereotype = 'interface' if isinstance(cls, javalang.tree.InterfaceDeclaration) else 'abstract' if 'abstract' in modifiers else 'class'

            class_entry = {
                'class': class_name,
                'fields': sorted(list(fields)),
                'methods': sorted(list(methods)),
                'stereotype': stereotype,
                'abstract': 'abstract' in modifiers,
                'package': package or package_path
            }
            result['java'].append(class_entry)
            class_info[class_name] = {
                'lang': 'java',
                'fields': fields,
                'methods': methods,
                'bases': [cls.extends.name] if cls.extends else [],
                'stereotype': stereotype,
                'package': package
            }
            for comp in compositions:
                composition_rels.append({'from': class_name, 'to': comp, 'type': 'composition'})
            for imp in imports:
                dependency_rels.append({'from': class_name, 'to': imp, 'type': 'dependency'})
            # Add extracted use cases and state transitions
            if usecases:
                result.setdefault('usecases', []).extend(usecases)
            if state_transitions:
                result.setdefault('states', []).extend(state_transitions)
            if method_calls:
                result.setdefault('sequence', []).extend(method_calls)
    except Exception as e:
        logging.error(f"Java file analysis failed for {full_path}: {e}")


def _extract_java_class_content(source: str, class_name: str) -> str:
    """Extract the textual body of a Java class by matching braces starting from class declaration."""
    # Find class declaration start
    pattern = re.compile(r'(?:public\s+|protected\s+|private\s+|abstract\s+|final\s+|static\s+)*class\s+' + re.escape(class_name) + r'\b[^\{]*\{', re.MULTILINE)
    m = pattern.search(source)
    if not m:
        # fallback: interface or record (not typical here but safe)
        pattern2 = re.compile(r'(?:public\s+|protected\s+|private\s+)*\b(?:class|interface|record)\s+' + re.escape(class_name) + r'\b[^\{]*\{', re.MULTILINE)
        m = pattern2.search(source)
        if not m:
            return ''
    start = m.end() - 1  # position of opening brace
    # Match braces to find end of class
    brace = 0
    i = start
    content = ''
    while i < len(source):
        ch = source[i]
        if ch == '{':
            brace += 1
            if brace > 1:
                content += ch
        elif ch == '}':
            if brace == 1:
                break
            brace -= 1
            content += ch
        else:
            if brace >= 1:
                content += ch
        i += 1
    return content


def _extract_java_endpoints(source, result):
    """Extract Spring Boot endpoints"""
    http_methods = {
        'GetMapping': 'GET', 'PostMapping': 'POST', 'PutMapping': 'PUT',
        'DeleteMapping': 'DELETE', 'PatchMapping': 'PATCH', 'RequestMapping': None
    }

    for match in re.finditer(r'@\s*(' + '|'.join(http_methods.keys()) + r')\s*\([^)]*\)', source):
        annotation = match.group(1)
        method = http_methods[annotation] or 'GET'

        # Extract path from annotation
        path_match = re.search(r'value\s*=\s*["\']([^"\']+)["\']', match.group(0))
        if path_match:
            path = path_match.group(1)
        else:
            path = f"/{annotation.lower()}"

        result['endpoints'].append({
            'framework': 'spring',
            'method': method,
            'path': path,
            'class': None
        })


def _analyze_csharp_file(full_path, package_path, result, class_info, all_class_names,
                        inheritance_rels, composition_rels, dependency_rels, usage_rels, cs_namespaces):
    """Enhanced C# file analysis"""
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        # Extract namespace
        namespace_match = re.search(r'namespace\s+([A-Za-z_][A-Za-z0-9_.]*)', source)
        namespace = namespace_match.group(1) if namespace_match else package_path

        # Extract using statements for dependencies
        using_matches = re.findall(r'using\s+([A-Za-z_][A-Za-z0-9_.]*)\s*;', source)
        imports = set(imp.split('.')[0] for imp in using_matches)

        # Extract classes
        class_pattern = r'\b(?:public|private|protected|internal)?\s*(?:abstract\s+|sealed\s+|static\s+)?\s*(?:partial\s+)?\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([A-Za-z0-9_\s,<>\.]+))?'
        for match in re.finditer(class_pattern, source, re.MULTILINE):
            class_name = match.group(1)
            all_class_names.add(class_name)

            inheritance_str = match.group(2) or ''
            bases = []

            if inheritance_str:
                base_parts = [part.strip() for part in inheritance_str.split(',')]
                for part in base_parts:
                    # Remove access modifiers
                    clean_part = re.sub(r'\b(public|private|protected|internal)\s+', '', part)
                    base_name = clean_part.split()[0] if clean_part.split() else clean_part
                    bases.append(base_name)

                    # Determine relationship type
                    if 'I' == base_name[0] or 'interface' in clean_part.lower():
                        inheritance_rels.append({'from': base_name, 'to': class_name, 'type': 'implements'})
                    else:
                        inheritance_rels.append({'from': base_name, 'to': class_name, 'type': 'extends'})

            # Extract fields
            fields = set()
            field_pattern = r'\b(?:public|private|protected|internal|static|readonly)\s+([A-Za-z_][A-Za-z0-9_<>\[\],\s]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*[^;]+)?\s*;'
            for field_match in re.finditer(field_pattern, source):
                field_type = field_match.group(1).strip()
                field_name = field_match.group(2)
                fields.add(f"{field_name}: {field_type}")

                # Composition candidate; validated at relation build stage
                clean_type = re.sub(r'<[^>]*>', '', field_type).strip()
                if clean_type and clean_type != class_name:
                    composition_rels.append({'from': class_name, 'to': clean_type, 'type': 'composition'})

            # Extract methods
            methods = set()
            method_pattern = r'\b(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*[A-Za-z_][A-Za-z0-9_<>\[\],\s]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
            for method_match in re.finditer(method_pattern, source):
                method_name = method_match.group(1)
                if method_name not in ['if', 'for', 'while', 'switch', 'try', 'catch']:  # Filter keywords
                    methods.add(method_name)

            # Determine stereotype
            is_abstract = 'abstract' in match.group(0)
            is_static = 'static' in match.group(0)
            stereotype = 'abstract' if is_abstract else 'class'

            class_entry = {
                'class': class_name,
                'fields': sorted(list(fields)),
                'methods': sorted(list(methods)),
                'stereotype': stereotype,
                'abstract': is_abstract,
                'namespace': namespace
            }

            result['csharp'].append(class_entry)
            class_info[class_name] = {
                'lang': 'csharp',
                'fields': fields,
                'methods': methods,
                'bases': bases,
                'stereotype': stereotype,
                'package': namespace
            }

            # Add dependencies
            for imp in imports:
                if imp in all_class_names and imp != class_name:
                    dependency_rels.append({'from': class_name, 'to': imp, 'type': 'dependency'})

    except Exception as e:
        logging.warning(f"Error analyzing C# file {full_path}: {e}")


def _analyze_javascript_file(full_path, package_path, result, class_info, all_class_names,
                           inheritance_rels, composition_rels, dependency_rels, usage_rels, js_modules):
    """Enhanced JavaScript file analysis"""
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        # Extract require/import statements for dependencies
        imports = set()
        require_matches = re.findall(r'require\(\s*[\'"]([^\'"]+)[\'"]\s*\)', source)
        import_matches = re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', source)
        imports.update(imp.split('/')[0] for imp in require_matches + import_matches)

        # Extract ES6 classes
        class_pattern = r'\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:extends\s+([A-Za-z_$][A-Za-z0-9_$.]*))?\s*{'
        for match in re.finditer(class_pattern, source):
            class_name = match.group(1)
            all_class_names.add(class_name)

            base_class = match.group(2)
            if base_class:
                inheritance_rels.append({'from': base_class, 'to': class_name, 'type': 'extends'})

            # Extract constructor and methods
            class_content = _extract_class_content(source, match.start())
            fields = set()
            methods = set()

            # Constructor parameters as fields
            constructor_match = re.search(r'constructor\s*\(([^)]*)\)', class_content)
            if constructor_match:
                params = constructor_match.group(1)
                param_names = re.findall(r'([A-Za-z_$][A-Za-z0-9_$]*)\s*(?::\s*[^,)]+)?', params)
                fields.update(param_names)

            # Methods
            method_matches = re.findall(r'\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\(', class_content)
            methods.update(method_matches)

            # Remove constructor from methods
            methods.discard('constructor')

            # Instance field assignments: this.foo = new Bar() or this.foo = expr
            for m in re.finditer(r'\bthis\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*new\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(', class_content):
                fld, rhs_cls = m.group(1), m.group(2)
                # record field with inferred type
                fields.add(f"{fld}: {rhs_cls}")
                if rhs_cls != class_name:
                    composition_rels.append({'from': class_name, 'to': rhs_cls, 'type': 'composition'})
            # generic assignment without type inference
            for m in re.finditer(r'\bthis\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*[^;]+;', class_content):
                fld = m.group(1)
                # don't overwrite typed form if already present
                if not any(str(f).startswith(fld + ":") or str(f) == fld for f in fields):
                    fields.add(fld)

            class_entry = {
                'class': class_name,
                'fields': sorted(list(fields)),
                'methods': sorted(list(methods)),
                'stereotype': 'class',
                'abstract': False
            }

            result['javascript'].append(class_entry)
            class_info[class_name] = {
                'lang': 'javascript',
                'fields': fields,
                'methods': methods,
                'bases': [base_class] if base_class else [],
                'stereotype': 'class',
                'package': package_path
            }

            # Add dependencies
            for imp in imports:
                if imp in all_class_names and imp != class_name:
                    dependency_rels.append({'from': class_name, 'to': imp, 'type': 'dependency'})

        # Extract Express endpoints
        _extract_js_endpoints(source, result)

    except Exception as e:
        logging.warning(f"Error analyzing JavaScript file {full_path}: {e}")


def _extract_class_content(source, start_pos):
    """Extract class content between braces"""
    brace_count = 0
    content = ""
    i = start_pos

    while i < len(source):
        char = source[i]
        if char == '{':
            brace_count += 1
            if brace_count > 1:
                content += char
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                break
            else:
                content += char
        elif brace_count > 0:
            content += char
        i += 1

    return content


def _extract_js_endpoints(source, result):
    """Extract Express.js endpoints"""
    endpoint_pattern = r'\b(?:app|router)\.(get|post|put|delete|patch|options|head)\(\s*([\'"`])\s*([^\'"`]+)\2'
    for match in re.finditer(endpoint_pattern, source, re.IGNORECASE):
        method = match.group(1).upper()
        path = match.group(3)
        result['endpoints'].append({
            'framework': 'express',
            'method': method,
            'path': path,
            'class': None
        })


def _analyze_typescript_file(full_path, package_path, result, class_info, all_class_names,
                           inheritance_rels, composition_rels, dependency_rels, usage_rels, ts_modules):
    """Enhanced TypeScript file analysis"""
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        # Extract import statements for dependencies
        imports = set()
        import_matches = re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', source)
        imports.update(imp.split('/')[0] for imp in import_matches)

        # Extract classes and interfaces
        type_pattern = r'\b(?:export\s+)?(?:abstract\s+)?\s*(class|interface)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:extends\s+([A-Za-z_$][A-Za-z0-9_$,]*))?(?:\s+implements\s+([A-Za-z_$][A-Za-z0-9_$,]*))?\s*{'
        for match in re.finditer(type_pattern, source):
            type_kind = match.group(1)
            class_name = match.group(2)
            all_class_names.add(class_name)

            extends_str = match.group(3) or ''
            implements_str = match.group(4) or ''

            # Process extends
            if extends_str:
                base_classes = [cls.strip() for cls in extends_str.split(',')]
                for base in base_classes:
                    inheritance_rels.append({'from': base, 'to': class_name, 'type': 'extends'})

            # Process implements
            if implements_str:
                interfaces = [iface.strip() for iface in implements_str.split(',')]
                for iface in interfaces:
                    inheritance_rels.append({'from': iface, 'to': class_name, 'type': 'implements'})

            # Extract fields and methods
            type_content = _extract_class_content(source, match.start())
            fields = set()
            methods = set()

            # Fields with types
            field_pattern = r'\b(?:public|private|protected|readonly)?\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*([A-Za-z_$][A-Za-z0-9_$\[\]<>\s|&]+)\s*(?:=\s*[^;]+)?\s*;'
            for field_match in re.finditer(field_pattern, type_content):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                fields.add(f"{field_name}: {field_type}")

                # Check for composition
                clean_type = re.sub(r'<[^>]*>', '', field_type).strip()
                if clean_type in all_class_names:
                    composition_rels.append({'from': class_name, 'to': clean_type, 'type': 'composition'})

            # Methods
            method_pattern = r'\b(?:public|private|protected|async)?\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*{'
            for method_match in re.finditer(method_pattern, type_content):
                method_name = method_match.group(1)
                if method_name not in ['constructor', 'if', 'for', 'while']:
                    methods.add(method_name)

            # Instance field assignments: this.foo = new Bar() or this.foo = expr
            for m in re.finditer(r'\bthis\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*new\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(', type_content):
                fld, rhs_cls = m.group(1), m.group(2)
                fields.add(f"{fld}: {rhs_cls}")
                if rhs_cls != class_name:
                    composition_rels.append({'from': class_name, 'to': rhs_cls, 'type': 'composition'})
            for m in re.finditer(r'\bthis\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*[^;]+;', type_content):
                fld = m.group(1)
                if not any(str(f).startswith(fld + ":") or str(f) == fld for f in fields):
                    fields.add(fld)

            stereotype = 'interface' if type_kind == 'interface' else 'abstract' if 'abstract' in match.group(0) else 'class'

            class_entry = {
                'class': class_name,
                'fields': sorted(list(fields)),
                'methods': sorted(list(methods)),
                'stereotype': stereotype,
                'abstract': stereotype == 'abstract'
            }

            result['typescript'].append(class_entry)
            class_info[class_name] = {
                'lang': 'typescript',
                'fields': fields,
                'methods': methods,
                'bases': base_classes if extends_str else [],
                'stereotype': stereotype,
                'package': package_path
            }

            # Add dependencies
            for imp in imports:
                if imp in all_class_names and imp != class_name:
                    dependency_rels.append({'from': class_name, 'to': imp, 'type': 'dependency'})

        # Extract endpoints
        _extract_js_endpoints(source, result)

    except Exception as e:
        logging.warning(f"Error analyzing TypeScript file {full_path}: {e}")


def _analyze_cpp_file(full_path, package_path, result, class_info, all_class_names,
                     inheritance_rels, composition_rels, dependency_rels, usage_rels):
    """Enhanced C/C++ file analysis"""
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        # Extract #include statements for dependencies
        includes = set()
        include_matches = re.findall(r'#include\s*[<"]([^>"]+)[>"]', source)
        includes.update(inc.split('/')[0] for inc in include_matches)

        # Extract classes and structs
        type_pattern = r'\b(class|struct)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([A-Za-z0-9_\s,:]+))?\s*{'
        for match in re.finditer(type_pattern, source):
            type_kind = match.group(1)
            class_name = match.group(2)
            all_class_names.add(class_name)

            inheritance_str = match.group(3) or ''

            # Process inheritance
            if inheritance_str:
                base_parts = [part.strip() for part in inheritance_str.split(',')]
                for part in base_parts:
                    # Remove access specifiers
                    clean_part = re.sub(r'\b(public|private|protected|virtual)\s+', '', part)
                    base_name = clean_part.split()[0] if clean_part.split() else clean_part
                    inheritance_rels.append({'from': base_name, 'to': class_name, 'type': 'extends'})

            # Extract class content
            type_content = _extract_class_content(source, match.start())
            fields = set()
            methods = set()

            # Fields
            field_pattern = r'\b(?:[A-Za-z_][A-Za-z0-9_<>\[\]\s]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]*\])?\s*;'
            for field_match in re.finditer(field_pattern, type_content):
                field_name = field_match.group(1)
                if field_name not in ['if', 'for', 'while', 'return']:  # Filter keywords
                    fields.add(field_name)

            # Methods
            method_pattern = r'\b[A-Za-z_][A-Za-z0-9_<>\[\]\s]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
            for method_match in re.finditer(method_pattern, type_content):
                method_name = method_match.group(1)
                if method_name not in ['if', 'for', 'while', 'return']:
                    methods.add(method_name)

            stereotype = 'struct' if type_kind == 'struct' else 'class'

            class_entry = {
                'class': class_name,
                'fields': sorted(list(fields)),
                'methods': sorted(list(methods)),
                'stereotype': stereotype,
                'abstract': False
            }

            result['cpp'].append(class_entry)
            class_info[class_name] = {
                'lang': 'cpp',
                'fields': fields,
                'methods': methods,
                'bases': [],
                'stereotype': stereotype,
                'package': package_path
            }

            # Add dependencies
            for inc in includes:
                if inc in all_class_names and inc != class_name:
                    dependency_rels.append({'from': class_name, 'to': inc, 'type': 'dependency'})

    except Exception as e:
        logging.warning(f"Error analyzing C++ file {full_path}: {e}")


def _build_relations(inheritance_rels, composition_rels, dependency_rels, usage_rels, all_class_names):
    """Build comprehensive relations list with deduplication"""
    relations = []

    # Add all relation types
    for rel in inheritance_rels + composition_rels + dependency_rels + usage_rels:
        if rel['from'] in all_class_names and rel['to'] in all_class_names:
            rel_copy = dict(rel)
            rel_copy['source'] = 'heuristic'
            relations.append(rel_copy)

    # Remove duplicates
    seen = set()
    unique_relations = []
    for rel in relations:
        key = (rel['from'], rel['to'], rel['type'])
        if key not in seen:
            seen.add(key)
            unique_relations.append(rel)

    return unique_relations


def _detect_patterns(class_info, relations):
    """Detect common design patterns"""
    patterns = []

    # Singleton pattern detection
    for class_name, info in class_info.items():
        methods = info.get('methods', [])
        fields = info.get('fields', [])

        # Ensure methods and fields are lists
        if not isinstance(methods, list):
            methods = []
        if not isinstance(fields, list):
            fields = []

        if any('getinstance' in method.lower() or 'instance' in method.lower() for method in methods):
            fields_str = ' '.join(str(f).lower() for f in fields)
            if 'private' in fields_str or 'static' in fields_str:
                patterns.append({
                    'type': 'singleton',
                    'classes': [class_name]
                })

    # Factory pattern detection
    for class_name, info in class_info.items():
        methods = info.get('methods', [])
        if not isinstance(methods, list):
            methods = []

        if any('create' in method.lower() or 'factory' in method.lower() or 'build' in method.lower() for method in methods):
            patterns.append({
                'type': 'factory',
                'classes': [class_name]
            })

    # Observer pattern detection
    observer_classes = []
    for class_name, info in class_info.items():
        methods = info.get('methods', [])
        if not isinstance(methods, list):
            methods = []

        if any('notify' in method.lower() or 'update' in method.lower() or 'attach' in method.lower() for method in methods):
            observer_classes.append(class_name)

    if len(observer_classes) >= 2:
        patterns.append({
            'type': 'observer',
            'classes': observer_classes
        })

    return patterns


def _detect_layers(class_info, relations):
    """Detect architectural layers"""
    layers = {'presentation': [], 'business': [], 'data': []}

    for class_name, info in class_info.items():
        methods = info.get('methods', [])
        fields = info.get('fields', [])

        # Ensure methods and fields are lists
        if not isinstance(methods, list):
            methods = []
        if not isinstance(fields, list):
            fields = []

        methods_lower = [m.lower() for m in methods]
        fields_lower = [f.lower() for f in fields]
        all_text = ' '.join(methods_lower + fields_lower)

        # Presentation layer indicators
        if any(keyword in all_text for keyword in
               ['controller', 'view', 'ui', 'component', 'page', 'screen', 'handler', 'endpoint']):
            layers['presentation'].append(class_name)

        # Business layer indicators
        elif any(keyword in all_text for keyword in
                 ['service', 'manager', 'logic', 'processor', 'validator', 'workflow']):
            layers['business'].append(class_name)

        # Data layer indicators
        elif any(keyword in all_text for keyword in
                 ['repository', 'dao', 'entity', 'model', 'database', 'query', 'persist']):
            layers['data'].append(class_name)

    return [
        {'name': layer_name, 'classes': classes}
        for layer_name, classes in layers.items()
        if classes
    ]


def _extract_system_name(repo_path):
    """Extract meaningful system name"""
    try:
        repo_name = os.path.basename(os.path.abspath(repo_path))
        if repo_name.startswith('tmp') or len(repo_name) < 3:
            import subprocess
            remote_url = subprocess.check_output(['git', '-C', repo_path, 'config', '--get', 'remote.origin.url'], text=True).strip()
            if remote_url:
                if '/' in remote_url:
                    repo_name = remote_url.split('/')[-1].replace('.git', '')
                else:
                    repo_name = remote_url.replace('.git', '')
        return repo_name
    except Exception:
        return 'System'



def analyze_repo(repo_path, limits=None):
    # If any UML diagram section is missing or empty, auto-populate with AI-generated details
    def ai_populate_if_missing(result):
        # Usecases
        if not result.get('usecases'):
            for ep in result.get('endpoints', []):
                result.setdefault('usecases', []).append({
                    'actor': 'User',
                    'action': ep.get('method', 'action'),
                    'controller': ep.get('class', ep.get('path', 'Unknown'))
                })
            for lang in ['java', 'python', 'csharp', 'javascript', 'typescript']:
                for cls in result.get(lang, []):
                    for method in cls.get('methods', []):
                        result.setdefault('usecases', []).append({
                            'actor': 'User',
                            'action': method,
                            'controller': cls.get('class', 'Unknown')
                        })
        # States
        if not result.get('states'):
            for lang in ['java', 'python', 'csharp', 'javascript', 'typescript']:
                for cls in result.get(lang, []):
                    state_fields = [f for f in cls.get('fields', []) if any(s in f.lower() for s in ['state', 'status', 'mode'])]
                    if state_fields:
                        for method in cls.get('methods', []):
                            result.setdefault('states', []).append({
                                'class': cls.get('class', 'Unknown'),
                                'state_fields': state_fields,
                                'action': method
                            })
        # Sequence diagrams
        if not result.get('sequence'):
            result['sequence'] = []
            for lang in ['java', 'python', 'csharp', 'javascript', 'typescript']:
                for cls in result.get(lang, []):
                    for method in cls.get('methods', []):
                        result['sequence'].append({
                            'caller': 'User',
                            'callee': cls.get('class', 'Unknown'),
                            'method': method
                        })
        # Activity diagrams
        if not result.get('activity'):
            result['activity'] = []
            for lang in ['java', 'python', 'csharp', 'javascript', 'typescript']:
                for cls in result.get(lang, []):
                    for method in cls.get('methods', []):
                        result['activity'].append({
                            'step': method,
                            'class': cls.get('class', 'Unknown')
                        })
        # Class diagrams (fallback)
        if not result.get('classdiagram'):
            result['classdiagram'] = []
            for lang in ['java', 'python', 'csharp', 'javascript', 'typescript', 'cpp', 'c']:
                for cls in result.get(lang, []):
                    result['classdiagram'].append({
                        'class': cls.get('class', 'Unknown'),
                        'fields': cls.get('fields', []),
                        'methods': cls.get('methods', []),
                        'stereotype': cls.get('stereotype', 'class')
                    })
        # Add more AI population logic for other diagram types as needed

    """
    Enhanced analysis with consistent parsing across all languages.
    Extracts classes, fields, methods, and relationships with high accuracy.
    
    Args:
        repo_path: Path to the repository to analyze
        limits: Dictionary with max_files, max_bytes, etc. for security
    """
    if limits is None:
        from security import validate_environment_limits
        limits = validate_environment_limits()
    
    result = {
        'python': [], 'java': [], 'csharp': [],
        'javascript': [], 'typescript': [],
        'cpp': [], 'c': [],
        'html': [], 'css': [],
        'endpoints': [],
        'relations': [],
        'patterns': [],  # design patterns
        'layers': []     # architectural layers
    }

    # Enhanced tracking structures
    all_class_names = set()
    class_info = {}  # class_name -> {lang, fields, methods, bases, stereotype, package}

    # Language-specific tracking
    java_packages = {}
    cs_namespaces = {}
    py_modules = {}
    js_modules = {}
    ts_modules = {}

    # Relationship tracking
    inheritance_rels = []
    composition_rels = []
    dependency_rels = []
    usage_rels = []

    max_bytes = limits.get('max_bytes', 2_000_000)
    max_files = limits.get('max_files', 20000)
    files_scanned = 0

    skip_dirs = {'.git', 'node_modules', 'dist', 'build', 'target', 'out', 'bin', 'obj', '__pycache__', '.tox', '.venv', 'venv', '.idea', '.vs'}
    import concurrent.futures
    file_tasks = []
    for root, dirs, files in os.walk(repo_path):
        if files_scanned >= max_files:
            break
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]

        for file in files:
            if files_scanned >= max_files:
                break
            full = os.path.join(root, file)
            try:
                if os.path.getsize(full) > max_bytes:
                    continue
            except Exception:
                pass
            if os.path.islink(full):
                continue
            files_scanned += 1

            # Extract package/module info
            rel_path = os.path.relpath(root, repo_path)
            package_path = rel_path.replace(os.sep, '.').replace('..', '').strip('.')

            file_tasks.append((full, package_path, file))

    def process_file(args):
        full, package_path, file = args
        if file.endswith('.py'):
            _analyze_python_file(full, package_path, result, class_info, all_class_names,
                              inheritance_rels, composition_rels, dependency_rels, usage_rels, py_modules)
        elif file.endswith('.java'):
            _analyze_java_file(full, package_path, result, class_info, all_class_names,
                             inheritance_rels, composition_rels, dependency_rels, usage_rels, java_packages)
        elif file.endswith('.cs'):
            _analyze_csharp_file(full, package_path, result, class_info, all_class_names,
                               inheritance_rels, composition_rels, dependency_rels, usage_rels, cs_namespaces)
        elif file.endswith(('.js', '.jsx')):
            _analyze_javascript_file(full, package_path, result, class_info, all_class_names,
                                   inheritance_rels, composition_rels, dependency_rels, usage_rels, js_modules)
        elif file.endswith(('.ts', '.tsx')):
            _analyze_typescript_file(full, package_path, result, class_info, all_class_names,
                                   inheritance_rels, composition_rels, dependency_rels, usage_rels, ts_modules)
        elif file.endswith(('.cpp', '.hpp', '.h', '.cc', '.cxx', '.hh', '.hxx')):
            _analyze_cpp_file(full, package_path, result, class_info, all_class_names,
                            inheritance_rels, composition_rels, dependency_rels, usage_rels)

    # Use ThreadPoolExecutor for parallel file processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(process_file, file_tasks))

    # Build comprehensive relations
    result['relations'] = _build_relations(inheritance_rels, composition_rels, dependency_rels, usage_rels, all_class_names)

    # Detect patterns and layers
    result['patterns'] = _detect_patterns(class_info, result['relations'])
    result['layers'] = _detect_layers(class_info, result['relations'])

    # Add metadata
    result['meta'] = {
        'files_scanned': files_scanned,
        'classes_found': len(all_class_names),
        'languages': list(set(info['lang'] for info in class_info.values())),
        'system': _extract_system_name(repo_path)
    }

    # Optional: populate secondary diagram sections if empty
    ai_populate_if_missing(result)

    return result
def _safe_extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        pass
    if '```' in text:
        start = text.find('```')
        end = text.rfind('```')
        if start != -1 and end != -1 and end > start:
            inner = text[start+3:end]
            if '\n' in inner:
                inner = inner.split('\n', 1)[1]
            try:
                return json.loads(inner)
            except Exception:
                pass
    return None


def call_gemini(ast_json):
    if STUB_LLM:
        logging.warning('STUB_LLM enabled: returning AST JSON as schema without calling an LLM.')
        return {'schema': ast_json}

    api_key = os.getenv('GROQ_API_KEY')
    api_url = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions')
    model = os.getenv('GROQ_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')

    if not api_key:
        return {'error': 'GROQ_API_KEY not set.'}

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    prompt_text = f"{PROMPT}\n\n{json.dumps(ast_json, ensure_ascii=False)}"
    payload = {
        'model': model,
        'messages': [
            { 'role': 'system', 'content': 'You are an expert code analysis tool. Return ONLY valid JSON. Do not include code fences.' },
            { 'role': 'user', 'content': prompt_text }
        ],
        'temperature': 0.2
    }

    def merge_schemas(ast_obj: dict, ai_obj: dict):
        merged = { 'python': [], 'java': [], 'csharp': [], 'javascript': [], 'typescript': [], 'cpp': [], 'c': [], 'relations': [] }
        all_ast_class_names = set()
        all_ai_class_names = set()
        by_lang = {}
        # Collect all AST and AI class names across languages
        for lang in ['python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c']:
            ast_list = ast_obj.get(lang, []) or []
            ai_list = ai_obj.get(lang, []) or []
            by_name = {}
            for item in ast_list:
                name = item.get('class')
                if not name:
                    continue
                all_ast_class_names.add(name)
                cur = by_name.setdefault(name, {'class': name, 'fields': set(), 'methods': set(), 'stereotype': None, 'abstract': False, 'package': None})
                for f in item.get('fields', []) or []:
                    cur['fields'].add(f)
                for m in item.get('methods', []) or []:
                    cur['methods'].add(m)
                st = (item.get('stereotype') or '').lower() or None
                if st:
                    cur['stereotype'] = st
                if isinstance(item.get('abstract'), bool):
                    cur['abstract'] = cur['abstract'] or item['abstract']
                pkg = item.get('package') or item.get('namespace')
                if pkg:
                    cur['package'] = pkg
            for item in ai_list:
                name = item.get('class')
                if not name:
                    continue
                all_ai_class_names.add(name)
                # If class not in AST, add it from AI
                if name not in by_name:
                    cur = by_name.setdefault(name, {'class': name, 'fields': set(), 'methods': set(), 'stereotype': None, 'abstract': False, 'package': None})
                else:
                    cur = by_name[name]
                for f in item.get('fields', []) or []:
                    cur['fields'].add(f)
                for m in item.get('methods', []) or []:
                    cur['methods'].add(m)
                st = (item.get('stereotype') or '').lower() or None
                if st:
                    cur['stereotype'] = st
                if isinstance(item.get('abstract'), bool):
                    cur['abstract'] = cur['abstract'] or item['abstract']
                pkg = item.get('package') or item.get('namespace')
                if pkg:
                    cur['package'] = pkg
            merged[lang] = [
                {
                    'class': n,
                    'fields': sorted(list(v['fields'])),
                    'methods': sorted(list(v['methods'])),
                    **({'stereotype': v['stereotype']} if v['stereotype'] else {}),
                    **({'abstract': True} if v['abstract'] else {}),
                    **({'package': v['package']} if v['package'] else {}),
                    **({'namespace': v['package']} if v['package'] and lang == 'csharp' else {})
                }
                for n, v in by_name.items()
            ]
            by_lang[lang] = by_name
        # relations with provenance tags
        rels = []
        ast_relations = ast_obj.get('relations', []) or []
        ai_relations = ai_obj.get('relations', []) or []
        all_class_names = all_ast_class_names | all_ai_class_names
        for r in ast_relations:
            if r and r.get('from') and r.get('to') and r.get('type'):
                rr = dict(r)
                rr['source'] = rr.get('source') or 'heuristic'
                rels.append(rr)
        for r in ai_relations:
            if r and r.get('from') and r.get('to') and r.get('type'):
                # Add AI relations if either class exists in any language
                if r['from'] in all_class_names and r['to'] in all_class_names:
                    rr = dict(r)
                    rr['source'] = rr.get('source') or 'ai'
                    rels.append(rr)
        # dedupe
        seen = set()
        uniq = []
        for r in rels:
            key = (r.get('from'), r.get('to'), r.get('type'), r.get('source'))
            if key not in seen:
                seen.add(key)
                uniq.append(r)
        merged['relations'] = uniq
        # pass-through other data
        for k in ['html', 'css', 'endpoints', 'patterns', 'layers', 'meta']:
            if isinstance(ast_obj.get(k), list) or isinstance(ast_obj.get(k), dict):
                merged[k] = ast_obj.get(k)
        return merged

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        parsed = _safe_extract_json(text)
        if isinstance(parsed, dict):
            try:
                merged = merge_schemas(ast_json, parsed)
            except Exception:
                merged = parsed
            return {'schema': merged}
        else:
            return {'schema': ast_json}
    except requests.HTTPError as http_err:
        try:
            err_body = response.json()
        except Exception:
            err_body = response.text if 'response' in locals() else str(http_err)
        logging.error(f'Groq API HTTP error: {http_err}, body: {err_body}')
        return {'error': f'HTTP {getattr(response, "status_code", "?")}', 'body': err_body}
    except Exception as e:
        logging.error(f'Groq API call failed: {e}')
        return {'error': str(e)}
