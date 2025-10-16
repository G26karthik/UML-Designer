

import os
import tempfile
import zipfile
import logging
from flask import Flask, request, jsonify  # type: ignore
from flask.testing import FlaskClient  # type: ignore
import threading
import shutil
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    ErrorType
)
from plantuml.plantuml_generator import PlantUMLGenerator

class ThreadSafeFlaskClient(FlaskClient):
    """Flask test client that serializes access for thread-safe testing."""
    _lock = threading.Lock()

    def open(self, *args, **kwargs):  # type: ignore[override]
        with self._lock:
            return super().open(*args, **kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore[override]
        try:
            return super().__exit__(exc_type, exc_val, exc_tb)
        except LookupError:
            # Flask test client isn't thread-safe; concurrent tests can pop contexts twice.
            # Swallow context errors so teardown doesn't raise in tests.
            return False
        except RuntimeError as err:
            if "Working outside of request context" in str(err):
                return False
            raise


app = Flask(__name__)
app.test_client_class = ThreadSafeFlaskClient
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for service monitoring."""
    return jsonify({
        'status': 'healthy',
        'service': 'python-parser',
        'version': '1.0.0',
        'timestamp': '2025-10-14T20:27:48.512Z'
    })

# POST /uml-from-prompt: Generate UML from natural language prompt
@app.route('/uml-from-prompt', methods=['POST'])
def uml_from_prompt():
    try:
        data = request.get_json(force=True)
        prompt = data.get('prompt') if data else None
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            return jsonify({'error': 'Prompt is required and must be a non-empty string'}), 400
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
                return jsonify({'error': f"Unsupported diagramType '{diagram_type}'."}), 400
        else:
            return jsonify({'error': 'diagramType must be a string'}), 400

        allowed_types = FORMAT_TO_TYPES.get(output_format.lower().strip(), SUPPORTED_DIAGRAM_TYPES)
        if diagram_type_normalized not in allowed_types:
            return jsonify({'error': f"Unsupported diagramType '{diagram_type}' for format '{output_format}'."}), 400

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
        except ValueError as exc:
            logging.warning(f"Invalid prompt request: {exc}")
            return jsonify({'error': str(exc)}), 400

        status_code = 200 if llm_result.get('diagram') else 500
        return jsonify(llm_result), status_code
    except Exception as e:
        logging.error(f"Error in /uml-from-prompt: {str(e)}")
        return jsonify({'error': 'Failed to process prompt'}), 500

@app.route('/generate-plantuml', methods=['POST'])
def generate_plantuml():
    """
    Generate PlantUML diagram from analysis schema.
    
    Request JSON:
    {
        "schema": {...},  // Required: Analysis schema from analyze_repo
        "diagram_type": "class",  // Required: class|sequence|usecase|state|activity
        "language_filter": ["python", "java"],  // Optional: Filter by languages
        "config": {  // Optional: PlantUML configuration
            "theme": "plain",
            "show_methods": true,
            "show_fields": true,
            "show_private": false
        }
    }
    
    Returns:
    {
        "plantuml": "...",  // PlantUML syntax string
        "diagram_type": "class",
        "statistics": {...}
    }
    """
    try:
        data = request.get_json(silent=True)

        # Validate request payload
        if data is None:
            return jsonify({'error': 'Request body must be valid JSON'}), 400

        if 'schema' not in data:
            return jsonify({'error': 'schema is required'}), 400

        schema = data.get('schema')
        if schema is None:
            return jsonify({'error': 'schema must not be null'}), 400
        if not isinstance(schema, dict):
            return jsonify({'error': 'schema must be an object'}), 400
        
        diagram_type = data.get('diagram_type', 'class')
        allowed_types = ['class', 'sequence', 'usecase', 'state', 'activity', 'component', 'communication', 'deployment']
        if diagram_type not in allowed_types:
            return jsonify({
                'error': f'Invalid diagram_type: {diagram_type}. Must be one of: {', '.join(allowed_types)}'
            }), 400
        
        language_filter = data.get('language_filter')
        config = data.get('config', {})
        
        # Create generator and generate PlantUML
        generator = PlantUMLGenerator(config)
        
        try:
            plantuml_syntax = generator.generate(
                schema=schema,
                diagram_type=diagram_type,
                language_filter=language_filter
            )
            
            # Get statistics
            stats = generator.get_statistics(schema)
            
            return jsonify({
                'plantuml': plantuml_syntax,
                'diagram_type': diagram_type,
                'statistics': stats,
                'success': True
            })
            
        except ValueError as e:
            logging.error(f"PlantUML generation validation error: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 400
        
    except Exception as e:
        logging.error(f"Error in /generate-plantuml: {str(e)}")
        return jsonify({
            'error': 'Failed to generate PlantUML diagram',
            'details': str(e),
            'success': False
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    repo_path = None
    try:
        # Get environment limits
        limits = validate_environment_limits()
        logging.info(f"Using limits: {limits}")
        
        github_url = request.json.get('githubUrl') if request.is_json else None
        if github_url:
            # Validate GitHub URL
            is_valid, error_msg, url_info = validate_github_url(github_url)
            if not is_valid:
                return jsonify({'error': f'Invalid GitHub URL: {error_msg}'}), 400
            
            logging.info(f"Analyzing repository: {url_info['display_name']}")
            
            # Clone repo securely with validated URL
            repo_path = tempfile.mkdtemp()
            env = os.environ.copy()
            env.update({
                'GIT_LFS_SKIP_SMUDGE': '1',
                'GIT_TERMINAL_PROMPT': '0',
                'GIT_ASKPASS': 'echo',  # Prevent interactive prompts
            })
            

            # Optimize git clone: shallow, filter blobs, sparse checkout
            clone_cmd = [
                'git', 'clone',
                '--depth', '1',
                '--filter=blob:none',
                '--single-branch',
                '--no-tags',
                url_info['clean_url'],
                repo_path
            ]
            proc = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=limits['timeout'],
                cwd=tempfile.gettempdir()
            )
            if proc.returncode != 0:
                error_msg = proc.stderr.strip() or proc.stdout.strip() or 'Git clone failed'
                logging.error(f"Git clone failed for {url_info['display_name']}: {error_msg}")
                return jsonify({'error': 'Repository cloning failed', 'details': error_msg}), 400

            # Sparse checkout to skip unnecessary directories
            sparse_patterns = [
                '/*',
                '!**/tests/', '!**/test/', '!**/node_modules/', '!**/.git/', '!**/.github/', '!**/docs/', '!**/examples/', '!**/sample/', '!**/samples/'
            ]
            try:
                # Disable sparse checkout for testing
                # subprocess.run(['git', '-C', repo_path, 'sparse-checkout', 'init', '--cone'], check=True, timeout=10)
                # subprocess.run(['git', '-C', repo_path, 'sparse-checkout', 'set'] + sparse_patterns, check=True, timeout=10)
                pass
            except Exception as e:
                logging.warning(f"Sparse checkout failed: {e}")
                
        elif 'repoZip' in request.files:
            # Handle ZIP upload securely
            repo_path = tempfile.mkdtemp()
            zip_file = request.files['repoZip']
            
            # Validate file size
            if hasattr(zip_file, 'content_length') and zip_file.content_length > 50 * 1024 * 1024:
                return jsonify({'error': 'ZIP file too large (max 50MB)'}), 400
            
            try:
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    for member in zf.infolist():
                        # Use our security function for path validation
                        is_safe, safe_path = sanitize_file_path(member.filename, repo_path)
                        if not is_safe:
                            return jsonify({'error': f'Unsafe zip path detected: {member.filename}'}), 400
                        
                        if member.is_dir():
                            os.makedirs(safe_path, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
                            with zf.open(member, 'r') as src, open(safe_path, 'wb') as dst:
                                shutil.copyfileobj(src, dst)
            except zipfile.BadZipFile:
                return jsonify({'error': 'Invalid ZIP file'}), 400
            except Exception as e:
                return jsonify({'error': f'ZIP extraction failed: {str(e)}'}), 400
        else:
            return jsonify({'error': 'No repository provided (githubUrl or repoZip required)'}), 400

        # Parse repo with security limits
        ast_json = analyze_repo(repo_path, limits)

        # Ensure meta property always exists and is a dict
        if 'meta' not in ast_json or not isinstance(ast_json['meta'], dict):
            ast_json['meta'] = {}

        # Attach commit metadata if available
        try:
            commit = subprocess.check_output(
                ['git', '-C', repo_path, 'rev-parse', 'HEAD'], 
                text=True, 
                timeout=10
            ).strip()
            ast_json['meta']['commit'] = commit
        except Exception as e:
            logging.debug(f"Could not get commit info: {e}")

        # Fill required meta fields with safe defaults if missing or invalid
        meta = ast_json['meta']
        meta['classes_found'] = meta.get('classes_found') if isinstance(meta.get('classes_found'), int) and meta.get('classes_found') >= 0 else 0
        meta['files_scanned'] = meta.get('files_scanned') if isinstance(meta.get('files_scanned'), int) and meta.get('files_scanned') >= 0 else 0
        meta['languages'] = meta.get('languages') if isinstance(meta.get('languages'), list) else []
        meta['system'] = meta.get('system') if isinstance(meta.get('system'), str) else 'UnknownSystem'
        ast_json['meta'] = meta

        # Log analysis summary
        try:
            summary = {k: len(v) for k, v in ast_json.items() if isinstance(v, list)}
            rels = len(ast_json.get('relations', []))
            logging.info(f'Analysis complete: {summary}, relations={rels}')
        except Exception:
            logging.info('Analysis completed')

        # Call LLM with security considerations
        gemini_result = call_gemini(ast_json)
        # If LLM result, enforce meta fields again
        if 'schema' in gemini_result and isinstance(gemini_result['schema'], dict):
            schema = gemini_result['schema']
            if 'meta' not in schema or not isinstance(schema['meta'], dict):
                schema['meta'] = {}
            meta = schema['meta']
            meta['classes_found'] = meta.get('classes_found') if isinstance(meta.get('classes_found'), int) and meta.get('classes_found') >= 0 else 0
            meta['files_scanned'] = meta.get('files_scanned') if isinstance(meta.get('files_scanned'), int) and meta.get('files_scanned') >= 0 else 0
            meta['languages'] = meta.get('languages') if isinstance(meta.get('languages'), list) else []
            meta['system'] = meta.get('system') if isinstance(meta.get('system'), str) else 'UnknownSystem'
            schema['meta'] = meta
            gemini_result['schema'] = schema
        if 'error' in gemini_result:
            logging.warning(f"LLM call failed: {gemini_result['error']}")
            # Return AST results even if LLM fails
            return jsonify({'schema': ast_json, 'meta': ast_json['meta']})

        return jsonify(gemini_result)
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Analysis timeout - repository too large or slow network'}), 408
    except MemoryError:
        return jsonify({'error': 'Analysis failed - repository too large for available memory'}), 413
    except Exception as e:
        logging.error(f"Unexpected error during analysis: {str(e)}")
        return jsonify({'error': 'Analysis failed due to unexpected error'}), 500
    finally:
        if repo_path and os.path.isdir(repo_path):
            try:
                shutil.rmtree(repo_path)
            except Exception as e:
                logging.warning(f'Cleanup failed for {repo_path}: {e}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
