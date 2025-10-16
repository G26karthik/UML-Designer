import os
import tempfile
import zipfile
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
import threading
import shutil
import subprocess
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from analyze import analyze_repo, call_gemini
from plantuml.llm import generate_plantuml_llm, SUPPORTED_DIAGRAM_TYPES, FORMAT_TO_TYPES
from security import validate_github_url, sanitize_file_path, validate_environment_limits
from utils.error_handler import (
    handle_error, 
    create_validation_error, 
    create_timeout_error, 
    create_resource_limit_error, 
    create_security_error,
    AppError,
    try:
        llm_start = time.time()
        try:
            llm_result = generate_plantuml_llm(
                prompt,
                diagram_type=diagram_type_normalized,
                output_format=output_format,
                context=context,
                schema=schema,
                style_preferences=style,
                focus=focus,
            )
        except Exception as ai_exc:
            # Fallback: return stub diagram, log error, do not crash
            from plantuml.llm import _stub_diagram, _normalize_diagram
            logging.error(f'{{"event": "ai_fallback", "error": "{ai_exc}"}}')
            stub = _stub_diagram(diagram_type_normalized, output_format=output_format)
            llm_result = _normalize_diagram(stub, diagram_type_normalized, output_format)
            llm_result['source'] = 'fallback'
            llm_result['warnings'] = [f'AI enrichment failed: {ai_exc}']
        llm_duration = time.time() - llm_start
        logging.info(f'{{"event": "llm_generate", "duration": {llm_duration:.3f}, "diagram_type": "{diagram_type_normalized}"}}')
    except ValueError as exc:
        logging.warning(f'{{"event": "invalid_prompt", "error": "{exc}"}}')
        raise HTTPException(status_code=400, detail=str(exc))
    status_code = 200 if llm_result.get('diagram') else 500
    cache.set(cache_key, llm_result, expire=cache_expire_seconds)
    total_duration = time.time() - start_time
    logging.info(f'{{"event": "cache_store", "key": "{cache_key}", "duration": {total_duration:.3f}}}')
    return JSONResponse(content=llm_result, status_code=status_code)
# Diskcache setup
DISKCACHE_DIR = os.environ.get("DISKCACHE_DIR", os.path.join(os.path.dirname(__file__), "..", "cache"))
os.makedirs(DISKCACHE_DIR, exist_ok=True)
cache = Cache(DISKCACHE_DIR)

app = FastAPI(title="UML Designer AI Parser", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/uml-from-prompt")
async def uml_from_prompt(request: Request):
    data = await request.json()
    prompt = data.get('prompt') if data else None
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        raise HTTPException(status_code=400, detail='Prompt is required and must be a non-empty string')
    diagram_type = data.get('diagramType', 'class')
    output_format = data.get('format', 'plantuml')
    if not isinstance(output_format, str):
        output_format = 'plantuml'
    raw_context = data.get('context')
    context = raw_context if isinstance(raw_context, dict) else None
    raw_schema = data.get('schema')
    schema = raw_schema if isinstance(raw_schema, dict) else None
    raw_style = data.get('stylePreferences')
    style = raw_style if isinstance(raw_style, dict) else None
    raw_focus = data.get('focus')
    focus = None
    if isinstance(raw_focus, (list, tuple)):
        focus = [str(item) for item in raw_focus if str(item).strip()]
    elif isinstance(raw_focus, str) and raw_focus.strip():
        focus = [segment.strip() for segment in raw_focus.split(',') if segment.strip()]
    if isinstance(diagram_type, str):
        diagram_type_normalized = diagram_type.lower()
        if diagram_type_normalized not in SUPPORTED_DIAGRAM_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported diagramType '{diagram_type}'.")
    else:
        raise HTTPException(status_code=400, detail='diagramType must be a string')
    allowed_types = FORMAT_TO_TYPES.get(output_format.lower().strip(), SUPPORTED_DIAGRAM_TYPES)
    if diagram_type_normalized not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported diagramType '{diagram_type}' for format '{output_format}'.")

    # Diskcache key: hash of prompt+diagram_type+output_format+schema
    import hashlib
    import json as pyjson
    cache_key_data = {
        "prompt": prompt,
        "diagram_type": diagram_type,
        "output_format": output_format,
        "schema": schema,
        "context": context,
        "style": style,
        "focus": focus,
    }
    cache_key = hashlib.sha256(pyjson.dumps(cache_key_data, sort_keys=True, default=str).encode()).hexdigest()

    # Try cache first
    cache_expire_seconds = int(os.environ.get("DISKCACHE_EXPIRE", 3600 * 24))  # 24h default
    start_time = time.time()
    cached = cache.get(cache_key)
    if cached:
        logging.info(f'{{"event": "cache_hit", "key": "{cache_key}", "duration": {time.time() - start_time:.3f}}}')
        return JSONResponse(content=cached, status_code=200)
    logging.info(f'{{"event": "cache_miss", "key": "{cache_key}"}}')

    try:
        llm_start = time.time()
        llm_result = generate_plantuml_llm(
            prompt,
            diagram_type=diagram_type_normalized,
            output_format=output_format,
            context=context,
            schema=schema,
            style_preferences=style,
            focus=focus,
        )
        llm_duration = time.time() - llm_start
        logging.info(f'{{"event": "llm_generate", "duration": {llm_duration:.3f}, "diagram_type": "{diagram_type_normalized}"}}')
    except ValueError as exc:
        logging.warning(f'{{"event": "invalid_prompt", "error": "{exc}"}}')
        raise HTTPException(status_code=400, detail=str(exc))
    status_code = 200 if llm_result.get('diagram') else 500
    cache.set(cache_key, llm_result, expire=cache_expire_seconds)
    total_duration = time.time() - start_time
    logging.info(f'{{"event": "cache_store", "key": "{cache_key}", "duration": {total_duration:.3f}}}')
    return JSONResponse(content=llm_result, status_code=status_code)

# Add more routes as needed, mirroring Flask routes

@app.get("/health")
def health():
    return {"status": "ok"}

# FastAPI auto-generates /docs and /openapi.json
