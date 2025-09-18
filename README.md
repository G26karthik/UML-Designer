# 📐 Coding Standards

All contributors should follow these guidelines for code quality and maintainability:

## General Principles
- Write clear, self-documenting code
- Use descriptive variable and function names
- Prefer pure functions and modular design
- Avoid magic numbers and hardcoded strings
- Add comments for complex logic

## JavaScript/TypeScript
- Use ES6+ syntax (const/let, arrow functions, destructuring)
- Prefer async/await for asynchronous code
- Use JSDoc for function and module documentation
- Run `npm run lint` before committing

## Python
- Follow PEP8 style guide
- Use type hints where possible
- Add docstrings for all functions and modules
- Prefer list comprehensions and built-in functions

## React/Next.js
- Use functional components and hooks
- Keep components small and focused
- Document props and state with JSDoc
- Use Tailwind CSS for styling

## Testing
- Add/extend unit tests for all new features and bug fixes
- Use descriptive test names and assertions
- Run all tests before submitting PRs

## Documentation
- Update README and relevant docs for any public API or behavior changes
- Prefer Markdown for documentation and comments

## Git & PRs
- Keep commits atomic and focused
- Write clear commit messages
- Reference issues in PRs when relevant

---

Following these standards ensures a maintainable, professional codebase for all contributors.
# UML Designer AI

� **Multi-Language UML Diagram Generator**

A comprehensive tool for analyzing code repositories and generating professional UML diagrams using AI-powered parsing and Mermaid.js visualization.

## 🚀 Features

### **Multi-Diagram Support**
- **Class Diagrams**: Inheritance, composition, aggregation, dependency relationships
- **Use Case Diagrams**: From detected HTTP endpoints
- **Activity Diagrams**: System-level workflows
- **Sequence Diagrams**: Interaction flows
- **State Diagrams**: System state transitions

### **Multi-Language Analysis**
- **Python**: Classes, inheritance, composition detection
- **Java**: Classes, interfaces, Spring Boot endpoints
- **C#**: Classes, inheritance, ASP.NET endpoints
- **JavaScript/TypeScript**: ES6 classes, Express/NestJS endpoints
- **C/C++**: Classes, structs, inheritance

### **Advanced Features**
- **AI-Enhanced Parsing**: Optional LLM integration for improved accuracy
- **Relationship Detection**: Extends, implements, composition, aggregation, dependency
- **Endpoint Detection**: REST API routes from frameworks (Flask, Spring, Express)
- **Caching**: In-memory and disk caching for performance
- **Interactive UI**: Real-time filtering, language visibility, export options

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │ Python Parser   │
│   (Next.js)     │◄──►│   (Express)     │◄──►│   (Flask)       │
│                 │    │                 │    │                 │
│ • UI Controls   │    │ • Caching       │    │ • AST Analysis  │
│ • Diagram Render│    │ • Proxy         │    │ • LLM Merge     │
│ • Export        │    │ • Health Check  │    │ • Multi-lang    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Requirements Coverage

✅ **Diagram Accuracy**: Improved parsing logic with standards-compliant relationships  
✅ **Diagram Types**: Support for 5 UML diagram types  
✅ **Multi-Language**: 6+ programming languages with framework detection  
✅ **Relationship Accuracy**: Extends, implements, composition, aggregation, dependency  
✅ **Software Quality**: Comprehensive tests, documentation, modular architecture  

## 🛠️ Quick Start

### **Prerequisites**
- Node.js 18+
- Python 3.8+
- Git

### **Installation**
```bash
# Clone repository
git clone <repository-url>
cd uml-designer

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install

# Install Python parser dependencies
cd ../python-parser
pip install -r requirements.txt
```

### **Configuration**
```bash
# Backend environment
cp backend/.env.example backend/.env
# Set PYTHON_PARSER_URL=http://localhost:5000

# Python parser environment
cp python-parser/.env.example python-parser/.env
# Set GROQ_API_KEY for AI enhancement (optional)
```

### **Running the Application**
```bash
# Terminal 1: Python Parser
cd python-parser
python app.py

# Terminal 2: Backend
cd backend
npm start

# Terminal 3: Frontend
cd frontend
npm run dev
```

Visit `http://localhost:3000` to use the application.

## 📖 Usage

1. **Select Diagram Type**: Choose from Class, Use Case, Activity, Sequence, or State
2. **Enter Repository URL**: Paste a public GitHub repository URL
3. **Analyze**: Click "Analyze" to process the repository
4. **Customize**: Use filters for relationships, fields, methods, and language visibility
5. **Export**: Copy Mermaid source or download SVG

## 🧪 Testing

```bash
# Run all tests
cd backend && npm test
cd ../frontend && npm test
cd ../python-parser && python -m pytest

# Test coverage
cd python-parser && python -m pytest --cov=analyze
```

## 📚 API Documentation


### **Backend Endpoints (v1)**
- `POST /api/v1/analyze`: Analyze repository (GitHub URL or ZIP upload)
- `GET /api/v1/health`: Service health check
- `GET /api/v1/openapi.json`: OpenAPI 3.0 specification for backend API

### **Python Parser API**
- `POST /analyze`: Process repository and return schema

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Made with ❤️ for software engineering education and professional UML diagramming**

## 🚀 Quick Start

1. **Start the Python Parser** (Port 5000)
   ```bash
   cd python-parser
   pip install -r requirements.txt
   python app.py
   ```

2. **Start the Backend** (Port 3001)
   ```bash
   cd backend
   npm install
   npm start
   ```

3. **Start the Frontend** (Port 3000)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Open http://localhost:3000** and paste any public GitHub repository URL!

## 🎯 Who This Is For

- **Product Managers & Stakeholders**: Get clear visual overviews of system architecture without diving into code
- **Software Engineers**: Quickly understand unfamiliar codebases, plan refactoring, or onboard new team members
- **Students & Educators**: Learn how real-world code translates to UML diagrams
- **Technical Writers**: Generate documentation diagrams automatically

## 🏗️ Architecture Overview

### Three-Tier Architecture
```
Frontend (Next.js + React + Mermaid)
    ↓ HTTP Requests
Backend (Express.js Proxy + Caching)
    ↓ Repository Analysis
Python Parser (Flask + Multi-Language AST + AI)
```

### **Frontend Layer** (`/frontend`)
- **Technology**: Next.js 13+, React, Tailwind CSS, Mermaid.js
- **Purpose**: User interface, diagram rendering, and interactive controls
- **Key Features**:
  - Client-side Mermaid rendering (avoids SSR issues)
  - Language-specific color coding and visibility toggles
  - Real-time diagram filtering (fields, methods, relationships)
  - Copy Mermaid source and download SVG functionality

### **Backend Layer** (`/backend`) 
- **Technology**: Express.js, Node.js
- **Purpose**: API proxy, caching, and request optimization
- **Key Features**:
  - Intelligent caching (in-memory + disk) with TTL
  - Request timeout handling and rate limiting
  - CORS configuration and security headers
  - Repository upload support (ZIP files)

### **Parser Layer** (`/python-parser`)
- **Technology**: Python 3.10+, Flask, javalang, AST parsing
- **Purpose**: Multi-language code analysis and AI enrichment
- **Key Features**:
  - Static AST analysis for 7+ programming languages
  - Relationship inference (inheritance, composition, dependencies)
  - Optional AI enhancement via Groq API
  - Performance optimization (shallow clones, file size limits)

## 🔍 What It Analyzes

### **Supported Languages & Features**

| Language | Classes | Fields | Methods | Inheritance | Implements | Uses/Dependencies |
|----------|---------|--------|---------|-------------|------------|------------------|
| **Java** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Python** | ✅ | ✅ | ✅ | ✅ | ❌ | 🔄 |
| **C#** | ✅ | ✅ | ✅ | ✅ | ✅ | 🔄 |
| **TypeScript** | ✅ | ✅ | ✅ | ✅ | ✅ | 🔄 |
| **JavaScript** | ✅ | ❌ | ✅ | ✅ | ❌ | 🔄 |
| **C++** | ✅ | ❌ | ✅ | ✅ | ❌ | 🔄 |
| **C** | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |

**Legend**: ✅ Fully Supported | 🔄 Roadmap | ❌ Not Applicable

### **Relationship Types Detected**
- **Inheritance** (`<|--`): Class extends another class
- **Interface Implementation** (`<|..`): Class implements an interface
- **Composition** (`*--`): Strong ownership relationship
- **Aggregation** (`o--`): Weak ownership relationship  
- **Dependency/Uses** (`..>`): Class depends on another class
- **Association** (`-->`): General relationship

## 📊 Data Flow & Processing

### **Input Processing**
1. **Repository Input**: GitHub URL or uploaded ZIP file
2. **Git Operations**: Shallow clone (depth=1) for performance
3. **File Discovery**: Recursive scan with intelligent filtering
4. **Language Detection**: File extension-based routing

### **Analysis Pipeline**
```
Raw Source Code
    ↓ Language-Specific Parsers
AST Extraction (Classes, Methods, Fields)
    ↓ Relationship Inference Engine  
Relationship Graph (Extends, Implements, Uses)
    ↓ AI Enhancement (Optional)
Enriched Schema (JSON)
    ↓ Mermaid Conversion
UML Class Diagram (Rendered)
```

### **Output Schema**
```json
{
  "python": [
    {
      "class": "ClassName",
      "fields": ["field1: type", "field2"],
      "methods": ["method1", "method2"]
    }
  ],
  "java": [...],
  "relations": [
    {
      "from": "BaseClass",
      "to": "DerivedClass", 
      "type": "extends",
      "source": "heuristic|ai"
    }
  ],
  "meta": {
    "commit": "abc123...",
    "files_scanned": 245
  }
}
```

## ⚙️ Configuration Guide

### **Environment Variables**

#### **Frontend** (`.env.local`)
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:3001
```

#### **Backend** (`.env`)
```bash
# Core Configuration
PYTHON_PARSER_URL=http://localhost:5000
PORT=3001

# Performance & Limits
ANALYZE_TIMEOUT_MS=120000
JSON_LIMIT=5mb
UPLOAD_LIMIT_BYTES=52428800

# Caching Strategy
CACHE_TTL_MS=300000
DISK_CACHE_TTL_MS=86400000
MAX_CACHE_ENTRIES=200
DISK_CACHE_DIR=./cache

# Security
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

#### **Python Parser** (`.env`)
```bash
# AI Configuration (Optional)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
STUB_LLM=false

# Performance Tuning
MAX_FILE_BYTES=500000
MAX_FILES=5000
GIT_CLONE_DEPTH=1

# Development
FLASK_ENV=development
```

## 🔧 Advanced Usage

### **Performance Optimization**
- **Large Repositories**: Increase `MAX_FILES` and `MAX_FILE_BYTES` gradually
- **Memory Usage**: Monitor cache size with `MAX_CACHE_ENTRIES`
- **Network**: Use `GIT_CLONE_DEPTH=1` for faster clones
- **CPU**: Set `ANALYZE_TIMEOUT_MS` based on expected repository size

### **AI Enhancement**
- **With AI**: Rich relationship detection, better field/method naming
- **Without AI**: Fast heuristic-only analysis, set `STUB_LLM=true`
- **Hybrid**: AI enhances heuristics but never replaces them

### **Deployment Considerations**
- **Frontend**: Static export compatible, CDN-ready
- **Backend**: Stateless design, horizontal scaling ready
- **Parser**: CPU-intensive, consider dedicated instances
- **Caching**: Redis can replace in-memory cache for multi-instance deployments

## 🧪 Testing & Development

### **Running Tests**
```bash
# Backend tests
cd backend && npm test

# Frontend tests  
cd frontend && npm test

# Python parser tests
cd python-parser && pytest -q
```

### **Development Workflow**
1. **Make Changes**: Edit source code in respective directories
2. **Test Locally**: Use the test commands above
3. **Integration Test**: Test with real repositories
4. **Performance Check**: Monitor memory/CPU usage
5. **Documentation**: Update relevant README files

## 🐛 Troubleshooting

### **Common Issues**

**Mermaid Rendering Errors**
- Use "Copy Mermaid" to inspect generated diagram source
- Check browser console for specific parsing errors
- Verify class names don't contain special characters

**Repository Analysis Timeouts**
- Increase `ANALYZE_TIMEOUT_MS` for large repositories
- Reduce `MAX_FILES` to scan fewer files
- Check network connectivity to GitHub

**Memory Issues**
- Lower `MAX_CACHE_ENTRIES` to reduce memory usage
- Decrease `MAX_FILE_BYTES` to skip large files
- Monitor disk cache size in `DISK_CACHE_DIR`

**AI/LLM Issues**
- Verify `GROQ_API_KEY` is valid and has quota
- Set `STUB_LLM=true` to bypass AI temporarily
- Check API endpoint availability

## 🗺️ Roadmap

### **Short Term** (Next 2-3 months)
- [ ] Enhanced Python relationship detection
- [ ] C# inheritance and interface analysis
- [ ] TypeScript advanced type relationship mapping
- [ ] Performance dashboard and metrics

### **Medium Term** (3-6 months)
- [ ] Multiple AI provider support (OpenAI, Anthropic, Local models)
- [ ] Advanced caching with Redis integration
- [ ] Batch repository analysis
- [ ] Custom diagram styling and themes

### **Long Term** (6+ months)
- [ ] Real-time collaboration features
- [ ] Integration with popular IDEs (VS Code extension)
- [ ] API documentation generation
- [ ] Enterprise SSO and authentication

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### **Development Setup**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow the Quick Start guide above
4. Make your changes and test thoroughly
5. Submit a pull request with clear description

### **Contribution Guidelines**
- **Code Style**: Follow existing patterns and linting rules
- **Testing**: Add tests for new features and bug fixes
- **Documentation**: Update relevant README files
- **Performance**: Consider impact on large repositories
- **Backwards Compatibility**: Avoid breaking existing APIs

### **Areas We Need Help**
- Additional programming language support
- Performance optimizations
- UI/UX improvements
- Documentation and examples
- Integration testing

## 📖 API Reference

### **Backend Endpoints**

#### `POST /analyze`
Analyze a repository and return UML diagram data.

**Request Body:**
```json
{
  "githubUrl": "https://github.com/user/repo"
}
```

**Response:**
```json
{
  "schema": {
    "python": [...],
    "java": [...],
    "relations": [...],
    "meta": {...}
  }
}
```

#### `POST /analyze` (File Upload)
Upload a ZIP file for analysis.

**Request:** Multipart form with `repoZip` file field
**Response:** Same as GitHub URL analysis

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Mermaid.js**: For excellent diagram rendering
- **Groq**: For fast AI inference capabilities  
- **javalang**: For robust Java AST parsing
- **Next.js Team**: For the amazing React framework
- **Open Source Community**: For inspiration and contributions

---

**Made with ❤️ for the developer community**

*For questions, issues, or feature requests, please open an issue on GitHub.*

## Architecture
- frontend (Next.js + Tailwind + Mermaid): UI, diagram rendering, and controls
- backend (Express): proxies /analyze to python-parser, caching (memory + disk), limits, CORS, compression
- python-parser (Flask): scans repos, extracts classes/relations (multi-language), optional Groq enrichment

## Quick start
1) Start python-parser
   - Optional env:
     - STUB_LLM=true (skip LLM, return AST summary)
     - MAX_FILES=5000, MAX_FILE_BYTES=500000
     - GROQ_API_KEY, GROQ_MODEL (if using LLM)
2) Start backend
   - Optional env:
     - PYTHON_PARSER_URL=http://localhost:5000
     - ALLOWED_ORIGINS=http://localhost:3000
     - MAX_CACHE_ENTRIES=200, CACHE_TTL_MS=300000, DISK_CACHE_TTL_MS=86400000
3) Start frontend
   - Optional env:
     - NEXT_PUBLIC_BACKEND_URL=http://localhost:3001

## Features
- Multi-language extraction: python, java, csharp, javascript, typescript, cpp, c (html/css presence only)
- Relations: extends, implements, uses (Java), with provenance tags (H/AI)
- Performance: shallow clone, skip heavy dirs, size cap, files cap; backend gzip and caching
- UI: per-language visibility & color, fields/methods toggles, relation source filter, AI edge coloring, copy/download

## Tips
- For large repos, raise MAX_FILES and MAX_FILE_BYTES cautiously.
- Disk cache in backend speeds repeat requests; cache key includes repo URL and commit when available.
- If Mermaid fails, use "Copy Mermaid" to inspect the diagram text.
# UML Designer AI

A full-stack app that generates easy-to-understand UML class diagrams from code repositories. Paste a public GitHub URL or upload a zip; we scan the repo, detect classes and relationships, and render a Mermaid UML diagram with copy/download tools.

## Who is this for?
- Product managers and stakeholders who want a clear picture of system structure without digging into code.
- Engineers who need a quick, visual map of a codebase to plan changes or onboarding.
- Students and beginners who want to learn how code turns into class diagrams.

## Why this exists
Understanding large or unfamiliar repos is slow and error-prone. This tool gives a fast, visual overview by combining static heuristics and an optional AI pass. It works even without AI (heuristics only) and is careful to avoid invalid diagrams.

## What it does (Definition)
- Clones or unzips a repository (shallow by default) and walks source files.
- Extracts classes, fields, and methods for multiple languages.
- Infers key relations (extends, implements, uses) with simple, explainable rules.
- Optionally enriches with an AI provider (Groq) to fill gaps while keeping a strict JSON contract.
- Renders a Mermaid UML class diagram in the browser. Includes copy and SVG download.

## Supported languages (static heuristics)
- Java: classes, fields, methods; extends/implements; parameter-based uses.
- Python: classes, fields (class vars and self.*), methods.
- C#: class and method names (regex heuristics).
- JavaScript/TypeScript: class names, class methods; TS also detects simple typed fields.
- C/C++: classes/structs (basic), method-like signatures (heuristic).
- HTML/CSS: tracked for presence; not rendered as classes.

Notes:
- Relations are strongest for Java today. Other languages show classes and members; relations are a roadmap item.
- Files larger than MAX_FILE_BYTES (default 500KB) are skipped for performance.

## Architecture
- frontend (Next.js + React + Tailwind + Mermaid)
  - Client-only Mermaid rendering to avoid SSR issues.
  - Toolbar: Copy Mermaid, Download SVG.
  - Toggle: show/hide relations; legend of edge types.
- backend (Express)
  - Proxies /analyze to the parser; supports zip uploads.
  - In-memory cache for repeated URLs (TTL configurable).
- python-parser (Flask + analyzers)
  - Static heuristics per language; merges with AI output when available.
  - Groq (OpenAI-compatible) as default AI provider; strict JSON prompt.
  - Shallow git clone (depth=1 by default) for large repos.

## Data contract (schema)
Parser returns JSON:
- python/java/csharp/javascript/typescript/cpp/c/html/css: arrays of
  - { class: string, fields: string[], methods: string[] }
- relations: [{ from, to, type, source? }]
  - type: extends | implements | uses | aggregates | composes | association
  - source: heuristic | ai (when known)

The frontend converts this schema into a Mermaid classDiagram. Unknown endpoints are added as placeholder classes to keep diagrams valid.

## How to run (local)
1. Start python-parser (needs Python 3.10+):
   - Install deps: `pip install -r python-parser/requirements.txt`
   - Set env (optional): GROQ_API_KEY, GROQ_MODEL, STUB_LLM=false/true, MAX_FILE_BYTES, GIT_CLONE_DEPTH
   - Run: `python python-parser/app.py`
2. Start backend:
   - Set MONGO_URL (URL-encode special chars) and optional PYTHON_PARSER_URL
   - `cd backend && npm install && npm start`
3. Start frontend:
   - `cd frontend && npm install && npm run dev`

Open http://localhost:3000 and paste a public GitHub URL.

## Tips for large repositories
- Shallow clone is enabled by default (depth=1). Increase GIT_CLONE_DEPTH if needed.
- Increase MAX_FILE_BYTES to analyze bigger files; lowering it can speed up scans.
- The backend caches results for a few minutes to avoid repeated work.

## Communicating the diagram to non-experts
- Boxes are “classes.” They list fields (data) and methods (actions).
- Lines show relationships:
  - Base <|-- Derived: inheritance (Derived is a kind-of Base)
  - Interface <|.. Class: implements (Class promises to provide Interface methods)
  - A *-- B: composition (A strongly owns B)
  - A o-- B: aggregation (A has B, but B can outlive A)
  - A ..> B: uses/dependency (A depends on B)
  - A --> B: association (general link)
- If you see only boxes and no lines: either there are no relations detected yet, or the language’s relation heuristics aren’t implemented.

## Env configuration
- backend
  - MONGO_URL: mongodb connection (URL-encode special characters)
  - PYTHON_PARSER_URL: http://localhost:5000
  - CACHE_TTL_MS: cache duration for analyze results
- python-parser
  - GROQ_API_KEY: API key for Groq (optional if STUB_LLM=true)
  - GROQ_MODEL: default meta-llama/llama-4-scout-17b-16e-instruct
  - GROQ_API_URL: OpenAI-compatible chat completions URL
  - STUB_LLM: true|false to bypass AI
  - MAX_FILE_BYTES: skip huge files (default 500kB)
  - GIT_CLONE_DEPTH: shallow git depth (default 1)

## Roadmap
- Relations for Python/C#/JS/TS/C++ (inheritance/implements/uses via AST parsing).
- Legend toggle, per-source (AI vs heuristic) relation filtering, and field/method visibility toggles.
- Persistent cache keyed by URL + commit hash.
- Robust class name sanitization for Mermaid edge cases.

## Contributing
- Keep changes small and testable.
- Add/extend unit tests when changing public behavior.
- Prefer additive heuristics that never break diagram validity.

## Appendix: FAQs
- Who maintains this? You do—this repo is designed to be easy to extend.
- Why Mermaid? It’s simple, human-readable, and easy to copy/paste in docs.
- What if the AI returns prose? We extract JSON only; if it fails, we fall back to heuristics.
- Can I run without AI? Yes: set STUB_LLM=true.
