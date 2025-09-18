from analyze import analyze_repo


def test_csharp_composition_and_uses(tmp_path):
    cs = tmp_path / 'Cart.cs'
    dep = tmp_path / 'ApiClient.cs'
    dep.write_text('namespace App { public class ApiClient { public static void Ping() {} } }')
    cs.write_text(
        'namespace App {\n'
        '  public class Cart : BaseCart, ICart {\n'
        '    private ApiClient api;\n'
        '    public Cart() { this.api = new ApiClient(); }\n'
        '    public void Checkout() { var x = new ApiClient(); ApiClient.Ping(); }\n'
        '  }\n'
        '  public class BaseCart {}\n'
        '  public interface ICart {}\n'
        '}'
    )
    res = analyze_repo(tmp_path)
    rels = res.get('relations') or []
    # composition from this.api = new ApiClient()
    assert {'from': 'Cart', 'to': 'ApiClient', 'type': 'composition', 'source': 'heuristic'} in rels
    # uses from new ApiClient() and static call
    assert {'from': 'Cart', 'to': 'ApiClient', 'type': 'uses', 'source': 'heuristic'} in rels
    # inheritance and implements
    assert {'from': 'BaseCart', 'to': 'Cart', 'type': 'extends', 'source': 'heuristic'} in rels
    assert {'from': 'ICart', 'to': 'Cart', 'type': 'implements', 'source': 'heuristic'} in rels


def test_cpp_uses_and_composition(tmp_path):
    a = tmp_path / 'car.hpp'
    b = tmp_path / 'engine.hpp'
    b.write_text('class Engine { public: static void Tune(); };')
    a.write_text(
        'class Car {\n'
        '  Engine* engine;\n'
        'public:\n'
        '  void drive() { Engine::Tune(); Engine* e = new Engine(); }\n'
        '};'
    )
    res = analyze_repo(tmp_path)
    rels = res.get('relations') or []
    # composition candidate from field type Engine*
    assert {'from': 'Car', 'to': 'Engine', 'type': 'composition', 'source': 'heuristic'} in rels
    # uses from new Engine() and static call
    assert {'from': 'Car', 'to': 'Engine', 'type': 'uses', 'source': 'heuristic'} in rels