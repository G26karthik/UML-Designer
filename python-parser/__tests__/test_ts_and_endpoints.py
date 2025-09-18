import os
import tempfile
from analyze import analyze_repo

def test_flask_endpoint_detection(tmp_path):
    app_py = tmp_path / 'app.py'
    app_py.write_text(
        'from flask import Flask\napp = Flask(__name__)\n' \
        '@app.route("/ping", methods=["GET"])\n' \
        'def ping():\n    return "pong"\n'
    )
    res = analyze_repo(tmp_path)
    eps = res.get('endpoints') or []
    assert any(e.get('framework') == 'flask' and e.get('path') == '/ping' and e.get('method') == 'GET' for e in eps)


def test_typescript_relations(tmp_path):
    a = tmp_path / 'a.ts'
    b = tmp_path / 'b.ts'
    a.write_text('export interface IFoo {}\nexport class Base {}\nexport class A extends Base implements IFoo { methodA() {} }')
    b.write_text('export class B extends A {}')
    res = analyze_repo(tmp_path)
    rels = res.get('relations') or []
    # extends from Base->A and A->B, implements IFoo->A
    assert {'from': 'Base', 'to': 'A', 'type': 'extends', 'source': 'heuristic'} in rels
    assert {'from': 'A', 'to': 'B', 'type': 'extends', 'source': 'heuristic'} in rels
    assert {'from': 'IFoo', 'to': 'A', 'type': 'implements', 'source': 'heuristic'} in rels
