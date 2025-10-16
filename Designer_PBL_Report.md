# UML Designer AI — Project-Based Learning (PBL) Report
**Course:** Bachelor of Technology in Computer Science and Engineering (Course Code: [Placeholder])
**Student:** [Student Name] — Roll: [Roll Number]
**Faculty Guide:** [Guide Name]
**Department:** Department of Computer Science and Engineering, Geethanjali College of Engineering and Technology
**Academic Year:** A.Y. 2025–26

---

## Abstract

UML Designer AI is a full‑stack platform that automatically analyzes source code and natural language prompts to produce UML diagrams. The system combines precise static analysis, heuristic relationship detection, and optional AI‑assisted inference to produce a normalized schema that can be rendered into PlantUML diagrams. A Node.js backend provides a secure API gateway, layered caching and validation; a Python microservice performs language‑specific parsing and relationship inference; and a React frontend renders and exports diagrams for users.

This report documents the system design, implementation details, representative code excerpts, testing considerations, and operational guidance. The project emphasizes engineering trade‑offs (accuracy vs. latency), modular analyzers for multi‑language support, and practical measures for secure handling of untrusted inputs. The artifacts included (code snippets and UML diagrams) are drawn directly from the repository and are intended to be verifiable by reviewers.

---

## Table of Contents

1. Abstract
2. Introduction
3. System Design
  3.1 Architecture Overview
  3.2 Modules and Responsibilities
  3.3 Data and Cache Model
4. Implementation
  4.1 Integration Flow
  4.2 Key Code Snippets
  4.3 Endpoint Behavior and Error Handling
5. Testing, Deployment, and Maintenance
6. Conclusion and Future Work
7. References

---

## 1. Introduction

Modern software projects are increasingly complex and multi‑language. UML diagrams remain a compact and widely understood medium for communicating architecture and design. UML Designer AI was built to reduce the friction of producing accurate diagrams by automating repository analysis and diagram generation.

Primary goals:

- Transform source code and natural language prompts into validated UML schemas.
- Make diagram generation repeatable, performant, and safe for untrusted inputs.
- Provide an extensible architecture so additional languages and diagram types can be added with minimal friction.

Key trade‑offs and design principles:

- Accuracy vs. responsiveness: deep analysis yields higher‑quality diagrams but increases latency. The system mitigates this with a two‑tier cache (in‑memory LRU + disk persistence) and configurable timeouts.
- Modularity: language analyzers are pluggable, enabling incremental extension and independent testing.
- Security: input validation, upload checks (ZIP magic bytes and path checks), CORS policy enforcement, and rate limiting protect the service from common misuse vectors.

Target users include developers, educators, and students who need rapid, reproducible visualizations of code structure.

---

## 2. System Design

### 2.1 Architecture Overview

UML Designer AI follows a modular client–server pattern:

- Frontend (Next.js + React): user interface for submitting GitHub URLs or ZIP uploads, rendering diagrams, and exporting artifacts.
- Backend (Node.js + Express): API gateway, request validation, caching, monitoring, and proxying to the parser service.
- Python Parser (Flask): language‑specific analyzers that parse source files, detect relationships, and produce a normalized schema consumable by the PlantUML generator.

The control flow is: User → Frontend → Backend → Python Parser → Backend → Frontend.

### 2.2 Modules and Responsibilities

Frontend

- Accepts input (GitHub URL or ZIP upload) and submits it to the backend.
- Encodes PlantUML and fetches SVG/PNG renderings for display and export.

Backend

- Exposes endpoints such as `/analyze`, `/generate-plantuml`, and `/uml-from-prompt`.
- Implements a memory+disk caching layer keyed by repository URL and optionally commit hash.
- Validates responses from the parser using a JSON schema validator and injects safe defaults when needed.
- Controls Python parser availability and can auto‑start a local parser when configured.

Python Parser

- Contains language analyzers under `analyzers/` and a `RelationshipDetector` for cross‑file relations.
- Supports AST‑based parsing for Python, `javalang` for Java, and targeted heuristics for other languages.
- Returns a normalized schema containing `meta`, language arrays (e.g., `python`, `java`), `relations`, `endpoints`, `patterns`, and `layers`.

### 2.3 Data and Cache Model

- Cache key: repository URL or `url@commit` when commit metadata is available.
- In‑memory cache: a Map used as a simple insertion‑ordered LRU whose capacity is governed by `MAX_CACHE_ENTRIES`.
- Disk cache: TTL‑based JSON files written to a cache directory to persist analysis results across restarts.

---

## 3. Implementation

This section highlights implementation patterns, representative code excerpts, and the way endpoints validate and proxy requests.

### 3.1 Integration Flow

- A user provides a GitHub URL or uploads a ZIP.
- Backend validates the input (GitHub URL format, ZIP magic bytes, safe upload path).
- Backend checks memory and disk cache for an existing analysis. If present and fresh, it returns cached data.
- Otherwise, the backend proxies the request to the Python parser and validates the returned schema.
- Valid schemas are stored in memory and persisted to disk; invalid schemas produce clear validation errors.

### 3.2 Key Code Snippets

The examples below are taken from the repository and simplified for readability while preserving the original logic.

#### Python file analysis (extract of `python` analyzer)

```python
def analyze_file(self, file_path: str, package_path: str = "") -> List[Dict]:
    classes = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        source = f.read()
    tree = ast.parse(source)
    self._extract_imports(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_dict = self._analyze_class(node, package_path)
            if class_dict:
                classes.append(class_dict)
                self.add_class_name(class_dict['class'])
    return classes
```

This snippet demonstrates AST traversal to locate class definitions and extract class metadata.

#### Caching implementation (excerpts from `backend/routes/api.js`)

```javascript
// Cache key helper
const cacheKey = (url, commit) => (commit ? `${url}@${commit}` : url);

// In-memory cache (LRU by insertion order) and disk persistence
const memCache = new Map();
const keyHash = s => require('crypto').createHash('sha1').update(s).digest('hex');

// Read cached analysis from disk (TTL-based)
const readDisk = async key => {
  try {
    const file = require('path').join(diskDir, `${keyHash(key)}.json`);
    const stat = await require('fs/promises').stat(file);
    if (Date.now() - stat.mtimeMs > diskTtlMs) {
      await require('fs/promises').unlink(file).catch(() => {});
      return null;
    }
    return JSON.parse(await require('fs/promises').readFile(file, 'utf8'));
  } catch {
    return null;
  }
};

// Persist cache entry to disk (best-effort)
const writeDisk = async (key, data) => {
  try {
    const file = require('path').join(diskDir, `${keyHash(key)}.json`);
    await require('fs/promises').writeFile(file, JSON.stringify(data));
  } catch (e) {
    logger?.warn?.(`Disk cache write failed: ${e.message}`);
  }
};

// Ensure memory cache capacity (evict oldest entries when over limit)
const ensureCapacity = () => {
  while (memCache.size > maxEntries) {
    const first = memCache.keys().next().value;
    if (!first) break;
    memCache.delete(first);
  }
};

// Example lookup
if (memCache.has(cacheKey)) {
  return memCache.get(cacheKey);
}
```

These helpers implement the two‑tier caching strategy used by the `/analyze` endpoint.

#### Repository analysis endpoint (behavior summary)

- Validate GitHub URL format using a strict pattern.
- Check memory cache and then disk cache.
- Proxy to Python parser (`/analyze`) with a configurable timeout.
- Validate the returned schema using `validateUmlSchema`; inject safe default `meta` when missing.
- Cache and persist validated results to memory and disk, and return the schema to the client.

A condensed portion of the request/response flow (omitting boilerplate error wrapping):

```javascript
const response = await http.post(`${pythonUrl}/analyze`, { githubUrl: v.url }, { timeout });
const data = response?.data ?? {};

// Inject default meta if missing
if (data && data.schema && (!data.schema.meta || typeof data.schema.meta !== 'object')) {
  data.schema.meta = { classes_found: 0, files_scanned: 0, languages: [], system: 'UnknownSystem' };
}

const validation = validateUmlSchema(data);
if (!validation.isValid) throw createValidationError(`Invalid schema structure: ${validation.errors.join(', ')}`);

memCache.set(urlKey, { data, ts: Date.now() });
ensureCapacity();
writeDisk(urlKey, data).catch(() => {});

return res.status(response.status || 200).json(data);
```

#### PlantUML generation proxy (validation + forward)

The `/generate-plantuml` endpoint validates the incoming request body (schema and diagram_type) and forwards it to the parser's `/generate-plantuml` endpoint. Timeouts and error types (validation, external service) are handled consistently so clients get meaningful responses.

```javascript
const response = await http.post(`${pythonUrl}/generate-plantuml`, { schema, diagram_type }, { timeout });
return res.status(response.status || 200).json(response.data ?? {});
```

### 3.3 Endpoint Error Handling and Resilience

- Timeouts are translated into domain‑specific timeout errors for clearer client messaging.
- 4xx responses from the parser are surfaced as validation errors; 5xx responses become internal/external service errors.
- The backend attempts to auto‑start a local Python parser when configured for development/CI convenience (see `pythonServiceManager`). This improves developer experience while production deployments typically use a managed parser service.

---

## 4. Testing, Deployment, and Maintenance

Testing

- The repository contains unit and integration tests under `__tests__` for backend, frontend, and parser components. Tests exercise endpoint behavior, schema validation, cache behavior, and PlantUML generation.
- Maintain tests whenever analyzers are modified—language grammars and heuristics change over time and will otherwise cause regressions.

Deployment and configuration

- The backend uses environment variables for tuning: `ANALYZE_TIMEOUT_MS`, `GENERATE_TIMEOUT_MS`, `CACHE_TTL_MS`, `MAX_CACHE_ENTRIES`, `DISK_CACHE_DIR`, `ALLOWED_ORIGINS`, and `ADMIN_TOKEN`.
- For local development the backend can auto‑start the Python parser; in production, point `PYTHON_PARSER_URL` at a stable parser service and tune cache TTLs.

Observability and performance

- The project uses structured logging and periodic metrics logging. Store logs centrally and enable monitoring of parser availability, request latencies, cache hit ratios, and disk usage.
- Tune rate limiting (`RATE_WINDOW_MS`, `RATE_MAX`) to protect the service while allowing reasonable usage for classroom or CI scenarios.

Maintenance guidance

- Keep `ALLOWED_ORIGINS` and `ADMIN_TOKEN` configured in production; protect admin endpoints.
- Consider incremental analysis (future work) to avoid reprocessing entire repositories when small changes occur.

---

## 5. Conclusion and Future Work

UML Designer AI demonstrates a pragmatic engineering approach to automating UML generation: combine language‑aware parsing, relationship detection, and safe, performant API patterns. The project successfully meets its goals of producing validated UML schemas and rendering them into PlantUML diagrams for consumption by the frontend.

Lessons learned and operational advice:

- Tests are essential. A small change in an analyzer can dramatically change relationships and diagram structure; coverage for analyzers prevents regressions.
- Observability matters. Parser availability and outbound call failures are the most frequent operational issues; log and monitor them.
- Tune caching according to workload. For classroom use, longer cache TTLs are helpful; for CI use, shorter TTLs and commit‑specific caching are preferable.

Recommended next steps and improvements:

- Incremental reanalysis: support reanalysis of changed files only, rather than entire repositories.
- Enhanced exports: produce optimized SVG, and allow interactive annotations linking diagram elements back to source file locations.
- CI/GitHub Action: expose an action or CLI for automatic diagram generation in CI pipelines.

Overall, the repository provides a solid foundation for automated diagram generation and is well suited for continued extension and classroom adoption.

---

## 6. References

1. Node.js Documentation: https://nodejs.org/
2. Express.js Documentation: https://expressjs.com/
3. React Documentation: https://react.dev/
4. Next.js Documentation: https://nextjs.org/
5. Python Documentation: https://python.org/
6. Flask Documentation: https://flask.palletsprojects.com/
7. javalang Library: https://github.com/c2nes/javalang
8. PlantUML: https://plantuml.com/
9. Tailwind CSS: https://tailwindcss.com/
10. Groq/OpenAI API Documentation: https://platform.openai.com/docs/
11. Winston Logger: https://github.com/winstonjs/winston
12. Diskcache: https://grantjenks.com/docs/diskcache/
13. Project README and source code files

---

*Diagrams used in this report are stored in the repository's `diagrams/` directory (e.g., `diagrams/class_diagram.png`) and will render when the repository is viewed on GitHub.*
      if (err?.response) {
