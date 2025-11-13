# UML Designer AI - IEEE Format Test Cases Documentation

## Project Information
- **Project Name:** UML Designer AI
- **Version:** 1.0.0
- **Date:** November 13, 2025
- **Prepared By:** Automated Test Case Generation
- **Document Type:** IEEE 829 Standard Test Case Specification

---

## Table of Contents
1. [Backend Module Test Cases](#backend-module-test-cases)
2. [Frontend Module Test Cases](#frontend-module-test-cases)
3. [Python Parser Module Test Cases](#python-parser-module-test-cases)

---

## Backend Module Test Cases

### Test Suite: Backend API Services
**Module:** Backend (Node.js/Express)  
**Component Path:** `/backend`  
**Testing Framework:** Jest/Vitest  
**Test Coverage Target:** 80%+

---

### TC-BE-001: GitHub Repository Analysis via POST /api/analyze

**Test Case ID:** TC-BE-001  
**Test Case Name:** Validate GitHub Repository Analysis Endpoint  
**Feature Under Test:** Repository Analysis via GitHub URL  
**Priority:** High  
**Test Type:** Functional, Integration  

**Preconditions:**
- Backend server is running on port 3001
- Python parser service is available at http://localhost:5000
- Valid GitHub repository URL is available for testing
- Network connectivity is established

**Test Data:**
```json
{
  "githubUrl": "https://github.com/valid-user/valid-repo"
}
```

**Test Steps:**
1. Initialize HTTP client with base URL http://localhost:3001
2. Prepare POST request with JSON payload containing valid GitHub URL
3. Send POST request to `/api/analyze` endpoint
4. Wait for response with timeout of 60 seconds
5. Verify response status code
6. Parse and validate response JSON structure
7. Verify schema contains required fields: classes, relations, meta

**Expected Results:**
- HTTP Status Code: 200 OK
- Response Content-Type: application/json
- Response Body Structure:
  ```json
  {
    "schema": {
      "classes": [],
      "relations": [],
      "meta": {
        "system": "string",
        "languages": ["array"],
        "classes_found": "number",
        "files_scanned": "number"
      }
    }
  }
  ```
- Response time < 60 seconds
- No memory leaks or crashes

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: All expected results are met
- FAIL: Any expected result is not met

**Test Environment:**
- OS: Windows/Linux/MacOS
- Node.js: v18+
- Backend Port: 3001
- Python Parser Port: 5000

**Notes:**
- This test validates the core repository analysis functionality
- Tests both AST parsing and LLM enhancement via Gemini
- Requires active internet connection for git clone operations

---

### TC-BE-002: ZIP File Upload and Analysis via POST /api/analyze

**Test Case ID:** TC-BE-002  
**Test Case Name:** Validate ZIP File Upload and Analysis  
**Feature Under Test:** Repository Analysis via ZIP Upload  
**Priority:** High  
**Test Type:** Functional, Security  

**Preconditions:**
- Backend server is running on port 3001
- Python parser service is available
- Valid test ZIP file with source code is prepared
- ZIP file size is within limits (< 50MB)

**Test Data:**
- ZIP File: `test-repo.zip` (contains Python/Java/TypeScript source files)
- Expected Content: At least 5 source files with classes

**Test Steps:**
1. Create multipart/form-data request
2. Attach ZIP file to `repoZip` field
3. Send POST request to `/api/analyze` endpoint
4. Monitor response time and memory usage
5. Verify response status and structure
6. Validate security checks (path traversal, zip bomb prevention)
7. Verify cleanup of temporary files

**Expected Results:**
- HTTP Status Code: 200 OK
- Response contains valid schema with analyzed classes
- Temporary upload directory is cleaned up after processing
- No path traversal vulnerabilities exploited
- ZIP extraction completes within timeout
- Response time < 45 seconds

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: ZIP is processed successfully, temporary files are cleaned up
- FAIL: Processing fails, security vulnerability detected, or memory leak occurs

**Test Environment:**
- OS: Windows/Linux/MacOS
- Upload Directory: `backend/uploads/`
- Temp Directory: System temp directory

**Notes:**
- Tests security validation for ZIP uploads
- Verifies proper resource cleanup
- Tests path traversal attack prevention

---

### TC-BE-003: Health Check Endpoint Validation GET /api/health

**Test Case ID:** TC-BE-003  
**Test Case Name:** Verify Health Check Endpoint Functionality  
**Feature Under Test:** Service Health Monitoring  
**Priority:** Medium  
**Test Type:** Functional, Monitoring  

**Preconditions:**
- Backend server is running
- Python parser service may or may not be available

**Test Data:** None required

**Test Steps:**
1. Send GET request to `/api/health` endpoint
2. Verify response status code
3. Parse response JSON
4. Validate response structure contains status, uptime, cache info
5. Test with Python parser service down (negative test)
6. Verify degraded status reporting

**Expected Results:**
- HTTP Status Code: 200 OK (when all services healthy)
- HTTP Status Code: 503 Service Unavailable (when Python parser down)
- Response Structure:
  ```json
  {
    "status": "healthy|degraded",
    "timestamp": "ISO8601 string",
    "uptime": "number (seconds)",
    "services": {
      "backend": "healthy",
      "pythonParser": "healthy|unreachable"
    },
    "cache": {
      "memory_entries": "number",
      "disk_entries": "number"
    }
  }
  ```
- Response time < 5 seconds

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: Health endpoint returns correct status for all service states
- FAIL: Incorrect status reported or endpoint unreachable

**Test Environment:**
- Backend Port: 3001
- Python Parser Port: 5000

**Notes:**
- Used by load balancers and monitoring systems
- Tests both healthy and degraded states
- Critical for production deployment

---

### TC-BE-004: Cache Management and Performance

**Test Case ID:** TC-BE-004  
**Test Case Name:** Validate In-Memory and Disk Cache Functionality  
**Feature Under Test:** Dual-Layer Caching (Memory + Disk)  
**Priority:** Medium  
**Test Type:** Performance, Functional  

**Preconditions:**
- Backend server is running
- Cache directory exists and is writable
- Admin token is configured in environment

**Test Data:**
- Test GitHub URL: `https://github.com/test/repo-1`
- Admin Token: Valid token from environment

**Test Steps:**
1. Send first analysis request for test repository
2. Measure response time (cold cache - miss)
3. Send second analysis request for same repository
4. Measure response time (warm cache - hit)
5. Send GET request to `/api/admin/cache/info` with admin token
6. Verify cache statistics
7. Send POST request to `/api/admin/cache/purge` with admin token
8. Verify cache is cleared
9. Send analysis request again and verify it's treated as cache miss

**Expected Results:**
- First request (cache miss): Response time ~15-60 seconds
- Second request (cache hit): Response time < 500ms
- Cache info endpoint returns:
  ```json
  {
    "success": true,
    "memoryEntries": "number",
    "diskFiles": "number",
    "cacheTtlMs": "number",
    "diskTtlMs": "number",
    "lastPurge": "ISO8601 string"
  }
  ```
- Cache purge clears both memory and disk cache
- Third request after purge behaves as cache miss

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: Cache hit is significantly faster than miss, purge works correctly
- FAIL: No performance improvement or cache not working

**Test Environment:**
- Cache Directory: `backend/cache/`
- Memory Cache Max: 200 entries
- Disk Cache TTL: 24 hours

**Notes:**
- Tests both memory (fast) and disk (persistent) cache layers
- Verifies cache key generation based on URL + commit hash
- Tests admin endpoints require authentication

---

### TC-BE-005: Rate Limiting and Security Validation

**Test Case ID:** TC-BE-005  
**Test Case Name:** Verify Rate Limiting and Security Controls  
**Feature Under Test:** API Rate Limiting and Input Validation  
**Priority:** High  
**Test Type:** Security, Non-Functional  

**Preconditions:**
- Backend server is running
- Rate limit configured (default: 60 requests per 5 minutes)
- CORS configuration is set

**Test Data:**
- Valid GitHub URL
- Invalid GitHub URL: `https://malicious-site.com/fake-repo`
- Large payload: JSON > 20MB (if JSON_LIMIT allows)

**Test Steps:**
1. Send 61 rapid requests to `/api/analyze` within 5 minutes
2. Verify 61st request is rate-limited with 429 status
3. Send request with invalid GitHub URL
4. Verify 400 Bad Request with validation error
5. Send request with oversized JSON payload
6. Verify 413 Payload Too Large
7. Send request from unauthorized CORS origin
8. Verify CORS rejection
9. Test SQL injection attempt in GitHub URL parameter
10. Verify input sanitization prevents exploitation

**Expected Results:**
- Request #61 within window: HTTP 429 Too Many Requests
- Invalid GitHub URL: HTTP 400 with error message
- Oversized payload: HTTP 413 Payload Too Large
- Unauthorized CORS origin: CORS error (blocked by browser/proxy)
- SQL injection attempt: Safely sanitized, no execution
- Rate limit headers present:
  ```
  X-RateLimit-Limit: 60
  X-RateLimit-Remaining: 0
  X-RateLimit-Reset: <timestamp>
  ```

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: All security controls work as expected, attacks are prevented
- FAIL: Any security control is bypassed or fails

**Test Environment:**
- Rate Window: 5 minutes
- Rate Max: 60 requests
- JSON Limit: 20MB

**Notes:**
- Critical security test for production deployment
- Tests multiple attack vectors (rate limit abuse, injection, CORS bypass)
- Verifies defense-in-depth security layers

---

## Frontend Module Test Cases

### Test Suite: Frontend UI Components
**Module:** Frontend (Next.js/React)  
**Component Path:** `/frontend`  
**Testing Framework:** Jest + React Testing Library  
**Test Coverage Target:** 75%+

---

### TC-FE-001: HomePage Component Rendering and State Management

**Test Case ID:** TC-FE-001  
**Test Case Name:** Validate HomePage Component Initial Render  
**Feature Under Test:** HomePage Component UI and State  
**Priority:** High  
**Test Type:** Functional, UI  

**Preconditions:**
- Frontend application is running on port 3000
- Backend API is available
- React components are properly built

**Test Data:** None required for initial render

**Test Steps:**
1. Render HomePage component using React Testing Library
2. Verify all input fields are present (GitHub URL, Prompt)
3. Verify diagram type selector is rendered with all options
4. Verify control buttons are present (Generate, Clear, Toggle Options)
5. Verify initial state values:
   - `diagramType` = 'class'
   - `loading` = false
   - `error` = ''
   - `diagram` = ''
6. Simulate user interaction: type GitHub URL in input
7. Verify input value updates in component state
8. Simulate button click: Generate
9. Verify loading state transitions to true

**Expected Results:**
- All UI elements render without errors
- Input fields are functional and update state
- Diagram type dropdown contains 8 options: class, usecase, activity, sequence, state, component, communication, deployment
- Initial render time < 1 second
- No console errors or warnings
- State management works correctly

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: All UI elements render and state updates correctly
- FAIL: Missing elements, broken state, or errors in console

**Test Environment:**
- Browser: Chrome/Firefox/Safari latest versions
- Node.js: v18+
- React: v18+

**Notes:**
- Tests component mounting and initial render
- Verifies React hooks (useState, useEffect) work correctly
- Foundation for all other UI tests

---

### TC-FE-002: GitHub Repository Analysis via UI

**Test Case ID:** TC-FE-002  
**Test Case Name:** End-to-End GitHub Repository Analysis  
**Feature Under Test:** Repository Analysis User Workflow  
**Priority:** High  
**Test Type:** Integration, E2E  

**Preconditions:**
- Frontend running on port 3000
- Backend running on port 3001
- Python parser running on port 5000
- Valid test GitHub repository available

**Test Data:**
- GitHub URL: `https://github.com/octocat/Hello-World`
- Diagram Type: `class`

**Test Steps:**
1. Open browser and navigate to http://localhost:3000
2. Locate GitHub URL input field
3. Enter test GitHub URL
4. Select "Class Diagram" from diagram type dropdown
5. Click "Generate UML Diagram" button
6. Wait for loading spinner to appear
7. Wait for diagram to render (max 60 seconds)
8. Verify PlantUML diagram is displayed
9. Verify diagram contains classes and relationships
10. Test diagram controls (zoom, pan, reset)
11. Toggle "Show Raw Diagram" and verify PlantUML syntax is shown
12. Click "Clear" button and verify state is reset

**Expected Results:**
- Loading spinner appears immediately after clicking Generate
- Diagram renders successfully within 60 seconds
- PlantUML SVG diagram is visible and interactive
- Raw PlantUML syntax is valid and matches diagram
- Controls (zoom, pan) work smoothly
- Clear button resets all state
- No errors displayed to user
- No console errors

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: Complete workflow executes successfully with valid diagram
- FAIL: Any step fails, error occurs, or diagram doesn't render

**Test Environment:**
- Browser: Chrome 120+
- Screen Resolution: 1920x1080
- Network: Stable connection

**Notes:**
- Tests complete user journey from input to output
- Validates frontend-backend-python integration
- Critical path for main application feature

---

### TC-FE-003: Prompt-to-UML Generation Feature

**Test Case ID:** TC-FE-003  
**Test Case Name:** Validate Natural Language Prompt to UML Conversion  
**Feature Under Test:** AI-Powered Prompt-to-UML Generation  
**Priority:** High  
**Test Type:** Functional, Integration  

**Preconditions:**
- Frontend application is running
- Backend and Python parser are running
- Groq/Gemini API keys are configured
- User has not exceeded API rate limits

**Test Data:**
- Prompt: "Create a library management system with Book, Member, and Loan classes. Books can be borrowed by members."
- Diagram Type: `class`

**Test Steps:**
1. Navigate to HomePage
2. Switch to "Prompt" input tab/section
3. Enter natural language prompt in textarea
4. Select diagram type: "Class Diagram"
5. Click "Generate from Prompt" button
6. Monitor loading state
7. Wait for LLM processing (10-30 seconds)
8. Verify generated UML diagram appears
9. Verify diagram contains mentioned entities (Book, Member, Loan)
10. Change diagram type to "Sequence"
11. Verify diagram regenerates automatically with new type
12. Test error handling: enter empty prompt and submit
13. Verify error message is displayed

**Expected Results:**
- Prompt textarea accepts multi-line input
- Loading indicator shows during LLM processing
- Generated diagram contains classes mentioned in prompt
- Relationships between classes are logical and correct
- Auto-regeneration on type change works without re-prompting
- Empty prompt validation triggers error: "Prompt is required"
- Generated PlantUML syntax is valid
- Response time: 10-45 seconds depending on prompt complexity

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: Prompt generates valid, relevant UML diagram with auto-regeneration
- FAIL: Diagram is incorrect, irrelevant, or error occurs

**Test Environment:**
- LLM Service: Groq/Gemini API
- API Key: Valid and not rate-limited
- Network: Stable connection

**Notes:**
- Tests AI/LLM integration feature
- Validates prompt parsing and diagram generation logic
- Tests automatic re-generation on configuration changes

---

### TC-FE-004: PlantUML Diagram Rendering and Error Handling

**Test Case ID:** TC-FE-004  
**Test Case Name:** Validate PlantUML Diagram Component Rendering  
**Feature Under Test:** PlantUML SVG Rendering and Error Boundaries  
**Priority:** Medium  
**Test Type:** Functional, Error Handling  

**Preconditions:**
- PlantUMLDiagram component is properly imported
- PlantUML server/renderer is accessible
- Test PlantUML syntax is prepared (valid and invalid)

**Test Data:**
- Valid PlantUML:
  ```
  @startuml
  class Book {
    +title: String
    +author: String
  }
  @enduml
  ```
- Invalid PlantUML:
  ```
  @startuml
  class InvalidSyntax {
    +++broken
  @enduml
  ```

**Test Steps:**
1. Render PlantUMLDiagram component with valid syntax
2. Verify SVG renders successfully
3. Measure render time
4. Verify diagram is interactive (zoom, pan)
5. Render PlantUMLDiagram with invalid syntax
6. Verify error boundary catches rendering error
7. Verify error message is user-friendly
8. Test with empty diagram string
9. Verify fallback/placeholder is shown
10. Test with very large diagram (100+ classes)
11. Monitor performance and memory usage

**Expected Results:**
- Valid syntax: SVG renders within 2 seconds
- Diagram is crisp, clear, and properly formatted
- Zoom and pan controls work smoothly
- Invalid syntax: Error boundary prevents app crash
- Error message: "Diagram rendering failed: [details]"
- Empty diagram: Shows placeholder message
- Large diagram: Renders successfully (may take 5-10 seconds)
- No memory leaks or browser freezing
- Component handles errors gracefully without crashing parent

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: Valid diagrams render correctly, errors are handled gracefully
- FAIL: App crashes, errors are not caught, or rendering fails

**Test Environment:**
- Browser: Chrome/Firefox
- PlantUML Server: Local or online
- Component: PlantUMLDiagram.js

**Notes:**
- Tests core diagram rendering functionality
- Validates error boundary implementation
- Critical for user experience and stability

---

### TC-FE-005: Responsive Design and Browser Compatibility

**Test Case ID:** TC-FE-005  
**Test Case Name:** Verify Responsive Layout Across Devices and Browsers  
**Feature Under Test:** Responsive UI and Cross-Browser Support  
**Priority:** Medium  
**Test Type:** UI, Compatibility  

**Preconditions:**
- Frontend application is built and deployed
- Test devices/emulators are available
- Multiple browsers are installed

**Test Data:** Sample diagram generated for visual validation

**Test Steps:**
1. Open application in Chrome desktop (1920x1080)
2. Verify layout is proper, no overflow or broken elements
3. Open developer tools and switch to mobile view (375x667 - iPhone SE)
4. Verify responsive layout adjustments:
   - Input fields stack vertically
   - Buttons resize appropriately
   - Diagram viewer is scrollable
5. Test on Firefox desktop
6. Verify no browser-specific rendering issues
7. Test on Safari (if available)
8. Verify CSS compatibility
9. Test on Edge browser
10. Verify all features work consistently
11. Test on actual mobile device (Android/iOS)
12. Verify touch interactions work correctly
13. Test with browser zoom at 50%, 100%, 150%
14. Verify UI scales properly

**Expected Results:**
- Desktop (>1280px): Full layout with sidebar/controls
- Tablet (768-1279px): Adjusted layout, stacked controls
- Mobile (<768px): Fully stacked, touch-optimized
- All browsers render consistently (minor differences acceptable)
- No horizontal scrolling on mobile
- All interactive elements are touch-friendly (min 44x44px)
- Zoom levels do not break layout
- Fonts are readable at all sizes
- Images/diagrams scale appropriately

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: Application is usable on all tested devices and browsers
- FAIL: Layout breaks, features don't work, or severe visual issues

**Test Environment:**
- Browsers: Chrome 120+, Firefox 120+, Safari 17+, Edge 120+
- Devices: Desktop, Tablet, Mobile (physical and emulated)
- Screen Sizes: 320px - 2560px width

**Notes:**
- Tests responsive design implementation
- Validates cross-browser compatibility
- Ensures accessibility on various devices
- Critical for user adoption and satisfaction

---

## Python Parser Module Test Cases

### Test Suite: Python Parser Service
**Module:** Python Parser (Flask/Python)  
**Component Path:** `/python-parser`  
**Testing Framework:** pytest  
**Test Coverage Target:** 80%+

---

### TC-PP-001: Code Analysis for Multi-Language Repository

**Test Case ID:** TC-PP-001  
**Test Case Name:** Validate Multi-Language Code Analysis  
**Feature Under Test:** AST Parsing and Analysis  
**Priority:** High  
**Test Type:** Functional, Integration  

**Preconditions:**
- Python parser service is running on port 5000
- Test repository with Python, Java, TypeScript, C# files is prepared
- All language analyzers are properly configured

**Test Data:**
- Test Repository Structure:
  ```
  /test-repo
    /python
      - user.py (contains User class)
      - book.py (contains Book class)
    /java
      - Library.java (contains Library class)
    /typescript
      - api.ts (contains Express routes)
    /csharp
      - Service.cs (contains Service class)
  ```

**Test Steps:**
1. Prepare test repository with sample files
2. Send POST request to `/analyze` with test repo ZIP
3. Wait for analysis to complete
4. Parse response JSON
5. Verify `languages` array in meta contains: ["python", "java", "typescript", "csharp"]
6. Verify `classes` array contains entries for User, Book, Library, Service
7. Check class properties:
   - Each class has `name`, `language`, `methods`, `fields`
   - Fields have correct types
   - Methods have correct signatures
8. Verify `relations` array contains detected relationships
9. Check meta statistics:
   - `files_scanned` >= 5
   - `classes_found` >= 4
10. Verify language-specific syntax is correctly parsed

**Expected Results:**
- Response status: 200 OK
- Schema structure:
  ```json
  {
    "schema": {
      "classes": [
        {
          "name": "User",
          "language": "python",
          "fields": [...],
          "methods": [...],
          "file": "/python/user.py"
        },
        ...
      ],
      "relations": [
        {
          "from": "Library",
          "to": "Book",
          "type": "association|composition|inheritance",
          "source": "ast|ai"
        }
      ],
      "meta": {
        "system": "test-repo",
        "languages": ["python", "java", "typescript", "csharp"],
        "classes_found": 4,
        "files_scanned": 5
      }
    }
  }
  ```
- All languages are detected and parsed correctly
- No parsing errors or exceptions
- Response time < 30 seconds

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: All languages parsed correctly with accurate class extraction
- FAIL: Missing languages, incorrect parsing, or errors

**Test Environment:**
- Python: 3.9+
- Language Analyzers: Python, Java, TypeScript, C#, C++
- Parser Libraries: ast, javalang, typescript (tree-sitter)

**Notes:**
- Tests core parsing functionality across multiple languages
- Validates AST analysis and relationship detection
- Critical for polyglot repository support

---

### TC-PP-002: PlantUML Generation from Analysis Schema

**Test Case ID:** TC-PP-002  
**Test Case Name:** Validate PlantUML Syntax Generation  
**Feature Under Test:** PlantUML Generator from Schema  
**Priority:** High  
**Test Type:** Functional  

**Preconditions:**
- Python parser service is running
- Valid analysis schema is available (from TC-PP-001)
- PlantUML generator module is loaded

**Test Data:**
- Input Schema:
  ```json
  {
    "classes": [
      {
        "name": "Book",
        "fields": [
          {"name": "title", "type": "String", "visibility": "public"}
        ],
        "methods": [
          {"name": "getTitle", "returnType": "String", "visibility": "public"}
        ]
      }
    ],
    "relations": [
      {"from": "Library", "to": "Book", "type": "composition"}
    ]
  }
  ```
- Diagram Type: `class`

**Test Steps:**
1. Send POST request to `/generate-plantuml`
2. Include schema and diagram_type in request body
3. Parse response
4. Verify PlantUML syntax is returned
5. Validate PlantUML structure:
   - Starts with `@startuml`
   - Ends with `@enduml`
   - Contains class definitions
   - Contains relationship arrows
6. Test with different diagram types: sequence, usecase, state
7. Verify syntax adapts to diagram type
8. Test with language_filter parameter
9. Verify only specified languages are included
10. Test with empty schema
11. Verify appropriate error handling

**Expected Results:**
- Response status: 200 OK
- Response structure:
  ```json
  {
    "plantuml": "@startuml\nclass Book {\n  +title: String\n  +getTitle(): String\n}\nLibrary *-- Book\n@enduml",
    "diagram_type": "class",
    "statistics": {
      "total_classes": 1,
      "total_relations": 1,
      "languages": ["python"]
    },
    "success": true
  }
  ```
- PlantUML syntax is valid and compilable
- Different diagram types produce appropriate syntax
- Language filtering works correctly
- Empty schema returns error with status 400

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: Valid PlantUML generated for all diagram types
- FAIL: Invalid syntax, missing elements, or generation fails

**Test Environment:**
- PlantUML Generator: plantuml_generator.py
- Supported Types: class, sequence, usecase, state, activity, component

**Notes:**
- Tests PlantUML syntax generation logic
- Validates diagram type-specific generation
- Critical for diagram rendering pipeline

---

### TC-PP-003: LLM-Powered Prompt to UML Generation

**Test Case ID:** TC-PP-003  
**Test Case Name:** Validate AI-Generated UML from Natural Language  
**Feature Under Test:** LLM Integration for Prompt-to-UML  
**Priority:** High  
**Test Type:** Integration, AI  

**Preconditions:**
- Python parser service is running
- Groq/Gemini API key is configured in environment
- LLM service is reachable and not rate-limited

**Test Data:**
- Test Prompts:
  1. "Create a shopping cart system with Product, Cart, and Order classes"
  2. "Design a user authentication system with login sequence diagram"
  3. "Model a state diagram for an order processing workflow"

**Test Steps:**
1. Send POST request to `/uml-from-prompt`
2. Include prompt, diagramType, and format in request body
3. Monitor request duration
4. Parse response
5. Verify diagram syntax is returned
6. Validate diagram relevance to prompt
7. Test with different diagram types
8. Verify diagram type adaptation
9. Test with invalid prompt (empty string)
10. Verify validation error
11. Test with unsupported diagram type
12. Verify error handling
13. Test with style preferences
14. Verify style is applied to diagram

**Expected Results:**
- Response status: 200 OK
- Response structure:
  ```json
  {
    "diagram": "@startuml\nclass Product {...}\nclass Cart {...}\n...\n@enduml",
    "diagramType": "class",
    "format": "plantuml"
  }
  ```
- Diagram contains entities mentioned in prompt
- Relationships are logical and relevant
- Diagram type matches request
- Empty prompt: 400 Bad Request with validation error
- Unsupported type: 400 Bad Request
- Response time: 5-30 seconds (depends on LLM)
- Generated diagram is syntactically valid

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: LLM generates relevant, valid diagrams for all prompt types
- FAIL: Irrelevant diagrams, syntax errors, or LLM failure

**Test Environment:**
- LLM Service: Groq (Llama) or Google Gemini
- API Key: Valid and within rate limits
- Timeout: 60 seconds

**Notes:**
- Tests AI/LLM integration
- Validates prompt parsing and diagram synthesis
- Subject to LLM availability and rate limits
- Quality may vary based on prompt clarity

---

### TC-PP-004: Security Validation and Input Sanitization

**Test Case ID:** TC-PP-004  
**Test Case Name:** Verify Security Controls and Input Validation  
**Feature Under Test:** Security Layer (Path Traversal, ZIP Bomb, URL Validation)  
**Priority:** Critical  
**Test Type:** Security, Negative Testing  

**Preconditions:**
- Python parser service is running
- Security module is properly configured
- Test malicious payloads are prepared

**Test Data:**
- Malicious GitHub URLs:
  - `https://evil.com/../../../etc/passwd`
  - `https://github.com/user/repo.git; rm -rf /`
  - `file:///etc/passwd`
- Malicious ZIP:
  - ZIP with path traversal: `../../etc/passwd`
  - ZIP bomb (highly compressed, expands to GB)
  - ZIP with symlinks pointing outside extraction directory

**Test Steps:**
1. Test malicious GitHub URL #1 (path traversal)
2. Send POST to `/analyze` with URL
3. Verify request is rejected with 400 Bad Request
4. Verify error message: "Invalid GitHub URL"
5. Test command injection attempt
6. Verify input is sanitized, no command execution
7. Upload ZIP with path traversal
8. Verify extraction is blocked or paths are sanitized
9. Upload ZIP bomb
10. Verify extraction fails with size limit error
11. Test with extremely large repository (>500MB)
12. Verify timeout or size limit is enforced
13. Test SQL injection in prompt field
14. Verify no database access or execution
15. Test XSS in prompt response
16. Verify output is properly escaped

**Expected Results:**
- Malicious GitHub URLs: 400 Bad Request, no code execution
- Path traversal in ZIP: Blocked or sanitized
- ZIP bomb: 413 Payload Too Large or extraction aborted
- Large repository: 408 Request Timeout after configured limit
- SQL injection: No database access, input sanitized
- XSS: Output is escaped, no script execution
- All security errors are logged
- No data leakage in error messages
- System remains stable, no crashes

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: All malicious inputs are blocked or sanitized
- FAIL: Any security control is bypassed or vulnerability is exploited

**Test Environment:**
- Security Module: security.py
- Validation Functions: validate_github_url, sanitize_file_path
- Resource Limits: Configured in environment

**Notes:**
- Critical security test for production deployment
- Tests defense against common attack vectors
- Validates input sanitization and validation layers
- Must PASS before production release

---

### TC-PP-005: Performance and Scalability Under Load

**Test Case ID:** TC-PP-005  
**Test Case Name:** Validate Performance Under Concurrent Load  
**Feature Under Test:** Service Performance and Scalability  
**Priority:** Medium  
**Test Type:** Performance, Load Testing  

**Preconditions:**
- Python parser service is running
- Load testing tool is configured (e.g., locust, JMeter)
- Test repositories of various sizes are prepared

**Test Data:**
- Small repository: ~10 files, 5 classes
- Medium repository: ~50 files, 30 classes
- Large repository: ~200 files, 150 classes
- Concurrent users: 10, 50, 100

**Test Steps:**
1. Configure load testing tool with test scenarios
2. Scenario 1: 10 concurrent users analyzing small repos
3. Monitor response times and success rate
4. Scenario 2: 50 concurrent users analyzing medium repos
5. Monitor CPU, memory, and response times
6. Scenario 3: 100 concurrent users mixed repos (small, medium, large)
7. Monitor system resources and error rates
8. Measure average response time for each scenario
9. Identify bottlenecks (CPU, memory, I/O, LLM API)
10. Test memory usage over extended period (1 hour)
11. Verify no memory leaks
12. Test cache effectiveness under load
13. Measure cache hit rate and performance improvement

**Expected Results:**
- Scenario 1 (10 users, small repos):
  - Average response time: <10 seconds
  - Success rate: >99%
  - CPU usage: <50%
  - Memory usage: <2GB
- Scenario 2 (50 users, medium repos):
  - Average response time: <25 seconds
  - Success rate: >95%
  - CPU usage: <80%
  - Memory usage: <4GB
- Scenario 3 (100 users, mixed):
  - Average response time: <45 seconds
  - Success rate: >90%
  - CPU usage: <90%
  - Memory usage: <6GB
- No memory leaks over 1 hour test
- Cache hit rate: >60% for repeated requests
- No service crashes or unhandled exceptions
- Graceful degradation under extreme load

**Actual Results:** _(To be filled during test execution)_

**Pass/Fail Criteria:**
- PASS: All scenarios meet performance targets, no crashes
- FAIL: Performance degrades below targets or service crashes

**Test Environment:**
- Load Testing Tool: Locust/JMeter/k6
- Server: Production-like environment
- Resources: 4 CPU cores, 8GB RAM

**Notes:**
- Tests service performance under realistic load
- Identifies scalability limits and bottlenecks
- Validates resource usage and stability
- Important for capacity planning

---

## Test Execution Summary

### Test Metrics
- **Total Test Cases:** 15 (5 Backend + 5 Frontend + 5 Python Parser)
- **Priority Breakdown:**
  - High Priority: 11 test cases
  - Medium Priority: 3 test cases
  - Critical Priority: 1 test case

### Test Coverage Areas
- **Functional Testing:** 11 test cases
- **Security Testing:** 3 test cases
- **Performance Testing:** 2 test cases
- **Integration Testing:** 6 test cases
- **UI Testing:** 3 test cases

### Execution Guidelines
1. Execute all High and Critical priority tests first
2. Run tests in isolated environments to avoid interference
3. Document all failures with detailed logs and screenshots
4. Re-test failed cases after fixes are applied
5. Maintain test data and environment consistency
6. Update test cases when features change

### Reporting
- Test results should be documented in IEEE 829 Test Log format
- Defects should be logged with severity and priority
- Test summary reports should be generated after each cycle
- Traceability matrix should link test cases to requirements

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-13 | Automated Generation | Initial test case documentation |

---

**End of Test Case Documentation**
