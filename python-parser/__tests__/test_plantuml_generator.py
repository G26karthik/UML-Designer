"""
Unit tests for PlantUML generator module
Tests PlantUMLGenerator class for all 5 diagram types
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plantuml.plantuml_generator import PlantUMLGenerator


class TestPlantUMLGenerator:
    def test_plantuml_line_limit_truncation(self, generator):
        """Test that PlantUML output is truncated to 2000 lines and includes a warning note if needed."""
        # Generate a schema that will produce >2000 lines
        many_classes = [
            {
                'class': f'Class{i}',
                'fields': [
                    {'name': f'field{j}', 'type': 'string', 'visibility': 'public'}
                    for j in range(20)
                ],
                'methods': [
                    {'name': f'method{j}', 'visibility': 'public'}
                    for j in range(20)
                ]
            }
            for i in range(120)
        ]
        schema = {'python': many_classes, 'relations': []}
        result = generator.generate(schema, 'class')
        lines = result.splitlines()
        assert len(lines) <= 2000
        if len(lines) == 2000:
            # Should include warning note before @enduml
            assert any('Diagram truncated to 2000 lines' in l for l in lines)
            assert lines[-1].strip() == '@enduml'
    """Test suite for PlantUMLGenerator class"""
    
    @pytest.fixture
    def generator(self):
        """Create generator instance for tests"""
        return PlantUMLGenerator()
    
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
                        {'name': '__init__', 'visibility': 'public', 'params': ['self', 'email']},
                        {'name': 'get_id', 'visibility': 'public', 'params': ['self'], 'return_type': 'int'}
                    ]
                },
                {
                    'class': 'IRepository',
                    'type': 'interface',
                    'methods': [
                        {'name': 'save', 'visibility': 'public', 'params': ['self', 'entity'], 'return_type': 'void'}
                    ]
                },
                {
                    'class': 'BaseEntity',
                    'type': 'abstract',
                    'fields': [
                        {'name': 'created_at', 'type': 'datetime', 'visibility': 'protected'}
                    ]
                }
            ],
            'java': [],
            'typescript': [],
            'relations': [
                {'from': 'User', 'to': 'BaseEntity', 'type': 'extends'},
                {'from': 'UserRepository', 'to': 'IRepository', 'type': 'implements'},
                {'from': 'Order', 'to': 'User', 'type': 'composition', 'multiplicity': {'from': '1', 'to': '*'}}
            ]
        }
    
    # ============================================================================
    # Test Class Diagram Generation
    # ============================================================================
    
    def test_generate_class_diagram_basic(self, generator, sample_schema):
        """Test basic class diagram generation"""
        result = generator.generate(sample_schema, 'class')
        
        # Check structure
        assert result.startswith('@startuml')
        assert result.endswith('@enduml')
        assert '!theme plain' in result
        
        # Check classes present
        assert 'class User' in result
        assert 'interface IRepository' in result or '<<interface>>' in result
        assert 'abstract class BaseEntity' in result or '<<abstract>>' in result
    
    def test_class_diagram_stereotypes(self, generator):
        """Test that stereotypes are properly generated"""
        schema = {
            'python': [
                {'class': 'MyInterface', 'type': 'interface', 'methods': []},
                {'class': 'MyAbstract', 'type': 'abstract', 'fields': []},
                {'class': 'MyEnum', 'type': 'enum', 'values': ['A', 'B']}
            ],
            'relations': []
        }
        
        result = generator.generate(schema, 'class')
        
        # Check stereotypes
        assert '<<interface>>' in result or 'interface MyInterface' in result
        assert '<<abstract>>' in result or 'abstract class MyAbstract' in result
        assert '<<enumeration>>' in result or 'enum MyEnum' in result
    
    def test_class_diagram_visibility(self, generator):
        """Test visibility modifiers in class diagrams"""
        # Create generator with show_private=True to test all visibilities
        generator_with_private = PlantUMLGenerator()
        generator_with_private.class_builder.show_private = True
        
        schema = {
            'python': [
                {
                    'class': 'TestClass',
                    'fields': [
                        {'name': 'public_field', 'visibility': 'public'},
                        {'name': 'private_field', 'visibility': 'private'},
                        {'name': 'protected_field', 'visibility': 'protected'},
                        {'name': 'package_field', 'visibility': 'package'}
                    ],
                    'methods': [
                        {'name': 'public_method', 'visibility': 'public'},
                        {'name': 'private_method', 'visibility': 'private'}
                    ]
                }
            ],
            'relations': []
        }
        
        result = generator_with_private.generate(schema, 'class')
        
        # Check visibility symbols (now private should be included)
        assert '+ public_field' in result or '+public_field' in result
        assert '- private_field' in result or '-private_field' in result
        assert '# protected_field' in result or '#protected_field' in result
        assert '~ package_field' in result or '~package_field' in result
    
    def test_class_diagram_relationships(self, generator):
        """Test relationship arrows in class diagrams"""
        schema = {
            'python': [
                {'class': 'Child', 'methods': []},
                {'class': 'Parent', 'methods': []},
                {'class': 'Interface', 'type': 'interface', 'methods': []},
                {'class': 'Implementation', 'methods': []},
                {'class': 'Car', 'methods': []},
                {'class': 'Engine', 'methods': []},
                {'class': 'Dept', 'methods': []},
                {'class': 'Employee', 'methods': []},
                {'class': 'Client', 'methods': []},
                {'class': 'Service', 'methods': []},
                {'class': 'A', 'methods': []},
                {'class': 'B', 'methods': []}
            ],
            'relations': [
                {'from': 'Child', 'to': 'Parent', 'type': 'extends'},
                {'from': 'Implementation', 'to': 'Interface', 'type': 'implements'},
                {'from': 'Car', 'to': 'Engine', 'type': 'composition'},
                {'from': 'Dept', 'to': 'Employee', 'type': 'aggregation'},
                {'from': 'Client', 'to': 'Service', 'type': 'dependency'},
                {'from': 'A', 'to': 'B', 'type': 'association'}
            ]
        }
        
        result = generator.generate(schema, 'class')
        
        # Check relationship arrows
        assert '--|>' in result  # extends
        assert '..|>' in result  # implements
        assert '*--' in result or '--*' in result  # composition
        assert 'o--' in result or '--o' in result  # aggregation
        assert '..>' in result   # dependency
        assert '--' in result    # association
    
    def test_class_diagram_multiplicities(self, generator):
        """Test multiplicity notation in relationships"""
        schema = {
            'python': [
                {'class': 'Customer', 'methods': []},
                {'class': 'Order', 'methods': []},
                {'class': 'Item', 'methods': []}
            ],
            'relations': [
                {
                    'from': 'Customer',
                    'to': 'Order',
                    'type': 'association',
                    'multiplicity': {'from': '1', 'to': '0..*'}
                },
                {
                    'from': 'Order',
                    'to': 'Item',
                    'type': 'composition',
                    'multiplicity': {'from': '*', 'to': '1..*'}
                }
            ]
        }
        
        result = generator.generate(schema, 'class')
        
        # Check multiplicity notation
        assert '"1"' in result
        assert '"0..*"' in result or '"*"' in result
        assert '"1..*"' in result
    
    # ============================================================================
    # Test Sequence Diagram Generation
    # ============================================================================
    
    def test_generate_sequence_diagram(self, generator):
        """Test sequence diagram generation"""
        schema = {
            'endpoints': [
                {
                    'path': '/users',
                    'method': 'POST',
                    'controller': 'UserController',
                    'service': 'UserService',
                    'repository': 'UserRepository'
                }
            ]
        }
        
        result = generator.generate(schema, 'sequence')
        
        assert '@startuml' in result
        assert '@enduml' in result
        assert 'participant' in result or 'actor' in result
        assert 'UserController' in result
        assert '->' in result or '-->' in result
    
    def test_sequence_diagram_with_multiple_endpoints(self, generator):
        """Test sequence diagram with multiple API endpoints"""
        schema = {
            'endpoints': [
                {'path': '/users', 'method': 'GET', 'controller': 'UserController'},
                {'path': '/orders', 'method': 'POST', 'controller': 'OrderController'}
            ]
        }
        
        result = generator.generate(schema, 'sequence')
        
        assert 'UserController' in result
        assert 'OrderController' in result
        assert 'GET' in result or '/users' in result
        assert 'POST' in result or '/orders' in result
    
    # ============================================================================
    # Test Use Case Diagram Generation
    # ============================================================================
    
    def test_generate_use_case_diagram(self, generator):
        """Test use case diagram generation"""
        schema = {
            'endpoints': [
                {'path': '/login', 'method': 'POST'},
                {'path': '/profile', 'method': 'GET'},
                {'path': '/admin/users', 'method': 'GET'}
            ]
        }
        
        result = generator.generate(schema, 'usecase')
        
        assert '@startuml' in result
        assert '@enduml' in result
        assert 'actor' in result
        assert 'usecase' in result or '(' in result  # usecase notation
    
    def test_use_case_diagram_actors(self, generator):
        """Test that actors are generated in use case diagrams"""
        schema = {
            'endpoints': [
                {'path': '/public/data', 'method': 'GET'},
                {'path': '/admin/settings', 'method': 'POST'}
            ]
        }
        
        result = generator.generate(schema, 'usecase')
        
        # Check for actors
        assert 'actor' in result.lower()
        # Check for use cases
        assert 'usecase' in result.lower() or '(' in result
    
    # ============================================================================
    # Test State Diagram Generation
    # ============================================================================
    
    def test_generate_state_diagram(self, generator):
        """Test state diagram generation"""
        schema = {
            'python': [
                {
                    'class': 'Order',
                    'methods': [
                        {'name': 'create'},
                        {'name': 'confirm'},
                        {'name': 'ship'},
                        {'name': 'deliver'},
                        {'name': 'cancel'}
                    ]
                }
            ]
        }
        
        result = generator.generate(schema, 'state')
        
        assert '@startuml' in result
        assert '@enduml' in result
        assert 'state' in result or '[*]' in result  # state notation
    
    def test_state_diagram_transitions(self, generator):
        """Test state transitions in state diagrams"""
        schema = {
            'python': [
                {
                    'class': 'UserAccount',
                    'methods': [
                        {'name': 'activate'},
                        {'name': 'suspend'},
                        {'name': 'close'}
                    ]
                }
            ]
        }
        
        result = generator.generate(schema, 'state')
        
        # Check for state transitions
        assert '-->' in result or '->' in result
        assert '[*]' in result  # start/end state
    
    # ============================================================================
    # Test Activity Diagram Generation
    # ============================================================================
    
    def test_generate_activity_diagram(self, generator):
        """Test activity diagram generation"""
        schema = {
            'endpoints': [
                {'path': '/checkout', 'method': 'POST', 'controller': 'CheckoutController'}
            ]
        }
        
        result = generator.generate(schema, 'activity')
        
        assert '@startuml' in result
        assert '@enduml' in result
        assert 'start' in result.lower() or ':' in result  # activity notation
    
    def test_activity_diagram_flow(self, generator):
        """Test activity flow in activity diagrams"""
        schema = {
            'endpoints': [
                {'path': '/process', 'method': 'POST'}
            ]
        }
        
        result = generator.generate(schema, 'activity')
        
        # Check for activity flow elements
        assert ':' in result or 'activity' in result.lower()
        assert 'stop' in result.lower() or 'end' in result.lower() or '[*]' in result
    
    # ============================================================================
    # Test Edge Cases and Error Handling
    # ============================================================================
    
    def test_empty_schema(self, generator):
        """Test generation with empty schema"""
        schema = {'python': [], 'java': [], 'relations': []}
        result = generator.generate(schema, 'class')
        
        assert '@startuml' in result
        assert '@enduml' in result
        # Should still generate valid PlantUML even if empty
    
    def test_invalid_diagram_type(self, generator):
        """Test with invalid diagram type"""
        schema = {'python': []}
        
        # Should either raise exception or default to class diagram
        try:
            result = generator.generate(schema, 'invalid_type')
            # If no exception, should return valid PlantUML
            assert '@startuml' in result
            assert '@enduml' in result
        except (ValueError, KeyError):
            # Expected behavior: raise exception for invalid type
            pass
    
    def test_missing_fields_in_schema(self, generator):
        """Test with incomplete schema data"""
        schema = {
            'python': [
                {
                    'class': 'IncompleteClass'
                    # Missing fields and methods
                }
            ],
            'relations': []
        }
        
        result = generator.generate(schema, 'class')
        
        # Should handle gracefully
        assert '@startuml' in result
        assert '@enduml' in result
        assert 'IncompleteClass' in result
    
    def test_special_characters_in_names(self, generator):
        """Test handling of special characters in class/method names"""
        schema = {
            'python': [
                {
                    'class': 'User_Model',
                    'methods': [
                        {'name': '__init__', 'visibility': 'public'},
                        {'name': 'get_user_by_id', 'visibility': 'public'}
                    ]
                }
            ],
            'relations': []
        }
        
        result = generator.generate(schema, 'class')
        
        # Should preserve underscores and special chars
        assert 'User_Model' in result or 'User' in result
        assert '__init__' in result or 'init' in result
    
    def test_multi_language_schema(self, generator):
        """Test schema with multiple languages"""
        schema = {
            'python': [{'class': 'PythonClass', 'methods': []}],
            'java': [{'class': 'JavaClass', 'methods': []}],
            'typescript': [{'class': 'TypeScriptClass', 'methods': []}],
            'relations': []
        }
        
        result = generator.generate(schema, 'class')
        
        # Should include classes from all languages
        assert 'PythonClass' in result
        assert 'JavaClass' in result
        assert 'TypeScriptClass' in result
    
    def test_output_is_valid_plantuml_syntax(self, generator, sample_schema):
        """Test that output follows PlantUML syntax rules"""
        result = generator.generate(sample_schema, 'class')
        
        # Check basic syntax rules
        assert result.count('@startuml') == result.count('@enduml')
        assert result.count('@startuml') == 1
        
        # Should not have obvious syntax errors
        assert '@@' not in result  # double @ is invalid
        assert result.strip().startswith('@startuml')
        assert result.strip().endswith('@enduml')
    
    def test_theme_configuration(self, generator):
        """Test that theme is properly configured"""
        schema = {'python': [], 'relations': []}
        result = generator.generate(schema, 'class')
        
        # Check for theme configuration
        assert '!theme' in result or 'skinparam' in result
    
    def test_class_diagram_with_packages(self, generator):
        """Test package grouping in class diagrams"""
        schema = {
            'python': [
                {
                    'class': 'User',
                    'package': 'com.example.domain',
                    'methods': []
                },
                {
                    'class': 'UserService',
                    'package': 'com.example.service',
                    'methods': []
                }
            ],
            'relations': []
        }
        
        result = generator.generate(schema, 'class')
        
        # Check for package notation (if supported)
        assert 'User' in result
        assert 'UserService' in result
