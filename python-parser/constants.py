"""
Python Parser Constants
Centralized configuration for the Python parser service
"""

import os

# File Processing Limits
FILE_LIMITS = {
    'MAX_FILE_BYTES': int(os.getenv('MAX_FILE_BYTES', '500000')),  # 500 KB
    'MAX_FILES': int(os.getenv('MAX_FILES', '5000')),
    'MAX_LINE_LENGTH': 10000,
    'MAX_FILE_LINES': 50000,
}

# Git Configuration
GIT_CONFIG = {
    'CLONE_DEPTH': int(os.getenv('GIT_CLONE_DEPTH', '1')),
    'TIMEOUT': int(os.getenv('GIT_TIMEOUT', '300')),  # 5 minutes
    'SKIP_LFS': True,
    'NO_CHECKOUT': False,
}

# AI/LLM Configuration
AI_CONFIG = {
    'STUB_LLM': os.getenv('STUB_LLM', 'false').lower() in ('1', 'true', 'yes'),
    'GROQ_API_KEY': os.getenv('GROQ_API_KEY', ''),
    'GROQ_MODEL': os.getenv('GROQ_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct'),
    'GROQ_API_URL': os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions'),
    'MAX_TOKENS': 8000,
    'TEMPERATURE': 0.1,
    'TIMEOUT': 60,
}

# Supported Languages
LANGUAGES = {
    'PYTHON': 'python',
    'JAVA': 'java',
    'CSHARP': 'csharp',
    'JAVASCRIPT': 'javascript',
    'TYPESCRIPT': 'typescript',
    'CPP': 'cpp',
    'C': 'c',
    'HTML': 'html',
    'CSS': 'css',
}

# File Extension to Language Mapping
EXTENSION_TO_LANGUAGE = {
    '.py': LANGUAGES['PYTHON'],
    '.java': LANGUAGES['JAVA'],
    '.cs': LANGUAGES['CSHARP'],
    '.js': LANGUAGES['JAVASCRIPT'],
    '.ts': LANGUAGES['TYPESCRIPT'],
    '.cpp': LANGUAGES['CPP'],
    '.cc': LANGUAGES['CPP'],
    '.cxx': LANGUAGES['CPP'],
    '.hpp': LANGUAGES['CPP'],
    '.c': LANGUAGES['C'],
    '.h': LANGUAGES['C'],  # Ambiguous, could be C or C++
    '.html': LANGUAGES['HTML'],
    '.htm': LANGUAGES['HTML'],
    '.css': LANGUAGES['CSS'],
}

# Directories to Skip (performance optimization)
SKIP_DIRECTORIES = {
    'node_modules',
    '__pycache__',
    '.git',
    '.svn',
    '.hg',
    'venv',
    'env',
    '.env',
    '.venv',
    'virtualenv',
    'dist',
    'build',
    'target',
    'bin',
    'obj',
    'out',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    'coverage',
    'htmlcov',
    '.idea',
    '.vscode',
    '.vs',
    '__MACOSX',
    '.DS_Store',
    'bower_components',
    'jspm_packages',
    'web_modules',
    '.cache',
    '.parcel-cache',
    '.next',
    '.nuxt',
    '.docusaurus',
}

# File Patterns to Skip
SKIP_FILE_PATTERNS = {
    '*.min.js',
    '*.min.css',
    '*.map',
    '*.lock',
    'package-lock.json',
    'yarn.lock',
    'Pipfile.lock',
    'poetry.lock',
    '*.pyc',
    '*.pyo',
    '*.so',
    '*.dll',
    '*.dylib',
    '*.exe',
    '*.class',
    '*.jar',
    '*.war',
    '*.ear',
    '*.zip',
    '*.tar',
    '*.gz',
    '*.7z',
    '*.rar',
    '*.pdf',
    '*.jpg',
    '*.jpeg',
    '*.png',
    '*.gif',
    '*.svg',
    '*.ico',
    '*.woff',
    '*.woff2',
    '*.ttf',
    '*.eot',
}

# Relationship Types
RELATIONSHIP_TYPES = {
    'EXTENDS': 'extends',
    'IMPLEMENTS': 'implements',
    'COMPOSITION': 'composition',
    'AGGREGATION': 'aggregation',
    'USES': 'uses',
    'DEPENDENCY': 'dependency',
    'ASSOCIATION': 'association',
}

# Stereotype Types
STEREOTYPE_TYPES = {
    'CLASS': 'class',
    'INTERFACE': 'interface',
    'ABSTRACT': 'abstract',
    'ENUM': 'enum',
    'STRUCT': 'struct',
}

# HTTP Status Codes
HTTP_STATUS = {
    'OK': 200,
    'BAD_REQUEST': 400,
    'INTERNAL_ERROR': 500,
}

# Error Messages
ERROR_MESSAGES = {
    'INVALID_URL': 'Invalid GitHub URL format',
    'INVALID_ZIP': 'Invalid ZIP file',
    'FILE_TOO_LARGE': 'File exceeds size limit',
    'TOO_MANY_FILES': 'Too many files in repository',
    'CLONE_FAILED': 'Failed to clone repository',
    'EXTRACTION_FAILED': 'Failed to extract ZIP file',
    'ANALYSIS_FAILED': 'Analysis failed',
    'LLM_FAILED': 'LLM enhancement failed',
    'PATH_TRAVERSAL': 'Path traversal detected',
    'TIMEOUT': 'Operation timed out',
}

# Success Messages
SUCCESS_MESSAGES = {
    'ANALYSIS_COMPLETE': 'Analysis completed successfully',
    'CLONE_SUCCESS': 'Repository cloned successfully',
    'EXTRACTION_SUCCESS': 'ZIP extracted successfully',
}

# Logging Configuration
LOG_CONFIG = {
    'LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'DATE_FORMAT': '%Y-%m-%d %H:%M:%S',
}

# Flask Configuration
FLASK_CONFIG = {
    'ENV': os.getenv('FLASK_ENV', 'development'),
    'DEBUG': os.getenv('FLASK_DEBUG', '0') == '1',
    'PORT': int(os.getenv('PORT', '5000')),
    'HOST': os.getenv('HOST', '0.0.0.0'),
}

# Security Configuration
SECURITY_CONFIG = {
    'MAX_URL_LENGTH': 2000,
    'ALLOWED_URL_SCHEMES': ['https'],
    'ALLOWED_DOMAINS': ['github.com'],
    'MAX_ZIP_SIZE_BYTES': 50 * 1024 * 1024,  # 50 MB
    'GITHUB_URL_PATTERN': r'^https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/?$',
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'ENABLE_PARALLEL_PROCESSING': os.getenv('ENABLE_PARALLEL_PROCESSING', 'false').lower() in ('1', 'true', 'yes'),
    'MAX_WORKERS': int(os.getenv('MAX_WORKERS', '4')),
    'CHUNK_SIZE': 100,  # Files per chunk for parallel processing
}

# PlantUML Configuration
PLANTUML_CONFIG = {
    'ENABLE': os.getenv('ENABLE_PLANTUML', 'true').lower() in ('1', 'true', 'yes'),
    'SERVER_URL': os.getenv('PLANTUML_SERVER_URL', 'http://localhost:8080'),
    'TIMEOUT': 60,
    'MAX_DIAGRAM_SIZE': 100000,  # 100 KB
}

# Analysis Options
ANALYSIS_OPTIONS = {
    'DETECT_PATTERNS': True,
    'DETECT_LAYERS': True,
    'INFER_RELATIONSHIPS': True,
    'INCLUDE_PRIVATE_MEMBERS': False,
    'INCLUDE_MAGIC_METHODS': False,
}

# Endpoint Detection Frameworks
FRAMEWORK_PATTERNS = {
    'PYTHON': {
        'flask': [r'@app\.route\s*\(\s*[\'"]([^\'"]+)[\'"]', r'@bp\.route\s*\(\s*[\'"]([^\'"]+)[\'"]'],
        'django': [r'path\s*\(\s*[\'"]([^\'"]+)[\'"]', r're_path\s*\(\s*r[\'"]([^\'"]+)[\'"]'],
        'fastapi': [r'@app\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'],
    },
    'JAVA': {
        'spring': [
            r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*["\']([^"\']+)["\']',
            r'@RequestMapping\s*\([^)]*value\s*=\s*["\']([^"\']+)["\']',
        ],
    },
    'CSHARP': {
        'aspnet': [
            r'\[(HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch)\s*\(\s*"([^"]+)"\s*\)\]',
            r'\[Route\s*\(\s*"([^"]+)"\s*\)\]',
        ],
    },
    'JAVASCRIPT': {
        'express': [r'\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'],
        'nestjs': [r'@(Get|Post|Put|Delete|Patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'],
    },
    'TYPESCRIPT': {
        'express': [r'\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'],
        'nestjs': [r'@(Get|Post|Put|Delete|Patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'],
    },
}

# Design Pattern Indicators
PATTERN_INDICATORS = {
    'singleton': ['getInstance', 'instance', 'Singleton'],
    'factory': ['Factory', 'create', 'build'],
    'builder': ['Builder', 'build', 'withX'],
    'observer': ['Observer', 'subscribe', 'notify', 'addEventListener'],
    'strategy': ['Strategy', 'execute', 'algorithm'],
    'decorator': ['Decorator', 'Component', 'ConcreteDecorator'],
    'adapter': ['Adapter', 'adapt', 'Adaptee'],
    'facade': ['Facade', 'simplify'],
}

# Architectural Layer Indicators
LAYER_INDICATORS = {
    'presentation': ['Controller', 'View', 'UI', 'Component', 'Page'],
    'business': ['Service', 'Manager', 'Handler', 'Processor', 'UseCase'],
    'data': ['Repository', 'DAO', 'Model', 'Entity', 'DataAccess'],
}

# Default Values
DEFAULTS = {
    'SYSTEM_NAME': 'System',
    'DEFAULT_PACKAGE': 'default',
    'DEFAULT_NAMESPACE': 'Default',
    'UNKNOWN_TYPE': 'Object',
}

# Export all constants
__all__ = [
    'FILE_LIMITS',
    'GIT_CONFIG',
    'AI_CONFIG',
    'LANGUAGES',
    'EXTENSION_TO_LANGUAGE',
    'SKIP_DIRECTORIES',
    'SKIP_FILE_PATTERNS',
    'RELATIONSHIP_TYPES',
    'STEREOTYPE_TYPES',
    'HTTP_STATUS',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'LOG_CONFIG',
    'FLASK_CONFIG',
    'SECURITY_CONFIG',
    'PERFORMANCE_CONFIG',
    'PLANTUML_CONFIG',
    'ANALYSIS_OPTIONS',
    'FRAMEWORK_PATTERNS',
    'PATTERN_INDICATORS',
    'LAYER_INDICATORS',
    'DEFAULTS',
]
