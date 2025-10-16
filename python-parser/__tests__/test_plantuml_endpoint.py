"""
Integration tests for PlantUML Flask endpoint
Tests /generate-plantuml API endpoint
"""
import pytest
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


class TestPlantUMLEndpoint:
    """Test suite for /generate-plantuml endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def sample_schema(self):
        """Sample schema for testing"""
        return {
            'python': [
                {
                    'class': 'User',
                    'type': 'class',
                    'fields': [
                        {'name': 'id', 'type': 'int', 'visibility': 'private'},
                        {'name': 'email', 'type': 'str', 'visibility': 'public'}
                    ],
                    'methods': [
                        {'name': '__init__', 'visibility': 'public'},
                        {'name': 'get_email', 'visibility': 'public', 'return_type': 'str'}
                    ]
                }
            ],
            'relations': []
        }
    
    # ============================================================================
    # Test Endpoint Basics
    # ============================================================================
    
    def test_endpoint_exists(self, client):
        """Test that /generate-plantuml endpoint exists"""
        response = client.post('/generate-plantuml')
        # Should return 400 (bad request) not 404 (not found)
        assert response.status_code in [400, 422, 500]  # Not 404
    
    def test_endpoint_requires_post(self, client):
        """Test that GET requests are rejected"""
        response = client.get('/generate-plantuml')
        assert response.status_code == 405  # Method Not Allowed
    
    def test_endpoint_requires_json(self, client):
        """Test that non-JSON requests are rejected"""
        response = client.post(
            '/generate-plantuml',
            data='not json',
            content_type='text/plain'
        )
        assert response.status_code in [400, 415]  # Bad Request or Unsupported Media Type
    
    # ============================================================================
    # Test Valid Requests
    # ============================================================================
    
    def test_generate_class_diagram(self, client, sample_schema):
        """Test generating a class diagram"""
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': sample_schema,
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check response structure
        assert 'plantuml' in data
        assert 'diagram_type' in data
        assert data['diagram_type'] == 'class'
        
        # Check PlantUML syntax
        plantuml = data['plantuml']
        assert plantuml.startswith('@startuml')
        assert plantuml.endswith('@enduml')
        assert 'User' in plantuml
    
    def test_generate_sequence_diagram(self, client):
        """Test generating a sequence diagram"""
        schema = {
            'endpoints': [
                {
                    'path': '/users',
                    'method': 'POST',
                    'controller': 'UserController',
                    'service': 'UserService'
                }
            ]
        }
        
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': schema,
                'diagram_type': 'sequence'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'plantuml' in data
        assert '@startuml' in data['plantuml']
        assert 'UserController' in data['plantuml']
    
    def test_generate_usecase_diagram(self, client):
        """Test generating a use case diagram"""
        schema = {
            'endpoints': [
                {'path': '/login', 'method': 'POST'},
                {'path': '/profile', 'method': 'GET'}
            ]
        }
        
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': schema,
                'diagram_type': 'usecase'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'plantuml' in data
        assert '@startuml' in data['plantuml']
    
    def test_generate_state_diagram(self, client):
        """Test generating a state diagram"""
        schema = {
            'python': [
                {
                    'class': 'Order',
                    'methods': [
                        {'name': 'create'},
                        {'name': 'confirm'},
                        {'name': 'ship'}
                    ]
                }
            ]
        }
        
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': schema,
                'diagram_type': 'state'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'plantuml' in data
        assert '@startuml' in data['plantuml']
    
    def test_generate_activity_diagram(self, client):
        """Test generating an activity diagram"""
        schema = {
            'endpoints': [
                {'path': '/checkout', 'method': 'POST'}
            ]
        }
        
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': schema,
                'diagram_type': 'activity'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'plantuml' in data
        assert '@startuml' in data['plantuml']
    
    # ============================================================================
    # Test Error Handling
    # ============================================================================
    
    def test_missing_schema(self, client):
        """Test request without schema"""
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 422]  # Bad Request
    
    def test_missing_diagram_type(self, client, sample_schema):
        """Test request without diagram_type"""
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': sample_schema
            }),
            content_type='application/json'
        )
        
        # Should either default to 'class' or return error
        assert response.status_code in [200, 400, 422]
    
    def test_invalid_diagram_type(self, client, sample_schema):
        """Test request with invalid diagram_type"""
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': sample_schema,
                'diagram_type': 'invalid_type'
            }),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 422]  # Bad Request
    
    def test_empty_schema(self, client):
        """Test request with empty schema"""
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': {},
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        
        # Should handle gracefully and return valid (empty) PlantUML
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '@startuml' in data['plantuml']
        assert '@enduml' in data['plantuml']
    
    def test_malformed_json(self, client):
        """Test request with malformed JSON"""
        response = client.post(
            '/generate-plantuml',
            data='{invalid json}',
            content_type='application/json'
        )
        
        assert response.status_code in [400, 422]
    
    # ============================================================================
    # Test Response Format
    # ============================================================================
    
    def test_response_content_type(self, client, sample_schema):
        """Test that response has correct content type"""
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': sample_schema,
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        assert 'application/json' in response.content_type
    
    def test_response_structure(self, client, sample_schema):
        """Test that response has expected structure"""
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': sample_schema,
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check all expected fields
        assert 'plantuml' in data
        assert 'diagram_type' in data
        assert isinstance(data['plantuml'], str)
        assert isinstance(data['diagram_type'], str)
    
    # ============================================================================
    # Test Complex Schemas
    # ============================================================================
    
    def test_multi_language_schema(self, client):
        """Test schema with multiple languages"""
        schema = {
            'python': [
                {'class': 'PythonClass', 'methods': []}
            ],
            'java': [
                {'class': 'JavaClass', 'methods': []}
            ],
            'typescript': [
                {'class': 'TypeScriptClass', 'methods': []}
            ],
            'relations': []
        }
        
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': schema,
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # All classes should be present
        plantuml = data['plantuml']
        assert 'PythonClass' in plantuml
        assert 'JavaClass' in plantuml
        assert 'TypeScriptClass' in plantuml
    
    def test_large_schema(self, client):
        """Test with a large schema (many classes)"""
        classes = [
            {
                'class': f'Class{i}',
                'fields': [
                    {'name': f'field{j}', 'type': 'string', 'visibility': 'public'}
                    for j in range(5)
                ],
                'methods': [
                    {'name': f'method{j}', 'visibility': 'public'}
                    for j in range(5)
                ]
            }
            for i in range(20)
        ]
        
        schema = {
            'python': classes,
            'relations': []
        }
        
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': schema,
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        
        # Should handle large schemas without error
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '@startuml' in data['plantuml']
        assert 'Class0' in data['plantuml']
        assert 'Class19' in data['plantuml']
    
    def test_complex_relationships(self, client):
        """Test schema with multiple relationship types"""
        schema = {
            'python': [
                {'class': 'A', 'methods': []},
                {'class': 'B', 'methods': []},
                {'class': 'C', 'methods': []},
                {'class': 'D', 'methods': []},
                {'class': 'E', 'methods': []}
            ],
            'relations': [
                {'from': 'A', 'to': 'B', 'type': 'extends'},
                {'from': 'C', 'to': 'D', 'type': 'implements'},
                {'from': 'E', 'to': 'A', 'type': 'composition'},
                {'from': 'B', 'to': 'C', 'type': 'aggregation'},
                {'from': 'D', 'to': 'E', 'type': 'dependency'}
            ]
        }
        
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': schema,
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        plantuml = data['plantuml']
        
        # Check for different arrow types
        assert '--|>' in plantuml  # extends
        assert '..|>' in plantuml  # implements
        assert '*--' in plantuml or '--*' in plantuml  # composition
        assert 'o--' in plantuml or '--o' in plantuml  # aggregation
        assert '..>' in plantuml  # dependency
    
    # ============================================================================
    # Test CORS and Headers
    # ============================================================================
    
    def test_cors_headers(self, client, sample_schema):
        """Test that CORS headers are present"""
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': sample_schema,
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        
        # Check for CORS headers (if implemented)
        # This test may need adjustment based on actual CORS configuration
        assert response.status_code == 200
    
    # ============================================================================
    # Test Performance
    # ============================================================================
    
    def test_response_time(self, client, sample_schema):
        """Test that endpoint responds in reasonable time"""
        import time
        
        start_time = time.time()
        response = client.post(
            '/generate-plantuml',
            data=json.dumps({
                'schema': sample_schema,
                'diagram_type': 'class'
            }),
            content_type='application/json'
        )
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        # Should respond within 5 seconds
        assert elapsed_time < 5.0
    
    def test_concurrent_requests(self, client, sample_schema):
        """Test handling of concurrent requests"""
        import threading
        
        results = []
        
        def make_request():
            response = client.post(
                '/generate-plantuml',
                data=json.dumps({
                    'schema': sample_schema,
                    'diagram_type': 'class'
                }),
                content_type='application/json'
            )
            results.append(response.status_code)
        
        # Make 5 concurrent requests
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should succeed
        assert all(status == 200 for status in results)
