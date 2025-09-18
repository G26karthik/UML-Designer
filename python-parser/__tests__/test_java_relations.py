from analyze import analyze_repo


def test_java_uses_and_composition(tmp_path):
    a = tmp_path / 'Car.java'
    b = tmp_path / 'Engine.java'
    b.write_text('public class Engine { public void start() {} public static void tune() {} }')
    a.write_text(
        'public class Car {\n'
        '  private Engine engine;\n'
        '  public Car() { this.engine = new Engine(); }\n'
        '  public void drive() { Engine e = new Engine(); Engine.tune(); }\n'
        '}'
    )

    res = analyze_repo(tmp_path)
    rels = res.get('relations') or []
    # composition from field assignment
    assert {'from': 'Car', 'to': 'Engine', 'type': 'composition', 'source': 'heuristic'} in rels
    # uses from local instantiation or static call
    assert {'from': 'Car', 'to': 'Engine', 'type': 'uses', 'source': 'heuristic'} in rels