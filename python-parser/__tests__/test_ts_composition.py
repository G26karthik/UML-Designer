import os
from analyze import analyze_repo


def test_typescript_instance_composition(tmp_path):
    # Define two classes where one composes the other via `this.engine = new Engine()`
    a = tmp_path / 'car.ts'
    b = tmp_path / 'engine.ts'
    b.write_text('export class Engine { start() {} }')
    a.write_text(
        'export class Car {\n'
        '  engine: Engine;\n'
        '  constructor() {\n'
        '    this.engine = new Engine();\n'
        '  }\n'
        '  drive() {}\n'
        '}'
    )

    res = analyze_repo(tmp_path)
    # Expect composition relation from Car to Engine
    rels = res.get('relations') or []
    assert {'from': 'Car', 'to': 'Engine', 'type': 'composition', 'source': 'heuristic'} in rels
    # Expect fields to include inferred type for engine
    ts = res.get('typescript') or []
    car = next((c for c in ts if c.get('class') == 'Car'), None)
    assert car is not None
    assert any(str(f).startswith('engine: Engine') for f in car.get('fields', []))