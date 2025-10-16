# Python Parser Microservice

🐍 **Multi-Language Code Analysis Engine with AI Enhancement**

The Python parser is the core analysis engine that extracts class structures, relationships, and metadata from source code repositories. It combines static AST analysis with optional AI enhancement to provide comprehensive UML diagram data.

## 🎯 Purpose & Architecture

### **Core Responsibilities**
- **Multi-Language AST Parsing**: Extract classes, fields, and methods from 7+ programming languages
- **Relationship Inference**: Detect inheritance, composition, and dependency relationships
- **AI Enhancement**: Optional LLM integration for improved analysis accuracy
- **Performance Optimization**: Efficient scanning with configurable limits and caching
- **Data Standardization**: Unified output schema for frontend consumption

### **Technology Stack**
- **Runtime**: Python 3.10+ with Flask framework
- **AST Parsing**: Built-in `ast` module for Python, `javalang` for Java
- **AI Integration**: Groq API (OpenAI-compatible) for enhanced analysis
- **File Processing**: Git operations, ZIP handling, and directory traversal
- **Caching**: In-memory caching for improved performance

## 🔍 Language Support & Capabilities

### **Supported Languages Matrix**

| Language | Parser | Classes | Fields | Methods | Inheritance | Interfaces | Dependencies |
|----------|--------|---------|--------|---------|-------------|------------|--------------|
| **Java** | javalang | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Python** | ast | ✅ | ✅ | ✅ | ✅ | ❌ | 🔄 |
| **C#** | regex | ✅ | 🔄 | ✅ | ✅ | ✅ | 🔄 |
| **TypeScript** | regex | ✅ | ✅ | ✅ | ✅ | ✅ | 🔄 |
| **JavaScript** | regex | ✅ | ✅ | ✅ | ✅ | ❌ | 🔄 |
| **C++** | regex | ✅ | 🔄 | ✅ | ✅ | ❌ | 🔄 |
| **C** | regex | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **HTML/CSS** | presence | 📊 | ❌ | ❌ | ❌ | ❌ | ❌ |

**Legend**: ✅ Fully Implemented | 🔄 Roadmap | ❌ Not Applicable | 📊 Metadata Only

### **Analysis Capabilities**

#### **Java Analysis** (Improved)
```python
# Extracts comprehensive information
{
  "class": "UserService",
  "fields": ["private userRepository: UserRepository", "private logger: Logger"],
  "methods": ["createUser", "findUser", "updateUser", "deleteUser"],
  "extends": ["BaseService"],
  "implements": ["UserOperations"],
  "uses": ["UserValidator", "EmailService"],
  "relations": [
    {"from":"UserService","to":"UserRepository","type":"composition","source":"heuristic"},
    {"from":"UserService","to":"Logger","type":"uses","source":"heuristic"}
  ]
}
```

#### **Python Analysis**
```python
# Focuses on class structure and methods
{
  "class": "DataProcessor",
  "fields": ["input_file: str", "output_format"],
  "methods": ["__init__", "process_data", "validate_input", "export_results"],
  "extends": ["BaseProcessor"]
}
```

#### **TypeScript Analysis**
```python
# Includes type information where available
{
  "class": "ApiClient",
  "fields": ["baseUrl: string", "timeout: number", "http: HttpClient"],
  "methods": ["get", "post", "put", "delete"],
  "extends": ["HttpClient"],
  "implements": ["IApiClient"]
}
```

#### **JavaScript Analysis**
```python
{
  "class": "Cart",
  "fields": ["items", "api: ApiClient"],
  "methods": ["add", "remove", "checkout"],
  "relations": [
    {"from":"Cart","to":"ApiClient","type":"composition","source":"heuristic"}
  ]
}
```

## 🔄 Data Processing Pipeline

### **Analysis Workflow**
```
Repository Input (URL/ZIP)
    ↓ Git Clone/Extract
File System Traversal
    ↓ Language Detection
Multi-Language AST Parsing
    ↓ Class/Method Extraction
Relationship Inference
    ↓ Schema Normalization
Unified JSON Schema
    ↓ AI Enhancement (Optional)
Enhanced Schema Output
    ↓ Response Generation
Final Analysis Results
```

### **File Processing Strategy**
```python
# Performance optimization approach
def process_repository(repo_path):
    skip_dirs = {'.git', 'node_modules', 'dist', 'build', 'target', 
                 'out', 'bin', 'obj', '__pycache__', '.tox', '.venv'}
    
    for root, dirs, files in os.walk(repo_path):
        # Prune heavy directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        # Skip symlinked directories/files
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        
        for file in files:
            if files_scanned >= MAX_FILES:
                break
                
            file_path = os.path.join(root, file)
            
            # Skip large files
            if os.path.getsize(file_path) > MAX_FILE_BYTES:
                continue
                
            # Process based on file extension
            process_file(file_path)
```

## 🤖 AI Enhancement System

### **AI Integration Architecture**
```python
# Dual-mode operation: Heuristic + AI
def analyze_with_ai(ast_data):
    # 1. Static heuristic analysis (always runs)
    heuristic_results = static_analysis(ast_data)
    
    # 2. AI enhancement (optional)
    if not STUB_LLM and GROQ_API_KEY:
        ai_results = call_groq_api(ast_data)
        merged_results = merge_schemas(heuristic_results, ai_results)
        return merged_results
    
    # 3. Fallback to heuristics only
    return heuristic_results
```

### **AI Prompt Engineering**
```python
PROMPT = '''You are a code analysis tool. From the provided AST summary, produce ONLY JSON (no markdown fences) matching exactly this schema:
{
    "python": [{"class": "Name", "fields": ["f1", "f2: Type"], "methods": ["m1", "m2"]}],
    "java":   [{"class": "Name", "fields": ["f1", "f2: Type"], "methods": ["m1", "m2"]}],
    "csharp": [{"class": "Name", "fields": ["f1", "f2: Type"], "methods": ["m1", "m2"]}],
    "relations": [{"from": "ClassA", "to": "ClassB", "type": "uses|extends|implements|aggregates|composes"}]
}
Methods should be names only (no parentheses). Only include classes actually present. If unsure about relations, return an empty array for "relations". Do not include any prose.'''
```

### **Schema Merging Strategy**
```python
def merge_schemas(ast_obj, ai_obj):
    """Intelligently merge heuristic and AI results"""
    merged = {'python': [], 'java': [], 'csharp': [], 'relations': []}
    
    for lang in ['python', 'java', 'csharp']:
        # Combine class information from both sources
        ast_classes = {cls['class']: cls for cls in ast_obj.get(lang, [])}
        ai_classes = {cls['class']: cls for cls in ai_obj.get(lang, [])}
        
        # Merge fields and methods
        for class_name in set(ast_classes.keys()) | set(ai_classes.keys()):
            merged_class = merge_class_data(
                ast_classes.get(class_name, {}),
                ai_classes.get(class_name, {})
            )
            merged[lang].append(merged_class)
    
    # Merge relationships with provenance tracking
    merged['relations'] = merge_relations(
        ast_obj.get('relations', []),
        ai_obj.get('relations', [])
    )
    
    return merged
```

## 📊 Output Schema & Data Format

### **Complete Schema Structure**
```json
{
  "python": [
    {
      "class": "ClassName",
      "fields": ["field1: type", "field2"],
      "methods": ["method1", "method2", "__init__"]
    }
  ],
  "java": [
    {
      "class": "ServiceClass", 
      "fields": ["private field: Type"],
      "methods": ["publicMethod", "privateMethod"]
    }
  ],
  "csharp": [...],
  "javascript": [...],
  "typescript": [...],
  "cpp": [...],
  "c": [...],
  "html": [
    {
      "class": "index.html",
      "fields": [],
      "methods": []
    }
  ],
  "css": [
    {
      "class": "styles.css", 
      "fields": [],
      "methods": []
    }
  ],
  "relations": [
    {
      "from": "BaseClass",
      "to": "DerivedClass",
      "type": "extends",
      "source": "heuristic"
    },
    {
      "from": "Service",
      "to": "Repository", 
      "type": "uses",
      "source": "ai"
    }
  ],
  "meta": {
    "commit": "abc123def456...",
    "files_scanned": 245,
    "timestamp": "2025-01-15T10:30:00Z",
    "processing_time_ms": 1250
  }
}
```

### **Relationship Types**
- **`extends`**: Class inheritance (A extends B)
- **`implements`**: Interface implementation (A implements B)
- **`uses`**: Dependency relationship (A uses B)
- **`aggregation`**: Weak ownership (A has B, B can exist independently)
- **`composition`**: Strong ownership (A owns B, B cannot exist without A)
- **`association`**: General association relationship

### **Source Provenance**
- **`heuristic`**: Detected by static code analysis
- **`ai`**: Detected by AI enhancement
- **`both`**: Confirmed by both methods (highest confidence)

## ⚙️ Configuration & Environment

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FILE_BYTES` | `500000` | Skip files larger than this (bytes) |
| `MAX_FILES` | `5000` | Maximum files to scan per repository |
| `GIT_CLONE_DEPTH` | `1` | Git clone depth (shallow clone) |
| `GROQ_API_KEY` | `None` | API key for Groq AI service |
| `GROQ_MODEL` | `meta-llama/llama-4-scout-17b-16e-instruct` | AI model to use |
| `GROQ_API_URL` | `https://api.groq.com/openai/v1/chat/completions` | AI API endpoint |
| `STUB_LLM` | `false` | Skip AI calls, return heuristics only |
| `FLASK_ENV` | `production` | Flask environment |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |

### **Performance Tuning**

#### **For Large Repositories**
```bash
# Increase limits cautiously
MAX_FILES=10000
MAX_FILE_BYTES=1000000
GIT_CLONE_DEPTH=1

# Monitor memory usage
# Larger limits = higher memory consumption
```

#### **For Fast Processing**
```bash
# Reduce limits for speed
MAX_FILES=1000
MAX_FILE_BYTES=100000
STUB_LLM=true  # Skip AI for fastest processing
```

#### **For Development**
```bash
# Balanced settings for development
MAX_FILES=2000
MAX_FILE_BYTES=500000
STUB_LLM=true
FLASK_ENV=development
FLASK_DEBUG=true
```

## 🚀 API Endpoints

### **POST /analyze**
Main analysis endpoint for repository processing.

#### **GitHub Repository Analysis**
```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "githubUrl": "https://github.com/username/repository"
  }'
```

#### **ZIP File Upload Analysis**
```bash
curl -X POST http://localhost:5000/analyze \
  -F "repoZip=@repository.zip"
```

#### **Response Format**
```json
{
  "schema": {
    "python": [...],
    "java": [...],
    "relations": [...],
    "meta": {
      "commit": "abc123...",
      "files_scanned": 245,
      "processing_time_ms": 1250,
      "languages_detected": ["python", "java", "javascript"],
      "ai_enhanced": true
    }
  }
}
```

#### **Error Response**
```json
{
  "error": "Git clone failed",
  "details": "Repository not found or access denied",
  "code": "CLONE_ERROR"
}
```

### **POST /uml-from-prompt**
Generate PlantUML or Mermaid diagrams directly from a natural-language description.

#### **Basic Usage**
```bash
curl -X POST http://localhost:5000/uml-from-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "User management system with admins and members",
    "diagramType": "class",
    "format": "plantuml"
  }'
```

#### **Optional Fields**
- `diagramType` – `class | sequence | usecase | state | activity` (default: `class`)
- `format` – `plantuml | mermaid` (default: `plantuml`)
- `context` – object with extra background details (e.g., `{ "domain": "SaaS" }`)
- `stylePreferences` – object with theme/layout hints to feed the LLM
- `focus` – array or comma-delimited string of emphasis areas (e.g., security, scalability)

#### **Response Format**
```json
{
  "diagram": "@startuml\nclass User {\n  +id: UUID\n}\n@enduml",
  "diagram_type": "class",
  "format": "plantuml",
  "source": "stub",
  "warnings": ["LLM call skipped because STUB_LLM is enabled."]
}
```

When the Groq API is unavailable or `STUB_LLM=true`, the service returns a deterministic stub diagram so the UI can continue to render preview output.

## 🧪 Testing & Quality Assurance

### **Test Structure**
```
__tests__/
├── test_analyze.py        # Main analysis function tests
├── fixtures/              # Test repositories and data
│   ├── sample_java/       # Java test project
│   ├── sample_python/     # Python test project
│   └── sample_mixed/      # Multi-language project
└── test_data/             # Expected outputs and schemas
    ├── java_expected.json
    ├── python_expected.json
    └── relations_expected.json
```

### **Running Tests**
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest -v

# Current suite count
# 19 tests covering Python, TypeScript/JavaScript, Java relations, endpoints, and prompt-driven diagrams

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_analyze.py -v

# Run tests for specific language
pytest -k "test_java" -v
```

### **Example Test Case**
```python
# test_analyze.py
import pytest
from analyze import analyze_repo

def test_java_class_extraction():
    """Test Java class and method extraction"""
    result = analyze_repo('fixtures/sample_java')
    
    # Verify basic structure
    assert 'java' in result
    assert len(result['java']) > 0
    
    # Find specific class
    user_service = next(
        (cls for cls in result['java'] if cls['class'] == 'UserService'),
        None
    )
    
    assert user_service is not None
    assert 'createUser' in user_service['methods']
    assert 'findUser' in user_service['methods']
    
    # Verify relationships
    extends_relations = [
        r for r in result['relations'] 
        if r['type'] == 'extends' and r['to'] == 'UserService'
    ]
    assert len(extends_relations) >= 0

def test_ai_enhancement():
    """Test AI enhancement functionality"""
    # Test with AI enabled
    os.environ['STUB_LLM'] = 'false'
    os.environ['GROQ_API_KEY'] = 'test-key'
    
    result_with_ai = analyze_repo('fixtures/sample_python')
    
    # Test without AI
    os.environ['STUB_LLM'] = 'true'
    result_without_ai = analyze_repo('fixtures/sample_python')
    
    # AI should potentially add more relationships
    ai_relations = len(result_with_ai.get('relations', []))
    heuristic_relations = len(result_without_ai.get('relations', []))
    
    # AI might find additional relationships
    assert ai_relations >= heuristic_relations
```

## 🔧 Development & Debugging

### **Local Development Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black isort flake8

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=true
export STUB_LLM=true

# Start development server
python app.py
```

### **Code Quality Tools**
```bash
# Code formatting
black analyze.py app.py

# Import sorting
isort analyze.py app.py

# Linting
flake8 analyze.py app.py

# Type checking (if using type hints)
mypy analyze.py app.py
```

### **Debugging Techniques**

#### **Enable Detailed Logging**
```python
import logging

# Configure logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def analyze_repo(repo_path):
    logger.info(f"Starting analysis of {repo_path}")
    logger.debug(f"MAX_FILES: {MAX_FILES}, MAX_FILE_BYTES: {MAX_FILE_BYTES}")
    
    # ... analysis code ...
    
    logger.info(f"Analysis complete. Found {len(result['python'])} Python classes")
    return result
```

#### **Performance Profiling**
```python
import time
import cProfile

def profile_analysis(repo_path):
    """Profile the analysis performance"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    result = analyze_repo(repo_path)
    end_time = time.time()
    
    profiler.disable()
    profiler.dump_stats('analysis_profile.prof')
    
    print(f"Analysis took {end_time - start_time:.2f} seconds")
    print(f"Files scanned: {result.get('meta', {}).get('files_scanned', 0)}")
    
    return result
```

## 🐛 Troubleshooting

### **Common Issues & Solutions**

#### **Git Clone Failures**
```python
# Issue: Repository access denied or not found
# Solution: Verify URL format and repository accessibility

# Debug git operations
def debug_git_clone(github_url, repo_path):
    import subprocess
    
    try:
        cmd = ['git', 'clone', '--depth', '1', github_url, repo_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        
        if result.returncode != 0:
            print(f"Git clone failed: {result.stderr}")
            print(f"Command: {' '.join(cmd)}")
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Git clone timed out")
        return False
```

#### **Memory Issues with Large Repositories**
```python
# Issue: Out of memory errors
# Solution: Reduce MAX_FILES and MAX_FILE_BYTES

# Monitor memory usage
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.2f} MB")
    
    if memory_mb > 500:  # Warn if over 500MB
        print("WARNING: High memory usage detected")
```

#### **AI API Issues**
```python
# Issue: AI API failures or timeouts
# Solution: Implement retry logic and fallbacks

def safe_ai_call(ast_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            return call_gemini(ast_data)
        except requests.exceptions.Timeout:
            print(f"AI API timeout, attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            print(f"AI API error: {e}")
            break
    
    # Fallback to heuristics only
    print("Falling back to heuristic analysis")
    return {'schema': ast_data}
```

#### **Language Parser Failures**
```python
# Issue: Syntax errors in parsed files
# Solution: Graceful error handling per file

def safe_parse_file(file_path, parser_func):
    try:
        return parser_func(file_path)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Parser error in {file_path}: {e}")
        return None
```

## 🔄 Integration & Deployment

### **Docker Deployment**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Start application
CMD ["python", "app.py"]
```

### **Production Configuration**
```bash
# Production environment variables
FLASK_ENV=production
FLASK_DEBUG=false
MAX_FILES=5000
MAX_FILE_BYTES=500000
GROQ_API_KEY=your_production_key
STUB_LLM=false

# Security considerations
GIT_LFS_SKIP_SMUDGE=1
GIT_TERMINAL_PROMPT=0
```

### **Monitoring & Observability**
```python
# Add metrics collection
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
request_count = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('request_duration_seconds', 'Request duration')
analysis_files = Histogram('analysis_files_count', 'Files analyzed per request')

@app.route('/metrics')
def metrics():
    return generate_latest()

# Usage in analysis
with request_duration.time():
    result = analyze_repo(repo_path)
    analysis_files.observe(result.get('meta', {}).get('files_scanned', 0))
```

---

**Made with 🐍 for comprehensive code analysis**

*This Python parser provides the foundation for accurate, scalable UML diagram generation with AI-enhanced insights.*
