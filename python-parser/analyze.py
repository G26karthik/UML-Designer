import os
import re
import ast
import javalang
import logging
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Return stubbed schema when true (for offline testing)
STUB_LLM = os.getenv('STUB_LLM', 'false').lower() in ('1', 'true', 'yes')

# Prompt to steer the model to return the exact JSON shape we need
PROMPT = '''You are a code analysis tool. From the provided AST summary, produce ONLY JSON (no markdown fences) matching exactly this schema:
{
    "python": [{"class": "Name", "fields": ["f1", "f2: Type"], "methods": ["m1", "m2"]}],
    "java":   [{"class": "Name", "fields": ["f1", "f2: Type"], "methods": ["m1", "m2"]}],
    "csharp": [{"class": "Name", "fields": ["f1", "f2: Type"], "methods": ["m1", "m2"]}],
    "relations": [{"from": "ClassA", "to": "ClassB", "type": "uses|extends|implements|aggregates|composes"}]
}
Methods should be names only (no parentheses). Only include classes actually present. If unsure about relations, return an empty array for "relations". Do not include any prose.'''


def _norm_type_name(name: str) -> str:
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


def analyze_repo(repo_path):
    """
    Walk the repo and extract a lightweight AST summary:
    - python/java/csharp: list of { class, fields, methods }
    - relations: heuristic list among Java (extends, implements, uses)

    Notes:
    - Python fields are gathered from class-level assignments/annotations and self.<name> in __init__.
    - Java fields are attached to their enclosing ClassDeclaration; parameter types contribute to 'uses'.
    """
    result = {
        'python': [], 'java': [], 'csharp': [],
        'javascript': [], 'typescript': [],
        'cpp': [], 'c': [],
        'html': [], 'css': [],
        'relations': []
    }
    java_class_names = set()
    py_class_names = set()
    cs_class_names = set()
    js_class_names = set()
    ts_class_names = set()
    cpp_class_names = set()

    # Index for quick class lookup to append fields/methods later if needed
    py_index = {}
    java_index = {}

    # First pass: gather classes/methods and type info
    java_types = {}  # className -> {extends: [], implements: [], uses: set()}
    py_bases = {}    # className -> [bases]
    cs_types = {}    # className -> {extends: [], implements: []}
    js_types = {}    # className -> {extends: []}
    ts_types = {}    # className -> {extends: [], implements: []}
    cpp_types = {}   # className -> {extends: []}

    max_bytes = int(os.getenv('MAX_FILE_BYTES', str(500_000)))  # 500 KB default
    max_files = int(os.getenv('MAX_FILES', str(5000)))  # hard cap of files to scan
    files_scanned = 0
    skip_dirs = {'.git', 'node_modules', 'dist', 'build', 'target', 'out', 'bin', 'obj', '__pycache__', '.tox', '.venv', 'venv', '.idea', '.vs'}
    for root, dirs, files in os.walk(repo_path):
        if files_scanned >= max_files:
            break
        # Prune heavy/unnecessary directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        # Skip symlinked directories
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
            # Skip symlinked files
            if os.path.islink(full):
                continue
            files_scanned += 1
            if file.endswith('.py'):
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    try:
                        tree = ast.parse(f.read())
                    except Exception:
                        continue
                    for node in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
                        cls_name = node.name
                        py_class_names.add(cls_name)
                        # bases
                        bases = []
                        for b in node.bases:
                            try:
                                if isinstance(b, ast.Name):
                                    bases.append(b.id)
                                elif isinstance(b, ast.Attribute):
                                    bases.append(b.attr)
                                elif isinstance(b, ast.Subscript) and isinstance(b.value, ast.Name):
                                    bases.append(b.value.id)
                            except Exception:
                                continue
                        if bases:
                            py_bases[cls_name] = [_norm_type_name(x) for x in bases]
                        # fields: class-level assignments/annassigns
                        fields = []
                        for n in node.body:
                            if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                                t = getattr(n.annotation, 'id', None) or getattr(getattr(n.annotation, 'attr', None), 'id', None)
                                fields.append(f"{n.target.id}: {t}" if t else n.target.id)
                            elif isinstance(n, ast.Assign):
                                for tgt in n.targets:
                                    if isinstance(tgt, ast.Name):
                                        fields.append(tgt.id)
                        # fields: self.<name> in __init__
                        for n in node.body:
                            if isinstance(n, ast.FunctionDef) and n.name == '__init__':
                                for sub in ast.walk(n):
                                    if isinstance(sub, ast.Assign):
                                        for tgt in sub.targets:
                                            if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == 'self':
                                                fields.append(tgt.attr)
                        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        entry = {'class': cls_name, 'fields': sorted(set(fields)), 'methods': methods}
                        py_index[cls_name] = entry
                        result['python'].append(entry)
            elif file.endswith('.java'):
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    src = f.read()
                try:
                    tree = javalang.parse.parse(src)
                except Exception:
                    continue
                # Classes and basic inheritance/interfaces
                for _, node in tree.filter(javalang.tree.ClassDeclaration):
                    name = node.name
                    java_class_names.add(name)
                    methods = [m.name for m in node.methods]
                    entry = {'class': name, 'fields': [], 'methods': methods}
                    java_index[name] = entry
                    result['java'].append(entry)
                    info = java_types.setdefault(name, {'extends': [], 'implements': [], 'uses': set()})
                    if node.extends:
                        try:
                            info['extends'].append(node.extends.name)
                        except Exception:
                            pass
                    if node.implements:
                        for impl in node.implements:
                            try:
                                info['implements'].append(impl.name)
                            except Exception:
                                pass
                # Fields with proper scoping to enclosing class
                for path, field in tree.filter(javalang.tree.FieldDeclaration):
                    try:
                        encl = next((p for p in reversed(path) if isinstance(p, javalang.tree.ClassDeclaration)), None)
                        if not encl:
                            continue
                        cls_name = encl.name
                        tname = getattr(field.type, 'name', None)
                        for decl in (field.declarators or []):
                            fname = getattr(decl, 'name', None)
                            if fname:
                                text = f"{fname}: {tname}" if tname else fname
                                java_index.get(cls_name, {}).get('fields', []).append(text)
                    except Exception:
                        continue
                # Method parameter types contribute to 'uses' for the enclosing class
                for path, method in tree.filter(javalang.tree.MethodDeclaration):
                    try:
                        encl = next((p for p in reversed(path) if isinstance(p, javalang.tree.ClassDeclaration)), None)
                        if not encl:
                            continue
                        cls_name = encl.name
                        for p in (method.parameters or []):
                            tname = getattr(getattr(p, 'type', None), 'name', None)
                            if tname:
                                java_types.setdefault(cls_name, {'extends': [], 'implements': [], 'uses': set()})['uses'].add(tname)
                    except Exception:
                        continue
                # Deduplicate collected fields for this file's classes
                for cls in list(java_index.keys()):
                    if java_index[cls].get('fields'):
                        java_index[cls]['fields'] = sorted(set(java_index[cls]['fields']))
            elif file.endswith('.cs'):
                # Heuristic C#: capture class and methods
                try:
                    with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                        src = f.read()
                    for m in re.finditer(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([A-Za-z0-9_\s,<>\.]+))?', src):
                        cls = m.group(1)
                        cs_class_names.add(cls)
                        bases_str = m.group(2) or ''
                        exts, impls = [], []
                        if bases_str:
                            parts = [p.strip() for p in bases_str.split(',') if p.strip()]
                            if parts:
                                exts = [_norm_type_name(parts[0])]
                                if len(parts) > 1:
                                    impls = [_norm_type_name(p) for p in parts[1:]]
                        if exts or impls:
                            cs_types[cls] = {'extends': exts, 'implements': impls}
                        body_methods = re.findall(r'\b(?:public|private|protected|internal|static|sealed|abstract|virtual|async|partial|new|override|unsafe|extern|ref|readonly|volatile|out|in)\s+[A-Za-z0-9_<>\[\],\s]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', src)
                        result['csharp'].append({'class': cls, 'fields': [], 'methods': sorted(set(body_methods))})
                except Exception:
                    # Fallback to filename
                    result['csharp'].append({'class': os.path.splitext(file)[0], 'fields': [], 'methods': []})
            elif file.endswith(('.js', '.jsx')):
                # Heuristic JavaScript classes (ES6)
                try:
                    with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                        src = f.read()
                    for m in re.finditer(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:extends\s+([A-Za-z_][A-Za-z0-9_\.]*))?', src):
                        cls = m.group(1)
                        js_class_names.add(cls)
                        base = m.group(2)
                        if base:
                            js_types[cls] = {'extends': [_norm_type_name(base)]}
                        # Methods inside class block (simple heuristic)
                        methods = sorted(set(re.findall(r'\n\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(', src)))
                        result['javascript'].append({'class': cls, 'fields': [], 'methods': methods})
                except Exception:
                    pass
            elif file.endswith(('.ts', '.tsx')):
                # Heuristic TypeScript classes
                try:
                    with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                        src = f.read()
                    for m in re.finditer(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:extends\s+([A-Za-z_][A-Za-z0-9_\.]*))?(?:\s+implements\s+([A-Za-z0-9_\s,<>\.]+))?', src):
                        cls = m.group(1)
                        ts_class_names.add(cls)
                        base = m.group(2)
                        impls_str = m.group(3) or ''
                        exts = [_norm_type_name(base)] if base else []
                        impls = []
                        if impls_str:
                            impls = [_norm_type_name(p) for p in impls_str.split(',') if p.strip()]
                        if exts or impls:
                            ts_types[cls] = {'extends': exts, 'implements': impls}
                        methods = sorted(set(re.findall(r'\n\s*(?:public|private|protected)?\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(', src)))
                        fields = sorted(set(re.findall(r'\n\s*(?:public|private|protected)?\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*[A-Za-z0-9_<>\[\],]+\s*;', src)))
                        result['typescript'].append({'class': cls, 'fields': fields, 'methods': methods})
                except Exception:
                    pass
            elif file.endswith(('.cpp', '.hpp', '.h', '.cc', '.cxx', '.hh', '.hxx')):
                # Heuristic C/C++ classes and structs
                try:
                    with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                        src = f.read()
                    # C++ classes/structs
                    for m in re.finditer(r'\b(class|struct)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([A-Za-z0-9_\s,<>:]+))?\s*[{]', src):
                        kind, cls, bases = m.group(1), m.group(2), (m.group(3) or '')
                        cpp_class_names.add(cls)
                        # Methods: look for returnType name( within file where class appears
                        methods = sorted(set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_:\-*&<>\[\]\s]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', src)))
                        (result['cpp'] if kind == 'class' else result['cpp']).append({'class': cls, 'fields': [], 'methods': methods})
                        if bases:
                            parts = [p.strip() for p in bases.split(',') if p.strip()]
                            cleaned = []
                            for p in parts:
                                # remove access specifiers and virtual keywords
                                tokens = [t for t in re.split(r'\s+', p) if t.lower() not in ('public', 'protected', 'private', 'virtual', 'final', 'override')]
                                if tokens:
                                    cleaned.append(_norm_type_name(tokens[-1]))
                            if cleaned:
                                cpp_types[cls] = {'extends': cleaned}
                    # C structs as pseudo-classes
                    for m in re.finditer(r'\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)\s*{', src):
                        result['c'].append({'class': m.group(1), 'fields': [], 'methods': []})
                except Exception:
                    pass
            elif file.endswith(('.html', '.htm')):
                # Track presence for meta/reporting (not rendered in UML)
                result['html'].append({'class': os.path.basename(full), 'fields': [], 'methods': []})
            elif file.endswith('.css'):
                result['css'].append({'class': os.path.basename(full), 'fields': [], 'methods': []})

    # Second pass: build relations for multiple languages
    relations = []
    for cls, info in java_types.items():
        for base in info.get('extends', []):
            relations.append({'from': base, 'to': cls, 'type': 'extends'})
        for iface in info.get('implements', []):
            relations.append({'from': iface, 'to': cls, 'type': 'implements'})
        for used in info.get('uses', set()):
            if used in java_class_names and used != cls:
                relations.append({'from': cls, 'to': used, 'type': 'uses'})
    # Python inheritance (extends)
    for cls, bases in py_bases.items():
        for base in bases:
            relations.append({'from': base, 'to': cls, 'type': 'extends'})

    # C# inheritance and implements
    for cls, info in cs_types.items():
        for base in info.get('extends', []):
            relations.append({'from': base, 'to': cls, 'type': 'extends'})
        for iface in info.get('implements', []):
            relations.append({'from': iface, 'to': cls, 'type': 'implements'})

    # JS extends
    for cls, info in js_types.items():
        for base in info.get('extends', []):
            relations.append({'from': base, 'to': cls, 'type': 'extends'})

    # TS extends/implements
    for cls, info in ts_types.items():
        for base in info.get('extends', []):
            relations.append({'from': base, 'to': cls, 'type': 'extends'})
        for iface in info.get('implements', []):
            relations.append({'from': iface, 'to': cls, 'type': 'implements'})

    # C++ base classes
    for cls, info in cpp_types.items():
        for base in info.get('extends', []):
            relations.append({'from': base, 'to': cls, 'type': 'extends'})

    result['relations'] = relations
    # attach scan meta
    try:
        # merge with any existing meta added by app layer
        meta = result.get('meta') or {}
        meta['files_scanned'] = files_scanned
        result['meta'] = meta
    except Exception:
        pass
    logging.info('AST summary prepared for LLM/enrichment')
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
        merged = { 'python': [], 'java': [], 'csharp': [], 'relations': [] }
        for lang in ['python', 'java', 'csharp']:
            ast_list = ast_obj.get(lang, []) or []
            ai_list = ai_obj.get(lang, []) or []
            by_name = {}
            for item in ast_list + ai_list:
                name = item.get('class')
                if not name:
                    continue
                cur = by_name.setdefault(name, {'class': name, 'fields': set(), 'methods': set()})
                for f in item.get('fields', []) or []:
                    cur['fields'].add(f)
                for m in item.get('methods', []) or []:
                    cur['methods'].add(m)
            merged[lang] = [
                {
                    'class': n,
                    'fields': sorted(list(v['fields'])),
                    'methods': sorted(list(v['methods']))
                }
                for n, v in by_name.items()
            ]
        # relations with provenance tags
        rels = []
        for r in ast_obj.get('relations', []) or []:
            if r and r.get('from') and r.get('to') and r.get('type'):
                rr = dict(r)
                rr['source'] = rr.get('source') or 'heuristic'
                rels.append(rr)
        for r in ai_obj.get('relations', []) or []:
            if r and r.get('from') and r.get('to') and r.get('type'):
                rr = dict(r)
                rr['source'] = rr.get('source') or 'ai'
                rels.append(rr)
        # dedupe
        seen = set()
        uniq = []
        for r in rels:
            key = (r.get('from'), r.get('to'), r.get('type'), r.get('source'))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(r)
        merged['relations'] = uniq
        return merged

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
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
