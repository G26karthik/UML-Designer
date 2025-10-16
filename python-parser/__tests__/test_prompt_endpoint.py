"""Tests for the /uml-from-prompt endpoint and LLM helpers."""

import os
import sys
import json
import importlib

import pytest

# Ensure STUB mode is enabled before importing application modules
os.environ['STUB_LLM'] = 'true'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # noqa: E402
import plantuml.llm as plantuml_llm  # noqa: E402
from prompts.plantuml_prompt import build_plantuml_prompt  # noqa: E402

# Reload LLM module so it picks up the STUB_LLM flag set above
plantuml_llm = importlib.reload(plantuml_llm)


class TestPromptEndpoint:
    """Test suite covering the natural-language UML endpoint."""

    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_build_prompt_includes_sections(self):
        prompt = build_plantuml_prompt(
            "Model an ecommerce checkout",
            diagram_type='sequence',
            context={'scope': 'web checkout'},
            focus=['payments'],
        )
        assert 'Diagram type: sequence' in prompt
        assert 'scope' in prompt.lower()
        assert 'payments' in prompt.lower()

    def test_generate_plantuml_stub(self):
        result = plantuml_llm.generate_plantuml_llm('User management platform', diagram_type='class')
        assert result['diagram'].startswith('@startuml')
        assert result['diagram'].endswith('@enduml')
        assert result['raw_diagram'].startswith('@startuml')
        assert result['source'] in {'stub', 'disabled', 'fallback', 'error-fallback', 'local-cache'}

    def test_generate_mermaid_stub(self):
        result = plantuml_llm.generate_plantuml_llm('Queue processing', diagram_type='activity', output_format='mermaid')
        first_line = result['diagram'].splitlines()[0]
        assert first_line in {'flowchart TD', 'graph TD'}
        assert result['raw_diagram'].startswith('```mermaid')
        assert result['diagram']

    def test_endpoint_returns_plantuml(self, client):
        payload = {
            'prompt': 'A task board with columns and cards',
            'diagramType': 'class',
            'format': 'plantuml',
        }
        response = client.post('/uml-from-prompt', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['diagram'].startswith('@startuml')
        assert data['diagram_type'] == 'class'
        assert data['format'] == 'plantuml'
        assert data['raw_diagram'].startswith('@startuml')

    def test_endpoint_returns_mermaid(self, client):
        payload = {
            'prompt': 'Notification flow from user action to email service',
            'diagramType': 'sequence',
            'format': 'mermaid',
        }
        response = client.post('/uml-from-prompt', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['format'] == 'mermaid'
        assert data['diagram']
        first_line = data['diagram'].splitlines()[0]
        assert first_line in {'sequenceDiagram', 'graph TD', 'flowchart TD', 'classDiagram', 'stateDiagram-v2', 'erDiagram'}
        assert data['raw_diagram'].startswith('```mermaid')

    def test_endpoint_validates_diagram_type(self, client):
        payload = {'prompt': 'anything', 'diagramType': 'foobar'}
        response = client.post('/uml-from-prompt', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 400

    def test_endpoint_requires_prompt(self, client):
        response = client.post('/uml-from-prompt', data=json.dumps({}), content_type='application/json')
        assert response.status_code == 400
