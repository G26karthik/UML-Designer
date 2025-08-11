

import os
import tempfile
import zipfile
import logging
from flask import Flask, request, jsonify
import shutil
import subprocess
from analyze import analyze_repo, call_gemini

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/analyze', methods=['POST'])
def analyze():
    repo_path = None
    try:
        github_url = request.json.get('githubUrl') if request.is_json else None
        if github_url:
            # Clone repo (shallow for large repositories)
            repo_path = tempfile.mkdtemp()
            depth = os.getenv('GIT_CLONE_DEPTH', '1')
            env = os.environ.copy()
            env.setdefault('GIT_LFS_SKIP_SMUDGE', '1')
            env.setdefault('GIT_TERMINAL_PROMPT', '0')
            proc = subprocess.run(['git', 'clone', '--depth', str(depth), github_url, repo_path], capture_output=True, text=True, env=env, timeout=180)
            if proc.returncode != 0:
                return jsonify({'error': 'Git clone failed', 'details': proc.stderr.strip() or proc.stdout.strip()}), 400
        elif 'repoZip' in request.files:
            # Unzip uploaded file securely
            repo_path = tempfile.mkdtemp()
            zip_file = request.files['repoZip']
            with zipfile.ZipFile(zip_file, 'r') as zf:
                for member in zf.infolist():
                    member_path = os.path.normpath(os.path.join(repo_path, member.filename))
                    if not member_path.startswith(os.path.abspath(repo_path)):
                        return jsonify({'error': 'Unsafe zip path detected.'}), 400
                    if member.is_dir():
                        os.makedirs(member_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(member_path), exist_ok=True)
                        with zf.open(member, 'r') as src, open(member_path, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
        else:
            return jsonify({'error': 'No repo provided.'}), 400
        # Parse repo
        ast_json = analyze_repo(repo_path)
        # Attach commit metadata if available (merge with existing meta)
        try:
            commit = subprocess.check_output(['git', '-C', repo_path, 'rev-parse', 'HEAD'], text=True).strip()
            meta = ast_json.get('meta') or {}
            meta['commit'] = commit
            ast_json['meta'] = meta
        except Exception:
            pass
        try:
            summary = {k: len(v) for k, v in ast_json.items() if isinstance(v, list)}
            rels = len(ast_json.get('relations') or [])
            logging.info(f'AST summary: {summary}, relations={rels}, meta={ast_json.get("meta") or {}}')
        except Exception:
            logging.info('AST summary prepared')
        # Call LLM
        gemini_result = call_gemini(ast_json)
        if 'error' in gemini_result:
            return jsonify({'error': 'Gemini API call failed', 'details': gemini_result['error']}), 500
        return jsonify(gemini_result)
    finally:
        if repo_path and os.path.isdir(repo_path):
            try:
                shutil.rmtree(repo_path)
            except Exception as e:
                logging.warning(f'Cleanup failed for {repo_path}: {e}')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
