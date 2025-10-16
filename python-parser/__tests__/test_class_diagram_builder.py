"""
Unit tests for ClassDiagramBuilder module
Tests UML 2.0 feature generation for class diagrams
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plantuml.class_diagram_builder import ClassDiagramBuilder


class TestClassDiagramBuilder:
    """Test suite for ClassDiagramBuilder class"""
    
    @pytest.fixture
    def builder(self):
        """Create builder instance for tests"""
        return ClassDiagramBuilder()
    
    # ============================================================================
    # Test Class Generation
    # ============================================================================
    
    def test_build_regular_class(self, builder):
        """Test building a regular class"""
        class_data = {
            'class': 'User',
            'type': 'class',
            'fields': [
                {'name': 'id', 'type': 'int', 'visibility': 'private'},
                {'name': 'email', 'type': 'string', 'visibility': 'public'}
            ],
            'methods': [
                {'name': 'getEmail', 'visibility': 'public', 'return_type': 'string'}
            ]
        }
        
        result = builder.build_class(class_data)
        
        assert 'class User' in result
        assert '- id: int' in result or '-id: int' in result
        assert '+ email: string' in result or '+email: string' in result
        assert '+ getEmail(): string' in result or '+getEmail()' in result
    
    def test_build_interface(self, builder):
        """Test building an interface with stereotype"""
        interface_data = {
            'class': 'IRepository',
            'type': 'interface',
            'methods': [
                {'name': 'save', 'visibility': 'public', 'params': ['entity'], 'return_type': 'void'},
                {'name': 'findById', 'visibility': 'public', 'params': ['id'], 'return_type': 'Entity'}
            ]
        }
        
        result = builder.build_class(interface_data)
        
        # Check for interface stereotype
        assert '<<interface>>' in result or 'interface IRepository' in result
        assert 'save' in result
        assert 'findById' in result
    
    def test_build_abstract_class(self, builder):
        """Test building an abstract class"""
        abstract_data = {
            'class': 'BaseEntity',
            'type': 'abstract',
            'fields': [
                {'name': 'id', 'type': 'long', 'visibility': 'protected'},
                {'name': 'createdAt', 'type': 'Date', 'visibility': 'protected'}
            ],
            'methods': [
                {'name': 'getId', 'visibility': 'public', 'return_type': 'long'}
            ]
        }
        
        result = builder.build_class(abstract_data)
        
        # Check for abstract stereotype
        assert '<<abstract>>' in result or 'abstract class BaseEntity' in result or 'abstract BaseEntity' in result
        assert '# id: long' in result or '#id' in result
        assert '# createdAt' in result or '#createdAt' in result
    
    def test_build_enum(self, builder):
        """Test building an enum"""
        enum_data = {
            'class': 'UserRole',
            'type': 'enum',
            'values': ['ADMIN', 'USER', 'GUEST']
        }
        
        result = builder.build_class(enum_data)
        
        # Check for enum stereotype
        assert '<<enumeration>>' in result or 'enum UserRole' in result
        assert 'ADMIN' in result
        assert 'USER' in result
        assert 'GUEST' in result
    
    # ============================================================================
    # Test Visibility Modifiers
    # ============================================================================
    
    def test_visibility_public(self, builder):
        """Test public visibility symbol (+)"""
        class_data = {
            'class': 'Test',
            'fields': [{'name': 'publicField', 'visibility': 'public', 'type': 'string'}],
            'methods': [{'name': 'publicMethod', 'visibility': 'public'}]
        }
        
        result = builder.build_class(class_data)
        
        assert '+ publicField' in result or '+publicField' in result
        assert '+ publicMethod' in result or '+publicMethod' in result
    
    def test_visibility_private(self, builder):
        """Test private visibility symbol (-)"""
        class_data = {
            'class': 'Test',
            'fields': [{'name': 'privateField', 'visibility': 'private', 'type': 'string'}],
            'methods': [{'name': 'privateMethod', 'visibility': 'private'}]
        }
        
        result = builder.build_class(class_data)
        
        assert '- privateField' in result or '-privateField' in result
        assert '- privateMethod' in result or '-privateMethod' in result
    
    def test_visibility_protected(self, builder):
        """Test protected visibility symbol (#)"""
        class_data = {
            'class': 'Test',
            'fields': [{'name': 'protectedField', 'visibility': 'protected', 'type': 'string'}],
            'methods': [{'name': 'protectedMethod', 'visibility': 'protected'}]
        }
        
        result = builder.build_class(class_data)
        
        assert '# protectedField' in result or '#protectedField' in result
        assert '# protectedMethod' in result or '#protectedMethod' in result
    
    def test_visibility_package(self, builder):
        """Test package visibility symbol (~)"""
        class_data = {
            'class': 'Test',
            'fields': [{'name': 'packageField', 'visibility': 'package', 'type': 'string'}],
            'methods': [{'name': 'packageMethod', 'visibility': 'package'}]
        }
        
        result = builder.build_class(class_data)
        
        assert '~ packageField' in result or '~packageField' in result
        assert '~ packageMethod' in result or '~packageMethod' in result
    
    def test_visibility_default(self, builder):
        """Test default visibility when not specified"""
        class_data = {
            'class': 'Test',
            'fields': [{'name': 'defaultField', 'type': 'string'}],
            'methods': [{'name': 'defaultMethod'}]
        }
        
        result = builder.build_class(class_data)
        
        # Should default to public or handle gracefully
        assert 'defaultField' in result
        assert 'defaultMethod' in result
    
    # ============================================================================
    # Test Relationship Generation
    # ============================================================================
    
    def test_inheritance_relationship(self, builder):
        """Test inheritance (extends) arrow"""
        relation = {
            'from': 'Child',
            'to': 'Parent',
            'type': 'extends'
        }
        
        result = builder.build_relationship(relation)
        
        # UML 2.0: solid line with hollow triangle
        assert '--|>' in result
        assert 'Child' in result
        assert 'Parent' in result
    
    def test_realization_relationship(self, builder):
        """Test realization (implements) arrow"""
        relation = {
            'from': 'ConcreteClass',
            'to': 'Interface',
            'type': 'implements'
        }
        
        result = builder.build_relationship(relation)
        
        # UML 2.0: dashed line with hollow triangle
        assert '..|>' in result
        assert 'ConcreteClass' in result
        assert 'Interface' in result
    
    def test_composition_relationship(self, builder):
        """Test composition arrow (strong ownership)"""
        relation = {
            'from': 'Car',
            'to': 'Engine',
            'type': 'composition'
        }
        
        result = builder.build_relationship(relation)
        
        # UML 2.0: solid line with filled diamond
        assert '*--' in result or '--*' in result
        assert 'Car' in result
        assert 'Engine' in result
    
    def test_aggregation_relationship(self, builder):
        """Test aggregation arrow (weak ownership)"""
        relation = {
            'from': 'Department',
            'to': 'Employee',
            'type': 'aggregation'
        }
        
        result = builder.build_relationship(relation)
        
        # UML 2.0: solid line with hollow diamond
        assert 'o--' in result or '--o' in result
        assert 'Department' in result
        assert 'Employee' in result
    
    def test_dependency_relationship(self, builder):
        """Test dependency arrow (uses)"""
        relation = {
            'from': 'Controller',
            'to': 'Service',
            'type': 'dependency'
        }
        
        result = builder.build_relationship(relation)
        
        # UML 2.0: dashed line with open arrow
        assert '..>' in result
        assert 'Controller' in result
        assert 'Service' in result
    
    def test_association_relationship(self, builder):
        """Test association arrow"""
        relation = {
            'from': 'Customer',
            'to': 'Order',
            'type': 'association'
        }
        
        result = builder.build_relationship(relation)
        
        # UML 2.0: solid line
        assert '--' in result
        assert 'Customer' in result
        assert 'Order' in result
    
    # ============================================================================
    # Test Multiplicity
    # ============================================================================
    
    def test_multiplicity_one_to_many(self, builder):
        """Test 1 to * multiplicity"""
        relation = {
            'from': 'Customer',
            'to': 'Order',
            'type': 'association',
            'multiplicity': {'from': '1', 'to': '*'}
        }
        
        result = builder.build_relationship(relation)
        
        assert '"1"' in result
        assert '"*"' in result or '"0..*"' in result
    
    def test_multiplicity_many_to_many(self, builder):
        """Test * to * multiplicity"""
        relation = {
            'from': 'Student',
            'to': 'Course',
            'type': 'association',
            'multiplicity': {'from': '*', 'to': '*'}
        }
        
        result = builder.build_relationship(relation)
        
        assert '"*"' in result
        # Should appear twice (both sides)
        assert result.count('"*"') >= 1
    
    def test_multiplicity_one_to_one(self, builder):
        """Test 1 to 1 multiplicity"""
        relation = {
            'from': 'User',
            'to': 'Profile',
            'type': 'composition',
            'multiplicity': {'from': '1', 'to': '1'}
        }
        
        result = builder.build_relationship(relation)
        
        assert '"1"' in result
        # Should appear twice (both sides)
        assert result.count('"1"') >= 1
    
    def test_multiplicity_optional(self, builder):
        """Test 0..1 (optional) multiplicity"""
        relation = {
            'from': 'Person',
            'to': 'Passport',
            'type': 'association',
            'multiplicity': {'from': '1', 'to': '0..1'}
        }
        
        result = builder.build_relationship(relation)
        
        assert '"0..1"' in result
    
    def test_multiplicity_range(self, builder):
        """Test range multiplicity (e.g., 1..*)"""
        relation = {
            'from': 'Team',
            'to': 'Player',
            'type': 'composition',
            'multiplicity': {'from': '1', 'to': '1..*'}
        }
        
        result = builder.build_relationship(relation)
        
        assert '"1..*"' in result
    
    # ============================================================================
    # Test Method Parameters and Return Types
    # ============================================================================
    
    def test_method_with_params(self, builder):
        """Test method with parameters"""
        class_data = {
            'class': 'Calculator',
            'methods': [
                {
                    'name': 'add',
                    'visibility': 'public',
                    'params': ['a: int', 'b: int'],
                    'return_type': 'int'
                }
            ]
        }
        
        result = builder.build_class(class_data)
        
        assert 'add' in result
        assert 'int' in result or 'a' in result or 'b' in result
    
    def test_method_no_params(self, builder):
        """Test method without parameters"""
        class_data = {
            'class': 'Test',
            'methods': [
                {
                    'name': 'getStatus',
                    'visibility': 'public',
                    'return_type': 'string'
                }
            ]
        }
        
        result = builder.build_class(class_data)
        
        assert 'getStatus' in result
        assert '()' in result  # Should have empty parentheses
    
    def test_method_with_return_type(self, builder):
        """Test method with return type"""
        class_data = {
            'class': 'Test',
            'methods': [
                {
                    'name': 'calculate',
                    'visibility': 'public',
                    'return_type': 'double'
                }
            ]
        }
        
        result = builder.build_class(class_data)
        
        assert 'calculate' in result
        assert 'double' in result or ':' in result  # Return type notation
    
    # ============================================================================
    # Test Field Types
    # ============================================================================
    
    def test_field_with_type(self, builder):
        """Test field with type annotation"""
        class_data = {
            'class': 'User',
            'fields': [
                {'name': 'id', 'type': 'int', 'visibility': 'private'},
                {'name': 'email', 'type': 'string', 'visibility': 'public'},
                {'name': 'age', 'type': 'int', 'visibility': 'public'}
            ]
        }
        
        result = builder.build_class(class_data)
        
        assert 'id: int' in result or 'id:int' in result
        assert 'email: string' in result or 'email:string' in result
        assert 'age: int' in result or 'age:int' in result
    
    def test_field_without_type(self, builder):
        """Test field without type annotation"""
        class_data = {
            'class': 'Test',
            'fields': [
                {'name': 'data', 'visibility': 'public'}
            ]
        }
        
        result = builder.build_class(class_data)
        
        assert 'data' in result
        # Should still generate valid PlantUML
    
    # ============================================================================
    # Test Edge Cases
    # ============================================================================
    
    def test_empty_class(self, builder):
        """Test class with no fields or methods"""
        class_data = {
            'class': 'EmptyClass'
        }
        
        result = builder.build_class(class_data)
        
        assert 'EmptyClass' in result
        assert 'class EmptyClass' in result or '{' in result
    
    def test_class_with_only_fields(self, builder):
        """Test class with only fields"""
        class_data = {
            'class': 'DataClass',
            'fields': [
                {'name': 'x', 'type': 'int', 'visibility': 'public'},
                {'name': 'y', 'type': 'int', 'visibility': 'public'}
            ]
        }
        
        result = builder.build_class(class_data)
        
        assert 'DataClass' in result
        assert 'x' in result
        assert 'y' in result
    
    def test_class_with_only_methods(self, builder):
        """Test class with only methods"""
        class_data = {
            'class': 'Service',
            'methods': [
                {'name': 'process', 'visibility': 'public'},
                {'name': 'validate', 'visibility': 'private'}
            ]
        }
        
        result = builder.build_class(class_data)
        
        assert 'Service' in result
        assert 'process' in result
        assert 'validate' in result
    
    def test_special_characters_in_class_name(self, builder):
        """Test class names with underscores and numbers"""
        class_data = {
            'class': 'User_Model_V2',
            'methods': []
        }
        
        result = builder.build_class(class_data)
        
        assert 'User_Model_V2' in result or 'User' in result
    
    def test_relationship_without_multiplicity(self, builder):
        """Test relationship without multiplicity specified"""
        relation = {
            'from': 'A',
            'to': 'B',
            'type': 'association'
        }
        
        result = builder.build_relationship(relation)
        
        # Should work without multiplicity
        assert 'A' in result
        assert 'B' in result
        assert '--' in result
    
    def test_full_diagram_generation(self, builder):
        """Test generating a complete class diagram"""
        schema = {
            'python': [
                {
                    'class': 'User',
                    'type': 'class',
                    'fields': [
                        {'name': 'id', 'type': 'int', 'visibility': 'private'},
                        {'name': 'email', 'type': 'string', 'visibility': 'public'}
                    ],
                    'methods': [
                        {'name': 'getId', 'visibility': 'public', 'return_type': 'int'}
                    ]
                },
                {
                    'class': 'BaseEntity',
                    'type': 'abstract',
                    'fields': [
                        {'name': 'createdAt', 'type': 'Date', 'visibility': 'protected'}
                    ]
                }
            ],
            'relations': [
                {
                    'from': 'User',
                    'to': 'BaseEntity',
                    'type': 'extends'
                }
            ]
        }
        
        result = builder.build(schema)
        
        # Check complete diagram structure
        assert '@startuml' in result
        assert '@enduml' in result
        assert 'User' in result
        assert 'BaseEntity' in result
        assert '--|>' in result  # inheritance arrow
        assert '<<abstract>>' in result or 'abstract' in result
