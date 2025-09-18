import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analyze import analyze_repo

def test_empty_repo(tmp_path):
    result = analyze_repo(tmp_path)
    assert isinstance(result, dict)
    assert result.get('python') == []
    assert result.get('java') == []
    assert result.get('csharp') == []
    assert result.get('relations') == []

def test_files_scanned_meta(tmp_path):
    # create tiny python file
    p = tmp_path / 'a.py'
    p.write_text('class A:\n    pass\n')
    result = analyze_repo(tmp_path)
    assert 'meta' in result and isinstance(result['meta'], dict)
    assert isinstance(result['meta'].get('files_scanned'), int)
    assert result['meta']['files_scanned'] >= 1

def test_typescript_extends(tmp_path):
    ts_file = tmp_path / 'test.ts'
    ts_file.write_text('''
class Base {
  name: string;
}

class Derived extends Base {
  age: number;
}
''')
    result = analyze_repo(tmp_path)
    assert len(result['typescript']) >= 2
    classes = {c['class']: c for c in result['typescript']}
    assert 'Base' in classes
    assert 'Derived' in classes
    relations = result['relations']
    extends_rel = next((r for r in relations if r['type'] == 'extends' and r['from'] == 'Base' and r['to'] == 'Derived'), None)
    assert extends_rel is not None

def test_flask_endpoints(tmp_path):
    py_file = tmp_path / 'app.py'
    py_file.write_text('''
from flask import Flask
app = Flask(__name__)

@app.route('/users', methods=['GET', 'POST'])
def users():
    pass

@app.route('/items/<id>', methods=['PUT'])
def item(id):
    pass
''')
    result = analyze_repo(tmp_path)
    endpoints = result.get('endpoints', [])
    assert len(endpoints) >= 2
    paths = {ep['path'] for ep in endpoints}
    assert '/users' in paths
    assert '/items/<id>' in paths
    methods = {ep['method'] for ep in endpoints}
    assert 'GET' in methods
    assert 'POST' in methods
    assert 'PUT' in methods

def test_system_name_extraction(tmp_path):
    # Create a mock git repo structure
    git_dir = tmp_path / '.git'
    git_dir.mkdir()
    config_file = git_dir / 'config'
    config_file.write_text('[remote "origin"]\n\turl = https://github.com/user/test-repo.git\n')
    
    py_file = tmp_path / 'test.py'
    py_file.write_text('class Test:\n    pass\n')
    
    result = analyze_repo(tmp_path)
    assert 'meta' in result
    # Should extract 'test-repo' from git remote, or fallback to directory name
    system_name = result['meta']['system']
    assert system_name in ['test-repo', 'test_system_name_extraction0', 'System']
