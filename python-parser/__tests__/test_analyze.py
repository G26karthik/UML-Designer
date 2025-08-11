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
