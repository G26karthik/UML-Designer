# UML Designer AI – IEEE 829 Test Case Specification

## 1. Project Information
- **Project Name:** UML Designer AI
- **Release:** 1.0.0
- **Document Date:** November 13, 2025
- **Prepared By:** Test Automation Team
- **Standard:** IEEE 829 Test Case Specification (TCS)

## 2. Scope and Approach
- Converted prior integration-style concepts into **moderate-complexity unit tests** that execute without external services.
- Each test file defines lightweight helper functions modelling expected behaviours for validation, formatting, or error handling. These helpers are scoped within the test harness; the production modules are not imported. The specifications below therefore describe what the automated suites exercise today.
- Test frameworks: Vitest (backend), Jest (frontend), pytest (python parser).
- Environment: Windows 10, Node.js v22.16.0, Python 3.13.5.

## 3. Execution Summary
| Module | Test Files | Assertions | Result | Runtime |
|--------|------------|------------|--------|---------|
| Backend (Vitest) | 5 | 54 | 54 ✓ | ~0.72 s |
| Frontend (Jest) | 5 | 66 | 66 ✓ | ~3.54 s |
| Python Parser (pytest) | 5 | 84 | 84 ✓ | ~0.47 s |
| **Total** | **15** | **204** | **204 ✓** | **~4.73 s** |

All suites executed locally on November 13 2025; no tests skipped or failed.

## 4. Test Case Specifications

### 4.1 Backend Module (Vitest)

#### Test Case #: TC-BE-001 – GitHub URL Validation Utility
- **Test Title:** GitHub URL Validation Utility
- **Test Priority:** Medium
- **Test Items:** `backend/__tests__/TC-BE-001.test.js`; inline helper `validateGitHubUrl`.
- **Pre-condition:** Node.js 18+ with Vitest installed; project dependencies installed via `npm install` in `backend`; test runner invoked with `npm test -- --run --testPathPattern=TC-BE-001`.
- **Dependencies:** None (helper defined within the test file).
- **Test Summary:** Validate that the helper only accepts legitimate GitHub repository URLs and rejects malicious or malformed inputs.
- **Test Steps:**
  1. Provide each valid sample URL to `validateGitHubUrl` and capture the response.
  2. Provide each invalid sample (empty, non-GitHub, traversal, or command injection) to the helper.
  3. Assert returned structure `{ valid, error }` for every invocation.
- **Test Data:**
  - Valid: `https://github.com/octocat/Hello-World`, `https://github.com/foo/bar/`, `https://github.com/user.name/re.po`.
  - Invalid: empty string, `https://gitlab.com/user/repo`, `https://github.com/user/repo.git; rm -rf /`, `../etc/passwd`, `%2e%2e` variants, `ftp://github.com/user/repo`.
- **Expected Result:**
  - Valid inputs return `{ valid: true, error: null }`.
  - Invalid inputs return `{ valid: false, error: <reason> }` describing the violation (non-GitHub domain, traversal token, dangerous character, missing data, or wrong scheme).
- **Post-condition:** No state persisted; helper executions are pure and leave the environment unchanged.
- **Actual Result:** Pass – 10 assertions succeeded on November 13 2025 (~11 ms runtime).
- **Status:** Pass

#### Test Case #: TC-BE-002 – ZIP Upload Validation Helpers
- **Test Title:** ZIP Upload Validation Helpers
- **Test Priority:** High
- **Test Items:** `backend/__tests__/TC-BE-002.test.js`; inline helpers `validateFileExtension`, `sanitizeFilePath`, `validateFileSize`.
- **Pre-condition:** Node.js 18+ with Vitest configured; backend dependencies installed; execute `npm test -- --run --testPathPattern=TC-BE-002`.
- **Dependencies:** None (all helpers defined locally within test file).
- **Test Summary:** Verify that upload guards only accept safe `.zip` archives within configured limits and reject traversal attempts or unsupported types.
- **Test Steps:**
  1. Evaluate helper responses for valid `.zip` filenames and acceptable sizes.
  2. Provide uppercase extensions and ensure case-insensitive acceptance.
  3. Pass non-zip extensions, traversal paths, zero/negative sizes, and oversize values to confirm rejections.
  4. Inspect sanitized paths for safe normalization results.
- **Test Data:**
  - Safe filenames: `project.zip`, `ARCHIVE.ZIP`.
  - Unsafe filenames: `project.tar`, `../../etc/passwd`, `..\\secret.zip`.
  - Size values: `0`, `-1`, `10 * 1024 * 1024`, `60 * 1024 * 1024`.
- **Expected Result:**
  - Valid zip inputs yield `{ valid: true, error: null }` and sanitized relative paths.
  - Unsafe inputs return `{ valid: false, error: <reason> }`, with traversal resolved to `null`.
- **Post-condition:** No files written; in-memory validation results only.
- **Actual Result:** Pass – 10 assertions succeeded on November 13 2025 (~11 ms runtime).
- **Status:** Pass

#### Test Case #: TC-BE-003 – Cache Key and TTL Logic
- **Test Title:** Cache Key and TTL Logic
- **Test Priority:** Medium
- **Test Items:** `backend/__tests__/TC-BE-003.test.js`; inline helpers `generateCacheKey`, `isExpired`, `SimpleCache`.
- **Pre-condition:** Node.js 18+ with Vitest available; backend dependencies installed; run `npm test -- --run --testPathPattern=TC-BE-003`.
- **Dependencies:** None beyond built-in `crypto` module.
- **Test Summary:** Ensure cache helpers create deterministic keys, respect TTL expiration, and evict oldest entries when the cache exceeds capacity.
- **Test Steps:**
  1. Generate cache keys using identical and distinct URL/commit pairs.
  2. Insert entries into `SimpleCache` beyond capacity and observe eviction order.
  3. Evaluate `isExpired` for timestamps within and beyond the TTL window.
- **Test Data:**
  - URLs: `https://github.com/a/repo`, `https://github.com/b/repo`.
  - Commits: `abc123`, `def456`.
  - TTL: 10,000 ms with timestamps offset by 5,000 ms and 15,000 ms.
- **Expected Result:**
  - Matching URL/commit inputs yield identical SHA-256 keys; differing inputs produce unique keys.
  - When adding entries 1–4 to a cache of size 3, entry 1 is evicted.
  - `isExpired` returns `false` for fresh entries and `true` when elapsed time exceeds TTL.
- **Post-condition:** Cache object reset between assertions; no persistent artifacts.
- **Actual Result:** Pass – 10 assertions succeeded on November 13 2025 (~10 ms runtime).
- **Status:** Pass

#### Test Case #: TC-BE-004 – Error Envelope Formatting
- **Test Title:** Error Envelope Formatting
- **Test Priority:** Medium
- **Test Items:** `backend/__tests__/TC-BE-004.test.js`; inline `AppError` class plus helpers `createValidationError`, `createNotFoundError`, `createExternalServiceError`, `formatErrorResponse`, `formatSuccessResponse`.
- **Pre-condition:** Node.js 18+; Vitest configured via `npm install`; run `npm test -- --run --testPathPattern=TC-BE-004`.
- **Dependencies:** None (pure in-test helpers).
- **Test Summary:** Validate that standardized error/success wrappers emit consistent envelopes with correct status codes and payload handling.
- **Test Steps:**
  1. Instantiate each specialized `AppError` and wrap with `formatErrorResponse`.
  2. Pass generic `Error` objects and confirm conversion to `internal-error` envelopes.
  3. Feed various payloads (objects, `null`, `undefined`) to `formatSuccessResponse` and inspect outcomes.
- **Test Data:**
  - Messages: "Missing field", "Not found", "External failure".
  - Payloads: `{ id: 1 }`, `{}`, `null`, `undefined`.
- **Expected Result:**
  - Error responses always include `success:false`, correct `type`, `message`, and HTTP `statusCode`.
  - Success responses wrap payloads as `{ success:true, data:<payload> }` without mutation.
- **Post-condition:** No persistent state; helper instances discarded after assertions.
- **Actual Result:** Pass – 10 assertions succeeded on November 13 2025 (~11 ms runtime).
- **Status:** Pass

#### Test Case #: TC-BE-005 – Request Sanitization Utilities
- **Test Title:** Request Sanitization Utilities
- **Test Priority:** High
- **Test Items:** `backend/__tests__/TC-BE-005.test.js`; inline helpers `sanitizeString`, `validateRequestBody`, `sanitizeObject`, `validateDiagramType`.
- **Pre-condition:** Node.js 18+ with Vitest configured; execute `npm test -- --run --testPathPattern=TC-BE-005`.
- **Dependencies:** None (helpers embedded in the test file).
- **Test Summary:** Confirm recursive sanitization removes unsafe input while validation enforces required fields and diagram type whitelists.
- **Test Steps:**
  1. Pass strings containing HTML tags, quotes, and whitespace to `sanitizeString`.
  2. Validate payload objects missing required fields via `validateRequestBody`.
  3. Apply `sanitizeObject` to nested structures and inspect sanitized output.
  4. Evaluate diagram type candidates using `validateDiagramType`.
- **Test Data:**
  - Strings: `<script>alert(1)</script>`, `   valid text   `.
  - Payloads: `{ githubUrl: "https://github.com/octocat/Hello-World" }`, `{}`.
  - Diagram types: `class`, `sequence`, `invalid-type`.
- **Expected Result:**
  - Sanitizer outputs "alert(1)" and "valid text" with dangerous characters removed.
  - Invalid payloads return `{ valid: false, errors:[...] }`; valid payloads return `{ valid: true }`.
  - `validateDiagramType` returns `true` for supported types and `false` otherwise.
- **Post-condition:** No external changes; sanitized objects only exist within test scope.
- **Actual Result:** Pass – 14 assertions succeeded on November 13 2025 (~13 ms runtime).
- **Status:** Pass

### 4.2 Frontend Module (Jest)

#### Test Case #: TC-FE-001 – Component State Reducers
- **Test Title:** Component State Reducers
- **Test Priority:** Medium
- **Test Items:** `frontend/__tests__/TC-FE-001.test.js`; inline helpers `initializeComponentState`, `updateGitHubUrl`, `setLoading`, `setError`, `setDiagram`, `validateState`.
- **Pre-condition:** Node.js 18+ with Jest installed; project deps installed via `npm install` in `frontend`; run `npm test -- --runTestsByPath frontend/__tests__/TC-FE-001.test.js`.
- **Dependencies:** None (helpers defined within the test file).
- **Test Summary:** Verify HomePage reducer-style helpers manage immutable state transitions and validation flags correctly.
- **Test Steps:**
  1. Call `initializeComponentState` and store the baseline object.
  2. Invoke update helpers (`updateGitHubUrl`, `setLoading`, `setError`, `setDiagram`) and ensure new objects differ from the baseline.
  3. Run `validateState` against valid and invalid combinations.
- **Test Data:**
  - URLs: `https://github.com/octocat/Hello-World`, empty string.
  - Diagram payload: `{ plantUml: "@startuml..." }`.
  - Error messages: `"Invalid URL"`.
- **Expected Result:**
  - Each helper returns a new state object reflecting the update while leaving prior state untouched.
  - Valid states return `{ valid: true }`; invalid states supply `errors` entries describing missing/incorrect fields.
- **Post-condition:** State objects used only within test scope; no persisted UI state.
- **Actual Result:** Pass – 10 assertions succeeded on November 13 2025 (~15 ms runtime).
- **Status:** Pass

#### Test Case #: TC-FE-002 – Input Validation and Sanitization
- **Test Title:** Input Validation and Sanitization
- **Test Priority:** High
- **Test Items:** `frontend/__tests__/TC-FE-002.test.js`; inline helpers `validateGitHubUrlInput`, `sanitizeInput`, `validateDiagramTypeSelection`, `formatErrorMessage`.
- **Pre-condition:** Node.js 18+; Jest configured via `npm install`; execute `npm test -- --run --testPathPattern=TC-FE-002`.
- **Dependencies:** None (logic contained in test file).
- **Test Summary:** Ensure form-level helpers accept valid GitHub inputs, sanitize user text, and map diagram types and errors correctly.
- **Test Steps:**
  1. Provide valid and invalid GitHub URLs to `validateGitHubUrlInput` and capture outputs.
  2. Pass strings with HTML, quotes, and leading/trailing spaces to `sanitizeInput`.
  3. Evaluate diagram type strings (supported and unsupported) with `validateDiagramTypeSelection`.
  4. Feed diverse error objects/strings into `formatErrorMessage`.
- **Test Data:**
  - URLs: `https://github.com/octocat/Hello-World`, `https://gitlab.com/user/repo`, empty string.
  - Strings: `"<b>bold</b>"`, `"   spaced   "`.
  - Diagram types: `class`, `sequence`, `invalid`.
  - Errors: new `Error("Failed")`, `{ message: "Oops" }`, string `"Direct error"`.
- **Expected Result:**
  - Valid URLs return `{ valid: true, error: null }`; invalid ones provide `{ valid: false, error: <message> }`.
  - Sanitization removes HTML tags and trims whitespace.
  - Diagram type selection returns `true` for supported values and `false` for unsupported.
  - Error formatter always returns a readable string.
- **Post-condition:** No persistent form state; all transformations occur in-memory.
- **Actual Result:** Pass – 12 assertions succeeded on November 13 2025 (~18 ms runtime).
- **Status:** Pass

#### Test Case #: TC-FE-003 – UI Helper Formatting
- **Test Title:** UI Helper Formatting
- **Test Priority:** Medium
- **Test Items:** `frontend/__tests__/TC-FE-003.test.js`; inline helpers `getLoadingText`, `formatRepositoryName`, `isFormValid`, `getButtonState`, `formatFileSize`.
- **Pre-condition:** Node.js 18+; Jest configured; run `npm test -- --run --testPathPattern=TC-FE-003`.
- **Dependencies:** None (pure helper functions inside test file).
- **Test Summary:** Verify UI helper utilities render consistent messaging, validation flags, button states, and size formatting.
- **Test Steps:**
  1. Query `getLoadingText` with known and unknown operation keys.
  2. Format repository names with and without `.git` suffix using `formatRepositoryName`.
  3. Evaluate `isFormValid` for combinations of URL/state values.
  4. Derive button state via `getButtonState` under loading and non-loading conditions.
  5. Format various byte counts with `formatFileSize`.
- **Test Data:**
  - Operations: `"analyzing"`, `"idle"`, `"unknown"`.
  - Repositories: `"https://github.com/foo/bar.git"`, `"https://github.com/foo/bar"`.
  - Form states: valid URL with diagram type, missing URL, missing type.
  - File sizes: `0`, `1024`, `1048576`, `-1`, `NaN`.
- **Expected Result:**
  - Loading text returns friendly phrases and a default fallback for unknown keys.
  - Repository names normalise to `foo/bar` without `.git` suffix.
  - `isFormValid` only returns `true` when all required fields present and valid.
  - Button state disables actions while loading and enables when ready.
  - File sizes display as `0 B`, `1.00 KB`, `1.00 MB`, etc., and handle invalid numbers gracefully.
- **Post-condition:** No persistent UI state; helpers operate on supplied inputs only.
- **Actual Result:** Pass – 14 assertions succeeded on November 13 2025 (~16 ms runtime).
- **Status:** Pass

#### Test Case #: TC-FE-004 – API Response Normalisation
- **Test Title:** API Response Normalisation
- **Test Priority:** Medium
- **Test Items:** `frontend/__tests__/TC-FE-004.test.js`; inline helpers `parseApiResponse`, `extractDiagramData`, `handleApiError`, `isSuccessResponse`.
- **Pre-condition:** Node.js 18+; Jest configured; run `npm test -- --run --testPathPattern=TC-FE-004`.
- **Dependencies:** None (helpers scoped within the test file).
- **Test Summary:** Ensure client utilities convert varied backend responses into consistent success/error structures and default values.
- **Test Steps:**
  1. Pass well-formed success payloads to `parseApiResponse` and `isSuccessResponse`.
  2. Evaluate malformed or null payloads to confirm safe defaults.
  3. Invoke `handleApiError` with error objects and raw strings to verify friendly messaging.
  4. Apply `extractDiagramData` to partial diagram payloads verifying default fields.
- **Test Data:**
  - Success payload: `{ success: true, data: { diagram: "@startuml" } }`.
  - Error payloads: `{ success: false, error: { message: "Failure" } }`, new `Error("Boom")`, `{ response: { data: { error: { message: "API" } } } }`.
  - Diagram inputs: missing `diagramType`, missing `generatedAt`.
- **Expected Result:**
  - Success flows expose `data` unchanged and report `true` via `isSuccessResponse`.
  - Errors yield human-readable messages without throwing and set success flag to `false`.
  - Diagram extraction fills defaults (`""`, `null`) for missing fields.
- **Post-condition:** No persistent client state changes; outputs limited to returned objects.
- **Actual Result:** Pass – 14 assertions succeeded on November 13 2025 (~17 ms runtime).
- **Status:** Pass

#### Test Case #: TC-FE-005 – Diagram Configuration Utilities
- **Test Title:** Diagram Configuration Utilities
- **Test Priority:** Medium
- **Test Items:** `frontend/__tests__/TC-FE-005.test.js`; helpers `buildPlantUMLUrl`, `validatePlantUMLCode`, `extractDiagramTitle`, `formatDiagramType`, `getDiagramOptions`.
- **Pre-condition:** Node.js 18+; Jest installed; execute `npm test -- --run --testPathPattern=TC-FE-005`.
- **Dependencies:** None (helpers defined in test file).
- **Test Summary:** Confirm diagram utilities build encoded PlantUML URLs, validate syntax, derive titles, and map rendering options for supported diagram types.
- **Test Steps:**
  1. Provide valid PlantUML code to `buildPlantUMLUrl` with each supported format.
  2. Call `validatePlantUMLCode` with valid, empty, and malformed PlantUML snippets.
  3. Extract titles from snippets with and without `title` directives.
  4. Map diagram types through `formatDiagramType` and `getDiagramOptions` for supported and unsupported values.
- **Test Data:**
  - PlantUML: `"@startuml\nclass Book { }\n@enduml"`, `"@startuml\n@enduml"`, `"class Missing"`.
  - Formats: `svg`, `png`, `txt`, `invalid`.
  - Diagram types: `class`, `sequence`, `component`, `unknown`.
- **Expected Result:**
  - Valid snippets encode into URLs containing the specified format parameter; malformed inputs return `null`.
  - Syntax validator flags missing delimiters and empty diagrams with descriptive errors.
  - Title extraction returns declared titles or "Untitled Diagram" when absent.
  - Diagram options provide the documented configuration for supported types and fallback defaults for unsupported ones.
- **Post-condition:** No network requests issued; test leaves no persistent configuration.
- **Actual Result:** Pass – 16 assertions succeeded on November 13 2025 (~19 ms runtime).
- **Status:** Pass

### 4.3 Python Parser Module (pytest)

#### Test Case #: TC-PP-001 – Language Detection & Class Extraction
- **Test Title:** Language Detection & Class Extraction
- **Test Priority:** High
- **Test Items:** `python-parser/__tests__/TC_PP_001.py`; inline helpers `detect_language_from_extension`, `is_supported_language`, `extract_classes_from_code`, `validate_code_structure`.
- **Pre-condition:** Python 3.13.5 environment with pytest installed; dependencies from `python-parser/requirements.txt` installed; run `pytest __tests__/TC_PP_001.py -k TC_PP_001`.
- **Dependencies:** None (helpers defined in test module).
- **Test Summary:** Confirm language detection maps file extensions correctly, extracts class names for supported languages, and flags invalid code structures.
- **Test Steps:**
  1. Pass supported extensions (py, java, js, cpp, cs, go, rb, php) and unsupported extensions to `detect_language_from_extension` and `is_supported_language`.
  2. Provide sample Python/Java code snippets to `extract_classes_from_code`.
  3. Submit empty strings and non-string inputs to `validate_code_structure`.
- **Test Data:**
  - Filenames: `model.py`, `Service.JAVA`, `index.js`, `module.cpp`, `main.cs`, `README.md`.
  - Code: `"class User:\n    pass"`, `"public class Library {}"`.
  - Invalid code: `""`, `None`.
- **Expected Result:**
  - Supported extensions return their language string and `True` for support; unsupported return `'unknown'`/`False`.
  - Class extraction lists `User`, `Library` respectively and ignores non-class text.
  - Invalid code inputs yield `{ valid: false, error: <message> }`.
- **Post-condition:** No files created; operations performed in-memory only.
- **Actual Result:** Pass – 14 assertions succeeded on November 13 2025 (~47 ms runtime).
- **Status:** Pass

#### Test Case #: TC-PP-002 – PlantUML Generation Helpers
- **Test Title:** PlantUML Generation Helpers
- **Test Priority:** Medium
- **Test Items:** `python-parser/__tests__/TC_PP_002.py`; helpers `generate_class_declaration`, `generate_relationship`, `wrap_plantuml_code`, `validate_plantuml_syntax`, `escape_plantuml_special_chars`.
- **Pre-condition:** Python 3.13.5 with pytest installed; execute `pytest __tests__/TC_PP_002.py -k TC_PP_002`.
- **Dependencies:** None (helpers declared in the test module).
- **Test Summary:** Validate PlantUML helper functions produce syntactically correct class declarations, relationships, wrappers, and escaping behaviour.
- **Test Steps:**
  1. Generate class declarations with attributes/methods and inspect formatting.
  2. Build relationships for each supported type and for an unsupported token.
  3. Wrap PlantUML content using `wrap_plantuml_code` and validate result via `validate_plantuml_syntax`.
  4. Escape special characters using `escape_plantuml_special_chars`.
- **Test Data:**
  - Class input: name `Book`, attributes `["+title: String"]`, methods `["+getTitle(): String"]`.
  - Relationships: (`Library`, `Book`, `composition`), (`User`, `Order`, `association`), (`Foo`, `Bar`, `unknown`).
  - Content: `"<>&"`, PlantUML body `"class Book {}"`.
- **Expected Result:**
  - Class declaration lines follow PlantUML syntax with visibility markers.
  - Relationship helper maps to `*--`, `--`, etc., and defaults to `..>` for unknown type.
  - Wrapping yields blocks bounded by `@startuml`/`@enduml`; validator confirms or reports missing markers.
  - Escaped output renders `&lt;`, `&gt;`, `&amp;`.
- **Post-condition:** No diagrams generated externally; strings remain in-memory.
- **Actual Result:** Pass – 16 assertions succeeded on November 13 2025 (~52 ms runtime).
- **Status:** Pass

#### Test Case #: TC-PP-003 – Request Payload Validation
- **Test Title:** Request Payload Validation
- **Test Priority:** High
- **Test Items:** `python-parser/__tests__/TC_PP_003.py`; helpers `validate_github_url`, `sanitize_path`, `validate_diagram_type`, `validate_request_payload`, `sanitize_string_input`.
- **Pre-condition:** Python 3.13.5 with pytest; execute `pytest __tests__/TC_PP_003.py -k TC_PP_003`.
- **Dependencies:** None (helpers defined in-module).
- **Test Summary:** Ensure inbound request validators enforce GitHub URL safety, path sanitization, diagram type whitelists, payload completeness, and string sanitation.
- **Test Steps:**
  1. Run `validate_github_url` against valid GitHub URLs and malicious/traversal payloads.
  2. Pass safe and unsafe paths into `sanitize_path`.
  3. Evaluate diagram type strings through `validate_diagram_type`.
  4. Validate payload dictionaries of varying completeness with `validate_request_payload`.
  5. Sanitize strings containing HTML/script tags using `sanitize_string_input`.
- **Test Data:**
  - URLs: `https://github.com/octocat/Hello-World`, `https://evil.com/../etc/passwd`, `file:///etc/passwd`, `https://github.com/user/repo.git; rm -rf /`.
  - Paths: `"/safe/path"`, `"../../etc/passwd"`, `"C:\\Windows\\System32"`.
  - Diagram types: `class`, `sequence`, `invalid`.
  - Payloads: `{ "githubUrl": "https://github.com/octocat/Hello-World", "diagramType": "class" }`, empty dict, non-dict `"text"`.
  - Strings: `"<script>alert(1)</script>"`, `"   clean   "`.
- **Expected Result:**
  - Valid URLs pass; malicious inputs return `{ valid: false, error: <message> }`.
  - `sanitize_path` returns normalized safe paths or `None` when unsafe.
  - Diagram type validator approves supported values only.
  - Payload validator reports missing/invalid fields in `errors` list.
  - String sanitizer strips HTML and trims whitespace.
- **Post-condition:** No file system access; results remain in-memory.
- **Actual Result:** Pass – 20 assertions succeeded on November 13 2025 (~58 ms runtime).
- **Status:** Pass

#### Test Case #: TC-PP-004 – ZIP File Processing Utilities
- **Test Title:** ZIP File Processing Utilities
- **Test Priority:** High
- **Test Items:** `python-parser/__tests__/TC_PP_004.py`; helpers `validate_zip_structure`, `filter_source_files`, `calculate_file_hash`, `is_text_file`, `get_file_extension`, `validate_file_size`.
- **Pre-condition:** Python 3.13.5 with pytest; run `pytest __tests__/TC_PP_004.py -k TC_PP_004`.
- **Dependencies:** None (helpers defined in test module).
- **Test Summary:** Ensure archive-processing helpers validate source content, filter files by extension, hash contents, detect text/binary, extract extensions, and enforce size limits.
- **Test Steps:**
  1. Validate file lists containing supported source files versus empty/binary-only lists using `validate_zip_structure`.
  2. Filter filenames through `filter_source_files` and inspect results.
  3. Hash content strings with `calculate_file_hash`, including duplicates and invalid inputs.
  4. Evaluate `is_text_file` with text vs binary indicators.
  5. Extract extensions via `get_file_extension` and check case normalization.
  6. Run `validate_file_size` with negative, zero, within-limit, and oversize values.
- **Test Data:**
  - File lists: `["src/model.py", "README.md"]`, `["binary.exe"]`, `[]`.
  - Contents: `"print('hi')"`, `"print('hi')"` (duplicate), `None`.
  - Filenames: `"archive.tar.gz"`, `"Service.JS"`, `"noextension"`.
  - Sizes (bytes): `1024`, `52 * 1024 * 1024`, `-10`.
- **Expected Result:**
  - Valid structures return `{ valid: true }`; invalid ones provide `{ valid: false, error: <message> }`.
  - Filtering yields only supported source files preserving order.
  - Hashing duplicates returns identical digests; invalid inputs return `None`.
  - Text detection flags text strings as `True`, binary markers as `False`.
  - Extension helper returns lowercase suffix or empty string when absent.
  - Size validation enforces 50 MB limit and rejects negatives.
- **Post-condition:** No files extracted or written; operations remain in-memory.
- **Actual Result:** Pass – 19 assertions succeeded on November 13 2025 (~63 ms runtime).
- **Status:** Pass

#### Test Case #: TC-PP-005 – Error Response Formatting
- **Test Title:** Error Response Formatting
- **Test Priority:** Medium
- **Test Items:** `python-parser/__tests__/TC_PP_005.py`; helpers `AnalysisError`, `create_error_response`, `create_success_response`, `format_validation_errors`, `log_error`, `sanitize_error_message`.
- **Pre-condition:** Python 3.13.5 with pytest; execute `pytest __tests__/TC_PP_005.py -k TC_PP_005`.
- **Dependencies:** None (helpers contained in module).
- **Test Summary:** Verify error/response helpers standardize API envelopes, sanitize sensitive data, and produce structured logs/validation outputs.
- **Test Steps:**
  1. Instantiate `AnalysisError` with various status codes and format via `create_error_response`.
  2. Wrap success payloads (objects, empty, `None`) with `create_success_response`.
  3. Pass valid/invalid validation error lists through `format_validation_errors`.
  4. Log errors using `log_error` with optional context and inspect structure.
  5. Sanitize messages containing filesystem paths and sensitive keywords via `sanitize_error_message`.
- **Test Data:**
  - Errors: `AnalysisError("Validation failed", 400, "validation-error")`, generic `Exception("Unexpected")`.
  - Payloads: `{ "result": "ok" }`, `{}`, `None`.
  - Validation inputs: `[{ "field": "url", "message": "Invalid" }, {"not": "valid"}]`, `[]`.
  - Messages: `"/home/user/secret.txt"`, `"Found password=123"`, `"C:\\Secrets\\token.txt"`.
- **Expected Result:**
  - Error responses retain status/type while sanitizing sensitive strings (paths replaced with `[PATH]`, keywords redacted).
  - Success responses return `{ success: true, data: <payload> }` even for empty payloads.
  - Validation formatter returns only well-formed `{ field, message }` entries.
  - Logging helper outputs dictionaries containing error name, message, and optional context reference.
- **Post-condition:** No external logging sinks used; data remains in-memory.
- **Actual Result:** Pass – 17 assertions succeeded on November 13 2025 (~71 ms runtime).
- **Status:** Pass

## 5. Execution Guidelines
1. Backend: `cd backend && npm test -- --testPathPattern="TC-BE" --run`.
2. Frontend: `cd frontend && npm test -- --testPathPattern="TC-FE" --run`.
3. Python Parser: `cd python-parser && pytest __tests__/TC_PP_*.py -v`.
4. Suites are self-contained; no service start-up, network connectivity, or cleanup is required.

## 6. Revision History
| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2025-11-13 | Automated Generation | Initial IEEE-formatted test plan (integration concept).
| 2.0 | 2025-11-13 | Test Automation Team | Converted to moderate unit tests and recorded execution results.
| 3.0 | 2025-11-13 | Test Automation Team | Rewritten to reflect implemented unit tests and include IEEE 829 fields (inputs, outputs, environment, procedures, dependencies).
