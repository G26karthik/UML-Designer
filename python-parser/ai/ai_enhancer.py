"""
AI Enhancer Module
Uses LLM/AI to enhance code analysis with intelligent relationship inference
"""

import logging
import json
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AIEnhancer:
    """
    Enhances code analysis using AI/LLM capabilities.
    Provides intelligent relationship inference, design pattern detection,
    and architectural insights.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize AI enhancer.
        
        Args:
            api_key: OpenAI API key (optional, can use environment variable)
            model: Model to use (gpt-4, gpt-3.5-turbo, etc.)
        """
        self.api_key = api_key
        self.model = model
        self.enabled = bool(api_key)
        
        if not self.enabled:
            logger.warning("AI enhancer initialized without API key - running in disabled mode")
    
    def enhance_relationships(
        self, 
        classes: List[Dict], 
        relationships: List[Dict],
        source_code: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Use AI to infer additional relationships that weren't detected by static analysis.
        
        Args:
            classes: List of class dictionaries
            relationships: List of existing relationships
            source_code: Optional dict mapping class names to source code
            
        Returns:
            List of AI-inferred relationships with confidence scores
        """
        if not self.enabled:
            logger.debug("AI enhancement disabled - skipping")
            return []
        
        try:
            # Prepare context for LLM
            context = self._prepare_relationship_context(classes, relationships, source_code)
            
            # Generate prompt
            prompt = self._create_relationship_prompt(context)
            
            # Call LLM
            response = self._call_llm(prompt)
            
            # Parse response
            inferred_relationships = self._parse_relationship_response(response)
            
            logger.info(f"AI inferred {len(inferred_relationships)} additional relationships")
            return inferred_relationships
            
        except Exception as e:
            logger.error(f"Error in AI relationship enhancement: {e}")
            return []
    
    def detect_design_patterns(self, classes: List[Dict], relationships: List[Dict]) -> List[Dict]:
        """
        Detect design patterns used in the codebase.
        
        Args:
            classes: List of class dictionaries
            relationships: List of relationships
            
        Returns:
            List of detected design patterns with confidence scores
        """
        if not self.enabled:
            return []
        
        try:
            context = self._prepare_pattern_context(classes, relationships)
            prompt = self._create_pattern_detection_prompt(context)
            response = self._call_llm(prompt)
            patterns = self._parse_pattern_response(response)
            
            logger.info(f"AI detected {len(patterns)} design patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error in design pattern detection: {e}")
            return []
    
    def suggest_refactoring(self, classes: List[Dict], relationships: List[Dict]) -> List[Dict]:
        """
        Suggest potential refactoring opportunities.
        
        Args:
            classes: List of class dictionaries
            relationships: List of relationships
            
        Returns:
            List of refactoring suggestions with rationale
        """
        if not self.enabled:
            return []
        
        try:
            context = self._prepare_refactoring_context(classes, relationships)
            prompt = self._create_refactoring_prompt(context)
            response = self._call_llm(prompt)
            suggestions = self._parse_refactoring_response(response)
            
            logger.info(f"AI generated {len(suggestions)} refactoring suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error in refactoring suggestions: {e}")
            return []
    
    def analyze_architecture(self, classes: List[Dict], relationships: List[Dict]) -> Dict:
        """
        Analyze overall architecture and provide insights.
        
        Args:
            classes: List of class dictionaries
            relationships: List of relationships
            
        Returns:
            Dictionary with architectural insights
        """
        if not self.enabled:
            return {}
        
        try:
            context = self._prepare_architecture_context(classes, relationships)
            prompt = self._create_architecture_prompt(context)
            response = self._call_llm(prompt)
            insights = self._parse_architecture_response(response)
            
            logger.info("AI generated architectural insights")
            return insights
            
        except Exception as e:
            logger.error(f"Error in architecture analysis: {e}")
            return {}
    
    def _prepare_relationship_context(
        self, 
        classes: List[Dict], 
        relationships: List[Dict],
        source_code: Optional[Dict[str, str]]
    ) -> Dict:
        """Prepare context for relationship inference"""
        # Extract class names and their members
        class_info = {}
        for cls in classes:
            class_info[cls['class']] = {
                'fields': cls.get('fields', []),
                'methods': cls.get('methods', []),
                'stereotype': cls.get('stereotype', 'class'),
                'package': cls.get('package', '')
            }
        
        # Group existing relationships by type
        rel_by_type = {}
        for rel in relationships:
            rel_type = rel.get('type')
            if rel_type not in rel_by_type:
                rel_by_type[rel_type] = []
            rel_by_type[rel_type].append(f"{rel['from']} -> {rel['to']}")
        
        return {
            'classes': class_info,
            'existing_relationships': rel_by_type,
            'source_code': source_code or {},
            'class_count': len(classes),
            'relationship_count': len(relationships)
        }
    
    def _create_relationship_prompt(self, context: Dict) -> str:
        """Create prompt for relationship inference"""
        prompt = f"""Analyze the following codebase structure and infer additional relationships that might exist between classes.

Number of classes: {context['class_count']}
Number of existing relationships: {context['relationship_count']}

Classes and their members:
"""
        
        # Add class information (limit to prevent token overflow)
        for class_name, info in list(context['classes'].items())[:20]:
            prompt += f"\nClass: {class_name} ({info['stereotype']})\n"
            if info['fields']:
                prompt += f"  Fields: {', '.join(info['fields'][:5])}\n"
            if info['methods']:
                prompt += f"  Methods: {', '.join(info['methods'][:5])}\n"
        
        prompt += f"\nExisting relationships:\n"
        for rel_type, rels in context['existing_relationships'].items():
            prompt += f"\n{rel_type.upper()}:\n"
            for rel in rels[:10]:
                prompt += f"  - {rel}\n"
        
        prompt += """
Based on the class names, methods, fields, and existing relationships, infer additional relationships that are likely to exist.

Consider:
1. Classes with similar names might have relationships
2. Method names suggesting operations on other classes
3. Field types that reference other classes
4. Common design patterns (Factory, Observer, Strategy, etc.)

Return a JSON array of inferred relationships with this structure:
[
  {
    "from": "ClassName1",
    "to": "ClassName2",
    "type": "composition|aggregation|association|uses",
    "confidence": 0.0-1.0,
    "reasoning": "Why this relationship is likely"
  }
]

Only include relationships with confidence > 0.6.
"""
        return prompt
    
    def _prepare_pattern_context(self, classes: List[Dict], relationships: List[Dict]) -> Dict:
        """Prepare context for pattern detection"""
        return {
            'classes': [
                {
                    'name': cls['class'],
                    'stereotype': cls.get('stereotype'),
                    'abstract': cls.get('abstract', False),
                    'method_count': len(cls.get('methods', [])),
                    'field_count': len(cls.get('fields', []))
                }
                for cls in classes
            ],
            'relationships': [
                {
                    'from': rel['from'],
                    'to': rel['to'],
                    'type': rel['type']
                }
                for rel in relationships
            ]
        }
    
    def _create_pattern_detection_prompt(self, context: Dict) -> str:
        """Create prompt for design pattern detection"""
        prompt = f"""Analyze the following codebase structure and identify design patterns.

Classes ({len(context['classes'])}):
"""
        
        for cls in context['classes'][:30]:
            prompt += f"  - {cls['name']} ({'abstract' if cls['abstract'] else cls['stereotype']}): "
            prompt += f"{cls['method_count']} methods, {cls['field_count']} fields\n"
        
        prompt += f"\nRelationships ({len(context['relationships'])}):\n"
        for rel in context['relationships'][:50]:
            prompt += f"  - {rel['from']} --{rel['type']}--> {rel['to']}\n"
        
        prompt += """
Identify design patterns present in this codebase.

Common patterns to look for:
- Creational: Singleton, Factory, Builder, Prototype
- Structural: Adapter, Decorator, Facade, Proxy
- Behavioral: Observer, Strategy, Command, Template Method

Return a JSON array:
[
  {
    "pattern": "PatternName",
    "confidence": 0.0-1.0,
    "classes_involved": ["Class1", "Class2"],
    "description": "How the pattern is implemented"
  }
]

Only include patterns with confidence > 0.7.
"""
        return prompt
    
    def _prepare_refactoring_context(self, classes: List[Dict], relationships: List[Dict]) -> Dict:
        """Prepare context for refactoring suggestions"""
        # Find classes with many relationships (god classes)
        class_rel_count = {}
        for rel in relationships:
            class_rel_count[rel['from']] = class_rel_count.get(rel['from'], 0) + 1
            class_rel_count[rel['to']] = class_rel_count.get(rel['to'], 0) + 1
        
        # Find classes with many methods (large classes)
        large_classes = [
            cls for cls in classes 
            if len(cls.get('methods', [])) > 10
        ]
        
        return {
            'total_classes': len(classes),
            'class_relationship_counts': class_rel_count,
            'large_classes': [cls['class'] for cls in large_classes],
            'relationships': relationships
        }
    
    def _create_refactoring_prompt(self, context: Dict) -> str:
        """Create prompt for refactoring suggestions"""
        prompt = f"""Analyze this codebase structure and suggest refactoring opportunities.

Total classes: {context['total_classes']}

Classes with many relationships (potential God classes):
"""
        
        sorted_classes = sorted(
            context['class_relationship_counts'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        for class_name, count in sorted_classes:
            prompt += f"  - {class_name}: {count} relationships\n"
        
        if context['large_classes']:
            prompt += f"\nLarge classes (>10 methods):\n"
            for cls in context['large_classes'][:10]:
                prompt += f"  - {cls}\n"
        
        prompt += """
Suggest refactoring opportunities based on:
1. God classes (too many responsibilities)
2. Large classes (too many methods)
3. Tight coupling (many dependencies)
4. Missing abstractions

Return a JSON array:
[
  {
    "type": "ExtractClass|SplitClass|IntroduceInterface|ReduceCoupling",
    "target_classes": ["Class1"],
    "priority": "High|Medium|Low",
    "reasoning": "Why this refactoring would help",
    "benefits": "Expected improvements"
  }
]
"""
        return prompt
    
    def _prepare_architecture_context(self, classes: List[Dict], relationships: List[Dict]) -> Dict:
        """Prepare context for architecture analysis"""
        # Group classes by package/namespace
        packages = {}
        for cls in classes:
            pkg = cls.get('package', 'default')
            if pkg not in packages:
                packages[pkg] = []
            packages[pkg].append(cls['class'])
        
        return {
            'total_classes': len(classes),
            'total_relationships': len(relationships),
            'packages': packages,
            'relationship_types': self._count_relationship_types(relationships)
        }
    
    def _count_relationship_types(self, relationships: List[Dict]) -> Dict[str, int]:
        """Count relationships by type"""
        counts = {}
        for rel in relationships:
            rel_type = rel.get('type', 'unknown')
            counts[rel_type] = counts.get(rel_type, 0) + 1
        return counts
    
    def _create_architecture_prompt(self, context: Dict) -> str:
        """Create prompt for architecture analysis"""
        prompt = f"""Analyze the architecture of this codebase and provide insights.

Overview:
- Total classes: {context['total_classes']}
- Total relationships: {context['total_relationships']}
- Packages/modules: {len(context['packages'])}

Relationship distribution:
"""
        
        for rel_type, count in context['relationship_types'].items():
            prompt += f"  - {rel_type}: {count}\n"
        
        prompt += f"\nPackage distribution:\n"
        for pkg, classes in list(context['packages'].items())[:10]:
            prompt += f"  - {pkg}: {len(classes)} classes\n"
        
        prompt += """
Provide architectural insights as JSON:
{
  "architecture_style": "Layered|MVC|Microservices|Monolithic|...",
  "strengths": ["Strength 1", "Strength 2"],
  "weaknesses": ["Weakness 1", "Weakness 2"],
  "coupling_level": "Low|Medium|High",
  "cohesion_level": "Low|Medium|High",
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "overall_quality": 1-10
}
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM API (OpenAI).
        
        Args:
            prompt: Prompt to send
            
        Returns:
            LLM response text
        """
        if not self.enabled:
            return ""
        
        try:
            import openai
            
            # Set API key
            if self.api_key:
                openai.api_key = self.api_key
            
            # Call API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert software architect and code analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            logger.error("openai package not installed. Install with: pip install openai")
            return ""
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return ""
    
    def _parse_relationship_response(self, response: str) -> List[Dict]:
        """Parse LLM response for relationships"""
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON array found in LLM response")
                return []
            
            json_str = response[json_start:json_end]
            relationships = json.loads(json_str)
            
            # Add source marker
            for rel in relationships:
                rel['source'] = 'ai-inferred'
            
            return relationships
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing relationship JSON: {e}")
            return []
    
    def _parse_pattern_response(self, response: str) -> List[Dict]:
        """Parse LLM response for design patterns"""
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                return []
            
            json_str = response[json_start:json_end]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing pattern JSON: {e}")
            return []
    
    def _parse_refactoring_response(self, response: str) -> List[Dict]:
        """Parse LLM response for refactoring suggestions"""
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                return []
            
            json_str = response[json_start:json_end]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing refactoring JSON: {e}")
            return []
    
    def _parse_architecture_response(self, response: str) -> Dict:
        """Parse LLM response for architecture insights"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return {}
            
            json_str = response[json_start:json_end]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing architecture JSON: {e}")
            return {}
