import os
from analyze import analyze_repo

def test_python_instance_fields_and_composition(tmp_path):
    src = tmp_path / 'mod.py'
    src.write_text(
        'class Engine:\n    pass\n\n'
        'class Car:\n'
        '    def __init__(self):\n'
        '        self.engine: Engine = Engine()\n'
        '        self.color = "red"\n'
        '    def drive(self):\n'
        '        pass\n'
    )
    res = analyze_repo(tmp_path)
    cars = [c for c in res.get('python', []) if c.get('class') == 'Car']
    assert cars, 'Car class should be detected'
    car = cars[0]
    fields = set(car.get('fields') or [])
    # Should capture instance annotated and unannotated fields
    assert any(f.startswith('engine') for f in fields)
    assert 'color' in fields
    # Composition Engine from Car
    rels = res.get('relations') or []
    assert any(r.get('type') == 'composition' and r.get('from') == 'Car' and r.get('to') == 'Engine' for r in rels)
