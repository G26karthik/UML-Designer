Course: Software Engineering (PBL)
Project: UML Designer AI
Submitted by: Team 12
Date: 25 August 2025

Summary
-------
UML Designer is a compact full-stack project that analyzes source code from a repository and automatically generates UML class diagrams. It demonstrates multi-service integration (Next.js frontend, Express backend with caching, Python parser service) and practical concerns such as AST analysis, diagram generation, error handling, and developer UX.

Learning objectives (PBL-aligned)
---------------------------------
- Apply system decomposition and architecture design in a real full-stack project.
- Implement and test APIs and inter-service contracts.
- Work with language parsing (ASTs) and transform code structure into visual models.
- Improve software quality through iterative bug-fixing, tests, and documentation.

What the project does (short)
-----------------------------
1. Accepts a target GitHub repository and source files.
2. The Python parser analyzes source files (Java, Python, others) producing a normalized JSON model (classes, fields, methods, relationships).
3. The backend caches analysis results and exposes an API.
4. The frontend converts the JSON model to Mermaid UML syntax and renders diagrams in-browser; users can export SVG and copy source.

Architecture & key components
-----------------------------
- `frontend/`: Next.js + React UI, Mermaid rendering, user controls and tests.
- `backend/`: Express server, API endpoints, memory + disk caching layer, CORS and security middleware.
- `python-parser/`: Flask analysis service using language-specific parsers (e.g., `javalang` for Java, Python `ast`), heuristics, and optional AI enrichment.

Testing and verification
------------------------
- Unit tests exist for the Python parser and backend (see `python-parser/__tests__` and `backend/__tests__`).
- Manual smoke test: run parser (`python-parser/app.py`), start backend, open frontend and analyze a sample repo. Diagrams should render without Mermaid parse errors.



