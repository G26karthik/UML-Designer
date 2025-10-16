"""Integration test for prompt-to-diagram flow with format detection."""

import os
import sys

# Force stub mode
os.environ['STUB_LLM'] = 'true'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plantuml.llm import generate_plantuml_llm


def test_format_routing():
    """Verify backend returns correct format markers."""
    
    # Test PlantUML format
    result_plantuml = generate_plantuml_llm(
        'ATM system',
        diagram_type='activity',
        output_format='plantuml'
    )
    assert result_plantuml['format'] == 'plantuml'
    assert result_plantuml['diagram'].startswith('@startuml')
    assert result_plantuml['diagram'].endswith('@enduml')
    assert result_plantuml['raw_diagram'].startswith('@startuml')
    print('✓ PlantUML format validation passed')
    
    # Test Mermaid format
    result_mermaid = generate_plantuml_llm(
        'ATM system',
        diagram_type='activity',
        output_format='mermaid'
    )
    assert result_mermaid['format'] == 'mermaid'
    first_line = result_mermaid['diagram'].splitlines()[0]
    assert first_line in {'flowchart TD', 'graph TD'}, f"Got: {first_line}"
    assert result_mermaid['raw_diagram'].startswith('```mermaid')
    print('✓ Mermaid format validation passed')
    
    # Test format-specific diagram types
    result_gantt = generate_plantuml_llm(
        'Project timeline',
        diagram_type='gantt',
        output_format='mermaid'
    )
    assert result_gantt['format'] == 'mermaid'
    assert 'gantt' in result_gantt['diagram'].lower()
    print('✓ Mermaid-specific diagram type (gantt) passed')
    
    print('\n✅ All format routing tests passed!')


if __name__ == '__main__':
    test_format_routing()
