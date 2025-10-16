"""
PlantUML Class Diagram Builder
Converts code analysis schema to PlantUML class diagram syntax
"""

import logging
from typing import Dict, Any, List, Set, Optional

logger = logging.getLogger(__name__)


class ClassDiagramBuilder:
    """
    Builds PlantUML class diagrams from code analysis schema.
    Handles classes, interfaces, relationships, and UML 2.0 features.
    """
    
    # PlantUML relationship mappings
    RELATIONSHIP_ARROWS = {
        'extends': '--|>',        # Inheritance (generalization)
        'implements': '..|>',     # Interface implementation (realization)
        'composition': '*--',     # Composition (filled diamond)
        'aggregation': 'o--',     # Aggregation (hollow diamond)
        'uses': '-->',            # Dependency / Usage
        'dependency': '..>',      # Dependency (dashed)
        'association': '--',      # Association
    }
    
    # Visibility modifiers
    VISIBILITY = {
        'public': '+',
        'private': '-',
        'protected': '#',
        'package': '~'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize class diagram builder.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.theme = self.config.get('theme', 'plain')
        self.show_methods = self.config.get('show_methods', True)
        self.show_fields = self.config.get('show_fields', True)
        self.show_private = self.config.get('show_private', True)
    
    def build(
        self, 
        schema: Dict[str, Any],
        language_filter: Optional[List[str]] = None
    ) -> str:
        """
        Build complete PlantUML class diagram.
        
        Args:
            schema: Analysis schema
            language_filter: Optional list of languages to include
        
        Returns:
            PlantUML syntax string
        """
        logger.info("Building PlantUML class diagram")
        
        lines = self._build_header()
        
        # Track all class names for relationship validation
        all_classes = set()
        
        # Build classes by language
        languages = language_filter if language_filter else [
            'python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c'
        ]
        
        for lang in languages:
            classes = schema.get(lang, [])
            if classes:
                lines.append(f"' {lang.upper()} Classes")
                for cls in classes:
                    class_lines = self._build_class(cls, lang)
                    lines.extend(class_lines)
                    all_classes.add(cls.get('class'))
                lines.append("")
        
        # Build relationships
        relations = schema.get('relations', [])
        if relations:
            lines.append("' Relationships")
            relationship_lines = self._build_relationships(relations, all_classes)
            lines.extend(relationship_lines)
            lines.append("")
        
        # Add footer
        lines.extend(self._build_footer())
        
        result = "\n".join(lines)
        logger.info(f"Generated PlantUML with {len(all_classes)} classes and {len(relations)} relationships")
        
        return result

    # ------------------------------------------------------------------
    # Backwards-compatible helpers used by unit tests and external callers
    # ------------------------------------------------------------------

    def build_class(self, cls: Dict[str, Any], language: str = 'python') -> str:
        """Public helper that returns a single class definition as PlantUML."""
        lines = self._build_class(cls, language)
        return "\n".join(lines)

    def build_relationship(
        self,
        relation: Dict[str, Any],
        all_classes: Optional[Set[str]] = None
    ) -> str:
        """Public helper that returns a single relationship definition."""
        if all_classes is None:
            all_classes = {relation.get('from'), relation.get('to')}
        lines = self._build_relationships([relation], all_classes)
        return lines[0] if lines else ""
    
    def _build_header(self) -> List[str]:
        """Build diagram header with configuration."""
        return [
            "@startuml",
            f"!theme {self.theme}",
            "",
            "' PlantUML Class Diagram",
            "' Generated from code analysis",
            "",
            "' Configuration",
            "skinparam classAttributeIconSize 0",
            "skinparam shadowing false",
            "skinparam roundcorner 5",
            "skinparam class {",
            "  BackgroundColor White",
            "  BorderColor Black",
            "  ArrowColor Black",
            "}",
            ""
        ]
    
    def _build_footer(self) -> List[str]:
        """Build diagram footer."""
        return ["@enduml"]
    
    def _build_class(self, cls: Dict[str, Any], language: str) -> List[str]:
        """
        Build single class definition.
        
        Args:
            cls: Class dictionary from schema
            language: Programming language
        
        Returns:
            List of PlantUML lines
        """
        lines = []
        
        class_name = cls.get('class', 'UnnamedClass')
        # Support both 'stereotype' (from analyze.py) and 'type' (for test compatibility)
        stereotype = cls.get('stereotype') or cls.get('type', 'class')
        is_abstract = cls.get('abstract', False)
        package = cls.get('package') or cls.get('namespace')
        
        # Build class declaration with stereotype
        class_keyword = self._get_class_keyword(stereotype, is_abstract)
        
        # Add stereotype annotation if needed
        stereotype_annotation = ""
        if stereotype == 'interface':
            stereotype_annotation = " <<interface>>"
        elif stereotype == 'abstract' or is_abstract:
            stereotype_annotation = " <<abstract>>"
        elif stereotype == 'enum':
            stereotype_annotation = " <<enumeration>>"
        elif stereotype == 'struct':
            stereotype_annotation = " <<struct>>"
        
        lines.append(f"{class_keyword} {class_name}{stereotype_annotation} {{")
        
        # Add fields
        if self.show_fields:
            fields = cls.get('fields', [])
            if fields:
                for field in fields:
                    field_line = self._format_field(field)
                    if field_line:
                        lines.append(f"  {field_line}")
                
                # Separator between fields and methods
                if cls.get('methods'):
                    lines.append("  ..")
        
        # Add methods
        if self.show_methods:
            methods = cls.get('methods', [])
            if methods:
                for method in methods:
                    method_line = self._format_method(method)
                    if method_line:
                        lines.append(f"  {method_line}")

        # Add enum values if present
        if stereotype == 'enum':
            for value in cls.get('values', []) or []:
                lines.append(f"  {value}")
        
        lines.append("}")
        
        # Add package/namespace annotation
        if package:
            lines.append(f"note right of {class_name}")
            lines.append(f"  Package: {package}")
            lines.append("end note")
        
        lines.append("")
        
        return lines
    
    def _get_class_keyword(self, stereotype: str, is_abstract: bool) -> str:
        """
        Get appropriate PlantUML keyword for class type.
        
        Args:
            stereotype: Class stereotype
            is_abstract: Whether class is abstract
        
        Returns:
            PlantUML keyword
        """
        if stereotype == 'interface':
            return 'interface'
        elif stereotype == 'abstract' or is_abstract:
            return 'abstract class'
        elif stereotype == 'enum':
            return 'enum'
        else:
            return 'class'
    
    def _format_field(self, field) -> Optional[str]:
        """
        Format field with visibility modifier.
        
        Args:
            field: Field dict (e.g., {'name': 'id', 'type': 'int', 'visibility': 'private'})
                   or field string (e.g., "name: String" or "-email: String")
        
        Returns:
            Formatted field line or None if should be hidden
        """
        # Handle dictionary input (from schema)
        if isinstance(field, dict):
            name = field.get('name', '')
            field_type = field.get('type', '')
            visibility = field.get('visibility', 'public')
            
            # Map visibility to symbol
            visibility_map = {
                'public': '+',
                'private': '-',
                'protected': '#',
                'package': '~'
            }
            vis_symbol = visibility_map.get(visibility, '+')
            
            # Filter private fields if configured
            if not self.show_private and vis_symbol == '-':
                return None
            
            # Format: + name: type
            if field_type:
                return f"{vis_symbol} {name}: {field_type}"
            else:
                return f"{vis_symbol} {name}"
        
        # Handle string input (legacy format)
        field = field.strip()
        if not field:
            return None
        
        # Check if field already has visibility
        if field[0] in ['+', '-', '#', '~']:
            visibility = field[0]
            field_rest = field[1:].strip()
            
            # Filter private fields if configured
            if not self.show_private and visibility == '-':
                return None
            
            return f"{visibility} {field_rest}"
        
        # No visibility specified, default to public
        return f"+ {field}"
    
    def _format_method(self, method) -> Optional[str]:
        """
        Format method with visibility modifier.
        
        Args:
            method: Method dict (e.g., {'name': 'getId', 'visibility': 'public', 'return_type': 'int', 'params': ['self']})
                    or method string (e.g., "getName()" or "+setName(name: String): void")
        
        Returns:
            Formatted method line or None if should be hidden
        """
        # Handle dictionary input (from schema)
        if isinstance(method, dict):
            name = method.get('name', '')
            visibility = method.get('visibility', 'public')
            return_type = method.get('return_type', '')
            params = method.get('params', [])
            
            # Map visibility to symbol
            visibility_map = {
                'public': '+',
                'private': '-',
                'protected': '#',
                'package': '~'
            }
            vis_symbol = visibility_map.get(visibility, '+')
            
            # Filter private methods if configured
            if not self.show_private and vis_symbol == '-':
                return None
            
            # Format parameters (filter out 'self' for Python)
            param_list = [p for p in params if p != 'self']
            param_str = ', '.join(param_list) if param_list else ''
            
            # Format: + methodName(params): returnType
            method_signature = f"{name}({param_str})"
            if return_type:
                method_signature += f": {return_type}"
            
            return f"{vis_symbol} {method_signature}"
        
        # Handle string input (legacy format)
        method = method.strip()
        if not method:
            return None
        
        # Check if method already has visibility
        if method[0] in ['+', '-', '#', '~']:
            visibility = method[0]
            method_rest = method[1:].strip()
            
            # Filter private methods if configured
            if not self.show_private and visibility == '-':
                return None
            
            return f"{visibility} {method_rest}"
        
        # No visibility specified, default to public for methods
        return f"+ {method}"
    
    def _build_relationships(
        self, 
        relations: List[Dict[str, Any]],
        all_classes: Set[str]
    ) -> List[str]:
        """
        Build relationship definitions.
        
        Args:
            relations: List of relationship dictionaries
            all_classes: Set of all class names for validation
        
        Returns:
            List of PlantUML relationship lines
        """
        lines = []
        seen_relations = set()
        
        for relation in relations:
            from_class = relation.get('from')
            to_class = relation.get('to')
            rel_type = relation.get('type', 'association')
            
            # Validate classes exist
            if not from_class or not to_class:
                continue
            
            if from_class not in all_classes or to_class not in all_classes:
                logger.debug(f"Skipping relation {from_class} -> {to_class}: class not found")
                continue
            
            # Avoid duplicate relationships
            rel_key = (from_class, to_class, rel_type)
            if rel_key in seen_relations:
                continue
            seen_relations.add(rel_key)
            
            # Get appropriate arrow
            arrow = self.RELATIONSHIP_ARROWS.get(rel_type, '--')
            
            # Add multiplicity if available (support both formats)
            multiplicity = relation.get('multiplicity', {})
            if isinstance(multiplicity, dict):
                multiplicity_from = multiplicity.get('from', '')
                multiplicity_to = multiplicity.get('to', '')
            else:
                multiplicity_from = relation.get('multiplicity_from', '')
                multiplicity_to = relation.get('multiplicity_to', '')
            
            # Build relationship line
            rel_line = f"{from_class} "
            
            if multiplicity_from:
                rel_line += f'"{multiplicity_from}" '
            
            rel_line += arrow
            
            if multiplicity_to:
                rel_line += f' "{multiplicity_to}"'
            
            rel_line += f" {to_class}"
            
            # Add label if available
            label = relation.get('label', '')
            if label:
                rel_line += f" : {label}"
            
            lines.append(rel_line)
        
        return lines
    
    def _sanitize_class_name(self, name: str) -> str:
        """
        Sanitize class name for PlantUML.
        
        Args:
            name: Original class name
        
        Returns:
            Sanitized name
        """
        # Remove special characters that might break PlantUML
        name = name.replace('<', '_').replace('>', '_')
        name = name.replace('[', '_').replace(']', '_')
        name = name.replace('(', '_').replace(')', '_')
        name = name.replace(' ', '_')
        return name
    
    def _get_field_visibility(self, field: str) -> str:
        """
        Extract visibility from field string.
        
        Args:
            field: Field string
        
        Returns:
            Visibility modifier ('+', '-', '#', '~')
        """
        field = field.strip()
        if field and field[0] in ['+', '-', '#', '~']:
            return field[0]
        return '+'  # Default to public
    
    def validate_relations(
        self, 
        relations: List[Dict[str, Any]],
        all_classes: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Validate and filter relationships.
        
        Args:
            relations: List of relationships
            all_classes: Set of all class names
        
        Returns:
            List of valid relationships
        """
        valid_relations = []
        
        for relation in relations:
            from_class = relation.get('from')
            to_class = relation.get('to')
            
            if from_class in all_classes and to_class in all_classes:
                valid_relations.append(relation)
            else:
                logger.debug(f"Invalid relation: {from_class} -> {to_class}")
        
        return valid_relations
