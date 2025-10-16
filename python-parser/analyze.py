import os
import logging
import json
from typing import Dict, Any, Optional, List

try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover - fallback for environments without python-dotenv
    def load_dotenv(*_args, **_kwargs):
        return False

# Import new modular architecture
from analyzers import AnalyzerFactory
from relationship import RelationshipDetector
from utils import FileUtils
from constants import EXTENSION_TO_LANGUAGE
from utils.groq_client import (
    GroqClient,
    GroqClientDisabledError,
    GroqClientError,
)

load_dotenv()


"""
analyze.py - Refactored with Modular Architecture
This module provides the main API for code analysis, now using a modular architecture:

- analyzers/ : Language-specific analyzers (Python, Java, C#, TypeScript, C++)
- relationship/ : Centralized relationship detection and validation
- ai/ : LLM-powered code analysis enhancements (optional)
- utils/ : File operations and Git utilities

This maintains backward compatibility with the original analyze_repo() API.
"""

# Return stubbed schema when true (for offline testing)
STUB_LLM = os.getenv('STUB_LLM', 'false').lower() in ('1', 'true', 'yes')

# Enable AI enhancement if OpenAI API key is available
ENABLE_AI_ENHANCEMENT = bool(os.getenv('OPENAI_API_KEY'))
if ENABLE_AI_ENHANCEMENT:
    try:
        from ai import AIEnhancer
        logging.info("AI enhancement enabled with OpenAI API")
    except ImportError:
        ENABLE_AI_ENHANCEMENT = False
        logging.warning("AI enhancement disabled (openai package not installed)")
else:
    logging.info("AI enhancement disabled (no OPENAI_API_KEY found)")


def _analyze_file_worker(args):
    """
    Worker function for parallel file analysis.
    Must be at module level to be picklable for multiprocessing.
    """
    file_path, repo_path = args
    try:
        from analyzers import AnalyzerFactory
        from utils import FileUtils

        factory = AnalyzerFactory()
        analyzer = factory.get_analyzer(file_path)
        if not analyzer:
            return None
        package_path = FileUtils.get_package_path(file_path, repo_path)
        classes = analyzer.analyze_file(file_path, package_path)
        lang_key = analyzer.get_language_name()
        # Also collect relationships from this analyzer
        relationships = analyzer.relationships + analyzer.compositions + analyzer.usages
        return (lang_key, classes, relationships)
    except Exception as e:
        logging.warning(f"Failed to analyze {file_path}: {e}")
        return None

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
    "endpoints": [{"method": "GET", "path": "/resource", "controller": "ControllerName", "layer": "presentation|business|data", "returns": "ResponseType", "description": "Purpose"}],
    "usecases": [{"name": "Use Case", "actor": "Primary Actor", "supportingActors": ["Secondary"], "goal": "Business outcome", "system": "System/Subsystem", "includes": ["Another Use Case"], "extends": ["Extended Use Case"], "summary": "Key steps"}],
    "sequence_flows": [{"from": "Actor/System", "to": "Component", "message": "Action", "response": "Result", "type": "sync|async", "note": "Important detail"}],
    "activity": [{"step": "Action", "role": "Role", "class": "ClassName", "next": ["Next Step"], "condition": "Guard/Decision"}],
    "states": [{"context": "ClassOrAggregate", "states": ["State1", "State2"], "transitions": [{"from": "State1", "to": "State2", "trigger": "Event"}]}],
    "patterns": [{"type": "singleton|factory|observer|strategy|decorator", "classes": ["Class1", "Class2"]}],
    "layers": [{"name": "presentation|business|data", "classes": ["Class1", "Class2"]}],
    "meta": {"system": "SystemName", "assumptions": ["Item"], "notes": ["Important observation"]}
}

INSTRUCTIONS:
1. If given a natural language prompt, infer classes, fields, methods, relationships, and behaviors as if designing the system from scratch. Use professional naming and architecture.
2. Always include ALL classes described or implied, even if they appear peripheral.
3. Fields must include type information when available (e.g., "name: String", "age: int").
4. Methods should be plain method names only (no parentheses or parameters).
5. Stereotypes: use "interface" for interfaces, "abstract" for abstract classes, "class" for concrete classes; mark "abstract": true when appropriate.
6. Relations: use "extends" for inheritance, "implements" for interface implementation, "composition" for strong ownership, "aggregation" for weak ownership, "uses" for method-level collaborations, "dependency" for imports/references, and "association" as the safest fallback.
7. Populate "endpoints" for each HTTP/API/service interface. Include method, path/topic, owning controller/service, architectural layer, return type, and short description.
8. Populate "usecases" with actor-driven goals. Provide actor (or actors), goal, system/boundary, and any includes/extends relationships. Summaries should reflect key happy-path behavior.
9. Populate "sequence_flows" describing runtime interactions from a primary scenario. Include from/to participants, message, optional response, whether the call is sync/async, and an explanatory note when useful.
10. Populate "activity" with ordered steps or decision points. Each item should include a step label, role or component handling it, optional implementation class, and the next step(s) with guard conditions.
11. Populate "states" for any entity or aggregate that exhibits a lifecycle. Provide the state names and transitions with triggers or events.
12. Add "patterns" array for detected design patterns (e.g., singleton, factory, observer) with the participating classes.
13. Add "layers" array for architectural layering (presentation/controllers/views, business/services/managers, data/models/repositories).
14. Provide "meta" details including the inferred system name plus assumptions or constraints you relied on to complete the diagram.
15. Cross-language relationships should be captured when components interact across technology boundaries.
16. Do not include any prose, explanations, or markdown fences—return ONLY valid JSON.
17. Think step-by-step like a senior software architect to ensure completeness and internal consistency.

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
    ],
    "endpoints": [
        {"method": "POST", "path": "/loans", "controller": "LoanController", "layer": "presentation", "returns": "Loan", "description": "Create a new loan"}
    ],
    "usecases": [
        {"name": "Borrow Book", "actor": "Member", "goal": "Check out a book", "system": "LibrarySystem", "includes": ["Validate Membership"], "extends": []}
    ],
    "sequence_flows": [
        {"from": "Member", "to": "LoanController", "message": "borrow(bookId)", "response": "Loan created", "type": "sync"}
    ],
    "activity": [
        {"step": "Select book", "role": "Member", "next": ["Submit loan request"]},
        {"step": "Submit loan request", "role": "Member", "next": ["Validate membership"]}
    ],
    "states": [
        {"context": "Loan", "states": ["Requested", "Active", "Returned"], "transitions": [{"from": "Requested", "to": "Active", "trigger": "Approval"}]}
    ]
}

Prompt: "An e-commerce platform with products, customers, orders, and payment processing."
Output:
{
    "python": [
        {"class": "Product", "fields": ["name: String", "price: Float", "sku: String"], "methods": ["updateStock"], "stereotype": "class", "abstract": false, "package": "shop"},
        {"class": "Customer", "fields": ["name: String", "email: String"], "methods": ["placeOrder"], "stereotype": "class", "abstract": false, "package": "shop"},
        {"class": "Order", "fields": ["customer: Customer", "items: List[OrderItem]", "total: Decimal"], "methods": ["addItem", "checkout"], "stereotype": "class", "abstract": false, "package": "shop"},
        {"class": "PaymentProcessor", "fields": ["provider: String"], "methods": ["processPayment"], "stereotype": "class", "abstract": false, "package": "shop"}
    ],
    "relations": [
        {"from": "Order", "to": "Product", "type": "aggregation", "source": "ai"},
        {"from": "Order", "to": "Customer", "type": "association", "source": "ai"},
        {"from": "Order", "to": "PaymentProcessor", "type": "uses", "source": "ai"}
    ],
    "endpoints": [
        {"method": "POST", "path": "/orders", "controller": "OrderController", "layer": "presentation", "returns": "Order", "description": "Create a new order"},
        {"method": "POST", "path": "/payments", "controller": "PaymentController", "layer": "business", "returns": "PaymentResult", "description": "Capture payment"}
    ],
    "usecases": [
        {"name": "Place Order", "actor": "Customer", "goal": "Purchase products", "system": "ECommercePlatform", "includes": ["Process Payment"], "extends": []}
    ],
    "sequence_flows": [
        {"from": "Customer", "to": "OrderController", "message": "checkout(cart)", "response": "OrderConfirmation", "type": "sync", "note": "Validates inventory before payment"}
    ],
    "activity": [
        {"step": "Browse catalog", "role": "Customer", "next": ["Add item to cart"]},
        {"step": "Add item to cart", "role": "Customer", "next": ["Checkout"]}
    ],
    "states": [
        {"context": "Order", "states": ["Draft", "PendingPayment", "Paid", "Shipped"], "transitions": [{"from": "PendingPayment", "to": "Paid", "trigger": "PaymentSuccess"}]}
    ]
}
'''


GROQ_CLIENT = GroqClient()


def _safe_extract_json(text: str):
    """
    Safely extract JSON from LLM response text.
    Handles markdown code fences and raw JSON.
    
    Args:
        text: Raw text response from LLM
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
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


def analyze_repo(repo_path: str, limits: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze a repository using the new modular architecture.
    
    This function maintains backward compatibility with the original API while using
    the refactored modular architecture underneath.
    
    Args:
        repo_path: Path to the repository to analyze
        limits: Dictionary with max_files, max_bytes, etc. for security
        
    Returns:
        Dictionary with analysis results in standard schema format
    """
    if limits is None:
        from security import validate_environment_limits
        limits = validate_environment_limits()
    
    logging.info(f"Analyzing repository: {repo_path}")
    logging.info(f"Using limits: {limits}")
    
    # Initialize result structure
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
    
    # Initialize factory and detector
    factory = AnalyzerFactory()
    detector = RelationshipDetector()
    
    # Track all classes for relationship validation
    all_classes = set()
    class_by_lang = {}  # lang -> {class_name: class_dict}
    
    # Find all source files
    max_files = limits.get('max_files', 20000)
    max_bytes = limits.get('max_bytes', 2_000_000)
    
    source_files = FileUtils.find_source_files(
        repo_path,
        supported_extensions=list(EXTENSION_TO_LANGUAGE.keys()),
        max_files=max_files,
        max_file_size=max_bytes
    )
    
    files_scanned = 0
    logging.info(f"Found {len(source_files)} source files to analyze")
    
    # Group files by language for statistics
    files_by_lang = FileUtils.group_files_by_language(source_files, EXTENSION_TO_LANGUAGE)
    for lang, files in files_by_lang.items():
        logging.info(f"  {lang}: {len(files)} files")
    

    import concurrent.futures

    with concurrent.futures.ProcessPoolExecutor() as executor:
        file_args = [(file_path, repo_path) for file_path in source_files[:max_files]]
        future_to_file = {executor.submit(_analyze_file_worker, arg): arg[0] for arg in file_args}
        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result_tuple = future.result()
                if not result_tuple:
                    continue
                lang_key, classes, relationships = result_tuple
                if not classes:
                    continue
                files_scanned += 1
                if lang_key not in result:
                    result[lang_key] = []
                result[lang_key].extend(classes)
                if lang_key not in class_by_lang:
                    class_by_lang[lang_key] = {}
                for cls in classes:
                    class_name = cls.get('class')
                    if class_name:
                        all_classes.add(class_name)
                        class_by_lang[lang_key][class_name] = cls
                # Add relationships from this file's analysis
                result['relations'].extend(relationships)
            except Exception as e:
                logging.warning(f"Exception in parallel file analysis for {file_path}: {e}")
                continue

    logging.info(f"Analyzed {files_scanned} files, found {len(all_classes)} classes")

    # Combine classes for relationship detector
    combined_classes: List[Dict[str, Any]] = []
    for lang_key in ['python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c']:
        combined_classes.extend(result.get(lang_key, []) or [])

    # Add detected relationships and endpoints from analyzers
    analyzer_relationships = factory.detect_all_relationships(combined_classes)
    if analyzer_relationships:
        result['relations'].extend(analyzer_relationships)

    endpoint_data = factory.extract_all_endpoints(source_files)
    if endpoint_data:
        normalized_endpoints: List[Dict[str, Any]] = []
        for endpoint in endpoint_data:
            methods = endpoint.get('methods')
            if methods:
                for method in methods:
                    entry = dict(endpoint)
                    entry['method'] = method
                    entry.pop('methods', None)
                    normalized_endpoints.append(entry)
            else:
                normalized_endpoints.append(endpoint)
        result['endpoints'].extend(normalized_endpoints)

    detector.set_classes(combined_classes)
    detector.add_relationships(result['relations'])

    # Validate and deduplicate relationships
    logging.info(f"Processing {len(result['relations'])} raw relationships")
    validated_relations = detector.validate_relationships()
    deduped_relations = detector.deduplicate_relationships(validated_relations)
    for rel in deduped_relations:
        rel.setdefault('source', 'heuristic')
    detector.relationships = deduped_relations
    result['relations'] = deduped_relations
    logging.info(f"After validation: {len(result['relations'])} relationships")

    # Infer additional relationships using detector heuristics
    inferred = detector.infer_additional_relationships(combined_classes)
    if inferred:
        logging.info(f"Inferred {len(inferred)} relationships from heuristics")
        detector.add_relationships(inferred)
        deduped = detector.deduplicate_relationships(detector.relationships)
        for rel in deduped:
            rel.setdefault('source', 'heuristic')
        detector.relationships = deduped
        result['relations'] = deduped
    
    # Detect circular dependencies
    circular_deps = detector.detect_circular_dependencies()
    if circular_deps:
        logging.warning(f"Found {len(circular_deps)} circular dependency chains")
        # Add to metadata for visibility
        result.setdefault('meta', {})['circular_dependencies'] = circular_deps

    # Categorize relationships by type and strength
    relationship_stats = detector.categorize_relationships(result['relations'])
    result.setdefault('meta', {})['relationship_stats'] = relationship_stats
    
    # Optional: AI enhancement if enabled
    if ENABLE_AI_ENHANCEMENT:
        try:
            enhancer = AIEnhancer()
            
            # Enhance relationships with AI
            logging.info("Enhancing relationships with AI...")
            ai_relationships = enhancer.enhance_relationships(class_by_lang, result['relations'])
            if ai_relationships:
                # Filter high-confidence AI relationships
                high_conf_rels = [r for r in ai_relationships if r.get('confidence', 0) >= 0.7]
                if high_conf_rels:
                    logging.info(f"Adding {len(high_conf_rels)} high-confidence AI relationships")
                    result['relations'].extend(high_conf_rels)
                    result['relations'] = detector.deduplicate_relationships(result['relations'])
            
            # Detect design patterns
            logging.info("Detecting design patterns...")
            patterns = enhancer.detect_design_patterns(class_by_lang, result['relations'])
            if patterns:
                result['patterns'] = patterns
                logging.info(f"Detected {len(patterns)} design patterns")
            
            # Analyze architecture
            logging.info("Analyzing architecture...")
            arch_analysis = enhancer.analyze_architecture(class_by_lang, result['relations'])
            if arch_analysis:
                result.setdefault('meta', {})['architecture'] = arch_analysis
                
        except Exception as e:
            logging.warning(f"AI enhancement failed: {e}")
    
    # Add metadata
    result['meta'] = result.get('meta', {})
    result['meta'].update({
        'files_scanned': files_scanned,
        'classes_found': len(all_classes),
        'languages': list(files_by_lang.keys()),
        'system': os.path.basename(repo_path)
    })
    
    # Get factory statistics
    try:
        factory_stats = factory.get_analyzer_stats()
    except AttributeError:
        factory_stats = {}
    result['meta']['analyzer_stats'] = factory_stats
    
    logging.info(f"Analysis complete: {len(all_classes)} classes, {len(result['relations'])} relationships")
    
    return result


def call_gemini(ast_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Groq LLM API to enhance analysis results.
    
    This function sends the AST analysis to the LLM for enhancement and merges
    the results with the original analysis.
    
    Args:
        ast_json: Analysis results from analyze_repo()
        
    Returns:
        Dictionary with 'schema' key containing merged results, or 'error' key on failure
    """
    if STUB_LLM:
        logging.warning('STUB_LLM enabled: returning AST JSON as schema without calling an LLM.')
        return {'schema': ast_json}

    model = os.getenv('GROQ_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')

    if not GROQ_CLIENT.enabled or not GROQ_CLIENT.api_key:
        logging.warning('Groq client disabled or missing API key, returning AST results without LLM enhancement')
        return {'schema': ast_json}

    prompt_text = f"{PROMPT}\n\n{json.dumps(ast_json, ensure_ascii=False)}"
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You are an expert code analysis tool. Return ONLY valid JSON. Do not include code fences.'},
            {'role': 'user', 'content': prompt_text}
        ],
        'temperature': 0.2
    }

    try:
        data = GROQ_CLIENT.call(payload)
    except GroqClientDisabledError as err:
        logging.warning('Groq client currently disabled: %s', err)
        return {'schema': ast_json}
    except GroqClientError as err:
        logging.error('Groq API call failed: %s', err)
        return {'error': str(err)}

    def merge_schemas(ast_obj: dict, ai_obj: dict) -> dict:
        """
        Merge AST analysis with AI-enhanced results.
        Preserves all AST data and adds AI-inferred information.
        """
        merged = {
            'python': [], 'java': [], 'csharp': [],
            'javascript': [], 'typescript': [], 'cpp': [], 'c': [],
            'relations': [],
            'endpoints': [],
            'usecases': [],
            'sequence_flows': [],
            'activity': [],
            'states': [],
            'patterns': [],
            'layers': [],
            'meta': {}
        }

        def _dedupe_list(items: List[Any], key_func=None) -> List[Any]:
            unique: List[Any] = []
            seen = set()
            for item in items:
                if item is None:
                    continue
                key = None
                if key_func:
                    try:
                        key = key_func(item)
                    except Exception:
                        key = json.dumps(item, sort_keys=True, default=str)
                else:
                    key = json.dumps(item, sort_keys=True, default=str)
                if key not in seen:
                    seen.add(key)
                    unique.append(item)
            return unique

        def _collect_items(source: Dict[str, Any], keys: List[str]) -> List[Any]:
            values: List[Any] = []
            for key in keys:
                raw = source.get(key)
                if isinstance(raw, list):
                    values.extend(raw)
            return values
        
        all_ast_class_names = set()
        all_ai_class_names = set()
        
        # Merge classes by language
        for lang in ['python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c']:
            ast_list = ast_obj.get(lang, []) or []
            ai_list = ai_obj.get(lang, []) or []
            by_name = {}
            
            # Add AST classes
            for item in ast_list:
                name = item.get('class')
                if not name:
                    continue
                all_ast_class_names.add(name)
                cur = by_name.setdefault(name, {
                    'class': name,
                    'fields': set(),
                    'methods': set(),
                    'stereotype': None,
                    'abstract': False,
                    'package': None
                })
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
            
            # Merge AI classes
            for item in ai_list:
                name = item.get('class')
                if not name:
                    continue
                all_ai_class_names.add(name)
                
                # Create or get existing class
                if name not in by_name:
                    cur = by_name.setdefault(name, {
                        'class': name,
                        'fields': set(),
                        'methods': set(),
                        'stereotype': None,
                        'abstract': False,
                        'package': None
                    })
                else:
                    cur = by_name[name]
                
                # Merge fields and methods
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
            
            # Convert to final format
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
        
        # Merge relationships with provenance tags
        rels = []
        ast_relations = ast_obj.get('relations', []) or []
        ai_relations = ai_obj.get('relations', []) or []
        all_class_names = all_ast_class_names | all_ai_class_names
        
        # Add AST relationships
        for r in ast_relations:
            if r and r.get('from') and r.get('to') and r.get('type'):
                rr = dict(r)
                rr['source'] = rr.get('source') or 'heuristic'
                rels.append(rr)
        
        # Add AI relationships (only if both classes exist)
        for r in ai_relations:
            if r and r.get('from') and r.get('to') and r.get('type'):
                if r['from'] in all_class_names and r['to'] in all_class_names:
                    rr = dict(r)
                    rr['source'] = rr.get('source') or 'ai'
                    rels.append(rr)
        
        # Deduplicate relationships
        seen = set()
        uniq = []
        for r in rels:
            key = (r.get('from'), r.get('to'), r.get('type'), r.get('source'))
            if key not in seen:
                seen.add(key)
                uniq.append(r)
        merged['relations'] = uniq
        
        # Pass-through other data from AST
        merged['endpoints'] = _dedupe_list(
            _collect_items(ast_obj, ['endpoints']) + _collect_items(ai_obj, ['endpoints']),
            lambda item: (
                (item or {}).get('method'),
                (item or {}).get('path'),
                (item or {}).get('controller') or (item or {}).get('class')
            )
        )

        merged['usecases'] = _dedupe_list(
            _collect_items(ast_obj, ['usecases']) + _collect_items(ai_obj, ['usecases']),
            lambda item: (
                (item or {}).get('name') or (item or {}).get('action'),
                (item or {}).get('actor') or (item or {}).get('actors'),
                (item or {}).get('goal')
            )
        )

        merged['sequence_flows'] = _dedupe_list(
            _collect_items(ast_obj, ['sequence_flows', 'sequenceFlows']) +
            _collect_items(ai_obj, ['sequence_flows', 'sequenceFlows']),
            lambda item: (
                (item or {}).get('from') or (item or {}).get('initiator'),
                (item or {}).get('to') or (item or {}).get('receiver'),
                (item or {}).get('message') or (item or {}).get('action')
            )
        )

        merged['activity'] = _dedupe_list(
            _collect_items(ast_obj, ['activity', 'activity_flows']) +
            _collect_items(ai_obj, ['activity', 'activity_flows']),
            lambda item: (item or {}).get('step') or (item or {}).get('name')
        )

        merged['states'] = _dedupe_list(
            _collect_items(ast_obj, ['states']) + _collect_items(ai_obj, ['states']),
            lambda item: (item or {}).get('context') or (item or {}).get('class')
        )

        merged['patterns'] = _dedupe_list(
            _collect_items(ast_obj, ['patterns']) + _collect_items(ai_obj, ['patterns']),
            lambda item: ((item or {}).get('type'), tuple((item or {}).get('classes') or []))
        )

        merged['layers'] = _dedupe_list(
            _collect_items(ast_obj, ['layers']) + _collect_items(ai_obj, ['layers']),
            lambda item: ((item or {}).get('name'), tuple((item or {}).get('classes') or []))
        )

        merged['meta'] = {}
        for source in [ast_obj.get('meta') or {}, ai_obj.get('meta') or {}]:
            if not isinstance(source, dict):
                continue
            for key, value in source.items():
                if isinstance(value, list):
                    existing = merged['meta'].setdefault(key, [])
                    if isinstance(existing, list):
                        merged['meta'][key] = _dedupe_list(existing + value)
                    else:
                        merged['meta'][key] = value
                elif isinstance(value, dict):
                    existing_dict = merged['meta'].setdefault(key, {})
                    if isinstance(existing_dict, dict):
                        existing_dict.update(value)
                    else:
                        merged['meta'][key] = value
                else:
                    merged['meta'][key] = value

        for k in ['html', 'css']:
            if isinstance(ast_obj.get(k), list):
                merged[k] = list(ast_obj.get(k, []))
            elif isinstance(ast_obj.get(k), dict):
                merged[k] = dict(ast_obj.get(k, {}))

        if isinstance(ai_obj.get('html'), list):
            merged.setdefault('html', [])
            merged['html'].extend(ai_obj.get('html', []))
            merged['html'] = _dedupe_list(merged['html'])

        if isinstance(ai_obj.get('css'), list):
            merged.setdefault('css', [])
            merged['css'].extend(ai_obj.get('css', []))
            merged['css'] = _dedupe_list(merged['css'])
        
        return merged

    try:
        text = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        logging.info(f"Received LLM response ({len(text)} chars)")

        parsed = _safe_extract_json(text)
        if isinstance(parsed, dict):
            try:
                merged = merge_schemas(ast_json, parsed)
                logging.info("Successfully merged AST and AI results")
            except Exception as e:
                logging.warning(f"Schema merge failed, using AI result: {e}")
                merged = parsed
            return {'schema': merged}
        else:
            logging.warning("Failed to parse LLM response as JSON, returning AST results")
            return {'schema': ast_json}

    except Exception as e:
        logging.error(f'Groq response handling failed: {e}')
        return {'error': str(e)}
