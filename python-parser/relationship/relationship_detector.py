"""
Relationship Detector Module
Centralized relationship inference and detection across all languages
"""

import logging
from typing import Dict, List, Set
from constants import RELATIONSHIP_TYPES

logger = logging.getLogger(__name__)


class RelationshipDetector:
    """
    Detects and infers relationships between classes across all languages.
    Handles relationship validation, deduplication, and enrichment.
    """
    
    def __init__(self):
        self.relationships: List[Dict] = []
        self.all_classes: Set[str] = set()
    
    def set_classes(self, classes: List[Dict]):
        """
        Set the list of all known classes.
        
        Args:
            classes: List of class dictionaries
        """
        self.all_classes = {cls['class'] for cls in classes}
        logger.info(f"Loaded {len(self.all_classes)} classes for relationship detection")
    
    def add_relationships(self, relationships: List[Dict]):
        """
        Add relationships to the detector.
        
        Args:
            relationships: List of relationship dictionaries
        """
        self.relationships.extend(relationships)
    
    def validate_relationships(self) -> List[Dict]:
        """
        Validate all relationships against known classes.
        
        Returns:
            List of valid relationships
        """
        valid_relationships = []
        
        for rel in self.relationships:
            if self._is_valid_relationship(rel):
                valid_relationships.append(rel)
            else:
                logger.debug(
                    f"Filtered invalid relationship: {rel.get('from')} -> {rel.get('to')} "
                    f"({rel.get('type')})"
                )
        
        logger.info(
            f"Validated relationships: {len(valid_relationships)}/{len(self.relationships)} valid"
        )
        return valid_relationships
    
    def _is_valid_relationship(self, rel: Dict) -> bool:
        """
        Check if a relationship is valid.
        
        Args:
            rel: Relationship dictionary
            
        Returns:
            True if valid, False otherwise
        """
        from_class = rel.get('from')
        to_class = rel.get('to')
        rel_type = rel.get('type')
        
        # Must have all required fields
        if not all([from_class, to_class, rel_type]):
            return False
        
        # Type must be valid
        if rel_type not in RELATIONSHIP_TYPES.values():
            return False
        
        # Both classes must exist (except for dependencies which might be external)
        if rel_type != 'dependency':
            if from_class not in self.all_classes or to_class not in self.all_classes:
                return False
        
        # No self-relationships (except certain types)
        if from_class == to_class and rel_type not in ['dependency']:
            return False
        
        return True
    
    def deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """
        Remove duplicate relationships.
        
        Args:
            relationships: List of relationships
            
        Returns:
            Deduplicated list
        """
        unique_rels = []
        seen = set()
        
        for rel in relationships:
            key = (rel.get('from'), rel.get('to'), rel.get('type'))
            if key not in seen:
                seen.add(key)
                unique_rels.append(rel)
        
        logger.info(
            f"Deduplicated relationships: {len(unique_rels)}/{len(relationships)} unique"
        )
        return unique_rels
    
    def infer_additional_relationships(self, classes: List[Dict]) -> List[Dict]:
        """
        Infer additional relationships based on heuristics.
        
        Args:
            classes: List of class dictionaries
            
        Returns:
            List of inferred relationships
        """
        inferred = []
        
        # Build field type mapping
        field_types = {}
        for cls in classes:
            class_name = cls['class']
            field_types[class_name] = set()
            
            for field in cls.get('fields', []):
                # Extract type from "fieldName: Type" format
                if ':' in field:
                    field_type = field.split(':')[1].strip()
                    # Remove generics
                    field_type = field_type.split('<')[0].split('[')[0].strip()
                    field_types[class_name].add(field_type)
        
        # Infer composition relationships from field types
        for class_name, types in field_types.items():
            for field_type in types:
                if field_type in self.all_classes and field_type != class_name:
                    inferred.append({
                        'from': class_name,
                        'to': field_type,
                        'type': 'composition',
                        'source': 'inferred'
                    })
        
        # Infer interface/abstract implementations
        for cls in classes:
            class_name = cls['class']
            
            # If class has abstract=False but inherits from abstract class, it implements it
            if not cls.get('abstract', False):
                for rel in self.relationships:
                    if rel.get('to') == class_name and rel.get('type') == 'extends':
                        base_class = rel.get('from')
                        # Find base class
                        base_cls_dict = next(
                            (c for c in classes if c['class'] == base_class), None
                        )
                        if base_cls_dict and base_cls_dict.get('abstract', False):
                            inferred.append({
                                'from': base_class,
                                'to': class_name,
                                'type': 'implements',
                                'source': 'inferred'
                            })
        
        logger.info(f"Inferred {len(inferred)} additional relationships")
        return inferred
    
    def categorize_relationships(self, relationships: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize relationships by type.
        
        Args:
            relationships: List of relationships
            
        Returns:
            Dictionary mapping relationship type to list of relationships
        """
        categorized = {rel_type: [] for rel_type in RELATIONSHIP_TYPES}
        
        for rel in relationships:
            rel_type = rel.get('type')
            if rel_type in categorized:
                categorized[rel_type].append(rel)
        
        # Log statistics
        for rel_type, rels in categorized.items():
            if rels:
                logger.info(f"  {rel_type}: {len(rels)}")
        
        return categorized
    
    def filter_relationships_by_strength(
        self, relationships: List[Dict], min_strength: str = 'weak'
    ) -> List[Dict]:
        """
        Filter relationships by strength.
        
        Args:
            relationships: List of relationships
            min_strength: Minimum strength ('strong', 'medium', 'weak')
            
        Returns:
            Filtered list
        """
        strength_order = ['strong', 'medium', 'weak']
        min_idx = strength_order.index(min_strength)
        
        strength_map = {
            'extends': 'strong',
            'implements': 'strong',
            'composition': 'medium',
            'aggregation': 'medium',
            'association': 'medium',
            'uses': 'weak',
            'dependency': 'weak',
            'creates': 'weak'
        }
        
        filtered = []
        for rel in relationships:
            rel_type = rel.get('type')
            strength = strength_map.get(rel_type, 'weak')
            strength_idx = strength_order.index(strength)
            
            if strength_idx <= min_idx:
                filtered.append(rel)
        
        logger.info(
            f"Filtered relationships by strength ({min_strength}): "
            f"{len(filtered)}/{len(relationships)}"
        )
        return filtered
    
    def get_class_relationships(self, class_name: str) -> Dict[str, List[Dict]]:
        """
        Get all relationships for a specific class.
        
        Args:
            class_name: Name of the class
            
        Returns:
            Dictionary with 'incoming' and 'outgoing' relationships
        """
        incoming = []
        outgoing = []
        
        for rel in self.relationships:
            if rel.get('from') == class_name:
                outgoing.append(rel)
            if rel.get('to') == class_name:
                incoming.append(rel)
        
        return {
            'incoming': incoming,
            'outgoing': outgoing,
            'total': len(incoming) + len(outgoing)
        }
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependencies between classes.
        
        Returns:
            List of circular dependency chains
        """
        # Build adjacency list
        graph = {}
        for rel in self.relationships:
            if rel.get('type') in ['extends', 'implements', 'composition', 'dependency']:
                from_class = rel.get('from')
                to_class = rel.get('to')
                
                if from_class not in graph:
                    graph[from_class] = []
                graph[from_class].append(to_class)
        
        # Find cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        if cycles:
            logger.warning(f"Detected {len(cycles)} circular dependencies")
        
        return cycles
    
    def get_relationship_statistics(self) -> Dict:
        """
        Get statistics about detected relationships.
        
        Returns:
            Dictionary with statistics
        """
        categorized = self.categorize_relationships(self.relationships)
        
        stats = {
            'total_relationships': len(self.relationships),
            'by_type': {k: len(v) for k, v in categorized.items() if v},
            'total_classes': len(self.all_classes),
            'circular_dependencies': len(self.detect_circular_dependencies())
        }
        
        return stats
