

import os
import tempfile
import zipfile
import logging
from flask import Flask, request, jsonify
import shutil
import subprocess
from analyze import analyze_repo, call_gemini
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

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# POST /uml-from-prompt: Generate UML from natural language prompt
@app.route('/uml-from-prompt', methods=['POST'])
def uml_from_prompt():
    try:
        data = request.get_json(force=True)
        prompt = data.get('prompt') if data else None
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            return jsonify({'error': 'Prompt is required and must be a non-empty string'}), 400
        # Call LLM directly with prompt (no repo analysis)
        gemini_result = call_gemini({'prompt': prompt})
        if 'error' in gemini_result:
            logging.warning(f"LLM call failed: {gemini_result['error']}")
            return jsonify({'error': gemini_result['error']}), 500
        return jsonify(gemini_result)
    except Exception as e:
        logging.error(f"Error in /uml-from-prompt: {str(e)}")
        return jsonify({'error': 'Failed to process prompt'}), 500

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
            
            clone_cmd = [
                'git', 'clone', 
                '--depth', str(limits['clone_depth']),
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
                cwd=tempfile.gettempdir()  # Safe working directory
            )
            
            if proc.returncode != 0:
                error_msg = proc.stderr.strip() or proc.stdout.strip() or 'Git clone failed'
                logging.error(f"Git clone failed for {url_info['display_name']}: {error_msg}")
                return jsonify({'error': 'Repository cloning failed', 'details': error_msg}), 400
                
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
        
        # Attach commit metadata if available
        try:
            commit = subprocess.check_output(
                ['git', '-C', repo_path, 'rev-parse', 'HEAD'], 
                text=True, 
                timeout=10
            ).strip()
            meta = ast_json.get('meta', {})
            meta['commit'] = commit
            ast_json['meta'] = meta
        except Exception as e:
            logging.debug(f"Could not get commit info: {e}")
        
        # Log analysis summary
        try:
            summary = {k: len(v) for k, v in ast_json.items() if isinstance(v, list)}
            rels = len(ast_json.get('relations', []))
            logging.info(f'Analysis complete: {summary}, relations={rels}')
        except Exception:
            logging.info('Analysis completed')
        
        # Call LLM with security considerations
        gemini_result = call_gemini(ast_json)
        if 'error' in gemini_result:
            logging.warning(f"LLM call failed: {gemini_result['error']}")
            # Return AST results even if LLM fails
            return jsonify({'schema': ast_json, 'meta': ast_json.get('meta', {})})
        
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
    app.run(host='0.0.0.0', port=5000)
