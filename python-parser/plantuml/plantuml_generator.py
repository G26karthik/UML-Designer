"""
PlantUML Generator
Main class for generating PlantUML diagrams from code analysis results
"""

import logging
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .class_diagram_builder import ClassDiagramBuilder

logger = logging.getLogger(__name__)


class PlantUMLGenerator:
    """Main PlantUML generator class."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.theme = self.config.get('theme', 'plain')
        self.class_builder = ClassDiagramBuilder(config)
        logger.info("PlantUMLGenerator initialized with theme: %s", self.theme)

    @staticmethod
    def _collect_classes(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        classes: Dict[str, Dict[str, Any]] = {}
        language_keys = ['python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c']
        for lang in language_keys:
            entries = schema.get(lang)
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict) and entry.get('class'):
                        classes.setdefault(entry['class'], entry)

        generic_entries = schema.get('classes')
        if isinstance(generic_entries, list):
            for entry in generic_entries:
                if isinstance(entry, dict) and entry.get('class'):
                    classes.setdefault(entry['class'], entry)

        return list(classes.values())

    @staticmethod
    def _top_classes_by_relations(relations: Iterable[Dict[str, Any]], limit: int = 6) -> List[str]:
        counts: Counter[str] = Counter()
        for relation in relations or []:
            if not isinstance(relation, dict):
                continue
            frm = relation.get('from')
            to = relation.get('to')
            if frm:
                counts[str(frm)] += 1
            if to:
                counts[str(to)] += 1
        return [name for name, _ in counts.most_common(limit)]

    @staticmethod
    def _split_identifier(identifier: Optional[str]) -> str:
        if not identifier:
            return "Item"
        text = re.sub(r'[_\-]+', ' ', str(identifier))
        text = re.sub(r'(?<!^)(?=[A-Z])', ' ', text)
        return text.strip().title() or "Item"

    def _derive_use_cases(self, schema: Dict[str, Any], limit: int = 6) -> List[Dict[str, str]]:
        derived: List[Dict[str, str]] = []
        classes = self._collect_classes(schema)
        relations = schema.get('relations') or []
        top_names: List[str] = self._top_classes_by_relations(relations, limit=limit * 2) if relations else []

        selected: List[Dict[str, Any]] = []
        if top_names:
            seen = set()
            for name in top_names:
                for cls in classes:
                    if cls.get('class') == name and name not in seen:
                        selected.append(cls)
                        seen.add(name)
                        break
        if not selected:
            selected = classes[:limit]

        for cls in selected:
            class_name = cls.get('class')
            if not class_name:
                continue
            methods = cls.get('methods') or []
            label: str
            if methods:
                primary = str(methods[0])
                primary = primary.split('(')[0]
                label = f"{self._split_identifier(class_name)}: {self._split_identifier(primary)}"
            else:
                label = f"Use {self._split_identifier(class_name)}"
            derived.append({
                'label': label,
                'system': cls.get('package') or cls.get('namespace') or 'System'
            })

        if not derived and isinstance(schema.get('endpoints'), list):
            for endpoint in schema.get('endpoints')[:limit]:
                method = endpoint.get('method', 'GET')
                path = endpoint.get('path', '/')
                label = f"{method.upper()} {path}".strip()
                derived.append({
                    'label': label,
                    'system': endpoint.get('controller') or endpoint.get('class') or 'API'
                })

        if not derived:
            derived.append({'label': 'Interact With System', 'system': 'System'})

        return derived[:limit]

    def _enforce_line_limit(self, plantuml: str, max_lines: int = 2000, max_bytes: int = 8000) -> str:
        """
        Truncate PlantUML output to max_lines and max_bytes, adding a warning note if truncated.
        """
        lines = plantuml.splitlines()
        truncated = False
        # Step 1: Truncate by line count
        if len(lines) > max_lines:
            truncated = True
            try:
                enduml_idx = next(i for i, l in enumerate(lines) if l.strip().lower() == '@enduml')
            except StopIteration:
                enduml_idx = len(lines)
            warning = ["note as WARNING", "Diagram truncated to 2000 lines for compatibility.", "end note"]
            keep = max_lines - len(warning) - 1
            if keep < 0:
                keep = 0
            new_lines = lines[:keep] + warning
            if enduml_idx < len(lines):
                new_lines.append(lines[enduml_idx])
            else:
                new_lines.append("@enduml")
            lines = new_lines
        # Step 2: Truncate by byte size
        # Always ensure @enduml is present at the end
        if not lines or lines[-1].strip().lower() != '@enduml':
            lines.append("@enduml")
        # Try to fit within max_bytes
        encoded = lambda lns: "\n".join(lns).encode("utf-8")
        while len(encoded(lines)) > max_bytes and len(lines) > 5:
            # Remove lines before the warning note (but keep @startuml and theme)
            # Find warning note or @enduml
            try:
                note_idx = next(i for i, l in enumerate(lines) if l.strip().startswith("note as WARNING"))
            except StopIteration:
                note_idx = len(lines) - 2  # before @enduml
            # Always keep first 2 lines (@startuml, theme), warning, and @enduml
            keep_head = 2
            keep_tail = len(lines) - note_idx
            # Remove one line from before the warning note
            if note_idx > keep_head:
                lines = lines[:note_idx-1] + lines[note_idx:]
                truncated = True
            else:
                # If can't remove more, break
                break
        if truncated or len(encoded(lines)) > max_bytes:
            # If still too big, replace with a minimal error diagram
            if len(encoded(lines)) > max_bytes:
                return "\n".join([
                    "@startuml",
                    f"!theme {self.theme}",
                    "note as WARNING",
                    f"Diagram too large to render (exceeds {max_bytes} bytes after truncation).",
                    "end note",
                    "@enduml"
                ])
            return "\n".join(lines)
        return plantuml

    @staticmethod
    def _relation_message(relation: Dict[str, Any]) -> str:
        relation_type = (relation.get('type') or 'interacts').replace('_', ' ').title()
        return relation_type

    @staticmethod
    def _stateful_classes(classes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        stateful: List[Dict[str, Any]] = []
        for cls in classes:
            fields = cls.get('fields') or []
            if any(re.search(r'state|status|phase|mode', str(field), re.IGNORECASE) for field in fields):
                stateful.append(cls)
        return stateful
    
    def generate(
        self, 
        schema: Dict[str, Any], 
        diagram_type: str = 'class',
        language_filter: Optional[List[str]] = None
    ) -> str:
        """
        Generate PlantUML diagram from schema.
        
        Args:
            schema: Analysis schema from analyze_repo()
            diagram_type: Type of diagram to generate
                - 'class': Class diagram (default)
                - 'sequence': Sequence diagram
                - 'usecase': Use case diagram
                - 'state': State machine diagram
                - 'activity': Activity diagram
            language_filter: Optional list of languages to include
        
        Returns:
            PlantUML syntax string
        
        Raises:
            ValueError: If schema is invalid or diagram_type unsupported
        """
        if schema is None or not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")
        
        diagram_type = diagram_type.lower()
        
        try:
            if diagram_type == 'class':
                return self._enforce_line_limit(self.build_class_diagram(schema, language_filter))
            elif diagram_type == 'sequence':
                return self.build_sequence_diagram(schema)
            elif diagram_type in ['usecase', 'use-case']:
                return self.build_use_case_diagram(schema)
            elif diagram_type == 'state':
                return self.build_state_diagram(schema)
            elif diagram_type == 'activity':
                return self.build_activity_diagram(schema)
            elif diagram_type == 'communication':
                return self.build_communication_diagram(schema)
            elif diagram_type == 'component':
                return self.build_component_diagram(schema)
            elif diagram_type == 'deployment':
                return self.build_deployment_diagram(schema)
            else:
                raise ValueError(f"Unsupported diagram type: {diagram_type}")
        
        except Exception as e:
            logger.error(f"Failed to generate {diagram_type} diagram: {e}")
            raise
    
    def build_class_diagram(
        self, 
        schema: Dict[str, Any],
        language_filter: Optional[List[str]] = None
    ) -> str:
        """
        Build PlantUML class diagram.
        
        Args:
            schema: Analysis schema
            language_filter: Optional list of languages to include
        
        Returns:
            PlantUML class diagram syntax
        """
        logger.info("Building PlantUML class diagram")
        return self.class_builder.build(schema, language_filter)
    
    def build_sequence_diagram(self, schema: Dict[str, Any]) -> str:
        """
        Build PlantUML sequence diagram.
        
        Args:
            schema: Analysis schema
        
        Returns:
            PlantUML sequence diagram syntax
        """
        logger.info("Building PlantUML sequence diagram")
        
        def _sanitize(name: str, prefix: str = "P") -> str:
            base = ''.join(ch if ch.isalnum() else '_' for ch in (name or 'Participant'))
            base = base or prefix
            return f"{prefix}_{base}"

        lines = [
            "@startuml",
            f"!theme {self.theme}",
            "' Sequence Diagram",
            ""
        ]
        
        flows = []
        for key in ('sequence_flows', 'sequenceFlows'):
            value = schema.get(key)
            if isinstance(value, list):
                flows.extend(value)
        flows = [flow for flow in flows if isinstance(flow, dict)]

        # Get endpoints for sequence interactions
        endpoints = schema.get('endpoints', [])

        if flows:
            participants: Dict[str, str] = {}

            def ensure_participant(label: str) -> str:
                name = label or 'Participant'
                if name not in participants:
                    prefix = 'ACT' if name.lower() in ('user', 'actor', 'client') else 'P'
                    participants[name] = _sanitize(name, prefix)
                return participants[name]

            # Register participants first for consistent ordering
            for flow in flows[:25]:
                ensure_participant(flow.get('from') or flow.get('initiator') or flow.get('actor') or 'User')
                ensure_participant(flow.get('to') or flow.get('receiver') or flow.get('component') or 'System')

            emitted_names: Set[str] = set()
            for label, identifier in participants.items():
                if label.lower() in ('user', 'actor', 'client'):
                    lines.append(f"actor {identifier} as \"{label}\"")
                else:
                    lines.append(f"participant {identifier} as \"{label}\"")
                emitted_names.add(label)

            lines.append("")

            for flow in flows[:25]:
                from_label = flow.get('from') or flow.get('initiator') or flow.get('actor') or 'User'
                to_label = flow.get('to') or flow.get('receiver') or flow.get('component') or 'System'
                message = flow.get('message') or flow.get('action') or 'interact'
                response = flow.get('response')
                note = flow.get('note')
                call_type = (flow.get('type') or 'sync').lower()

                from_id = ensure_participant(from_label)
                to_id = ensure_participant(to_label)
                arrow = '->>' if call_type in ('sync', 'synchronous') else '-)'

                if from_label not in emitted_names:
                    lines.append(f"participant {from_id} as \"{from_label}\"")
                    emitted_names.add(from_label)
                if to_label not in emitted_names:
                    lines.append(f"participant {to_id} as \"{to_label}\"")
                    emitted_names.add(to_label)

                lines.append(f"{from_id}{arrow}{to_id}: {message}")
                if note:
                    lines.append(f"note over {from_id},{to_id}: {note}")
                if response:
                    lines.append(f"{to_id}-->>{from_id}: {response}")
                lines.append("")

        elif endpoints:
            # Add actors and participants
            lines.append("actor User")
            lines.append("")
            
            # Extract unique controllers/classes
            participants = set()
            for endpoint in endpoints:
                class_name = endpoint.get('class', endpoint.get('controller', 'Controller'))
                participants.add(class_name)
            
            for participant in sorted(participants):
                lines.append(f"participant {participant}")
            
            lines.append("")
            
            # Add interactions
            for endpoint in endpoints[:20]:  # Limit to first 20 to avoid clutter
                method = endpoint.get('method', 'GET')
                path = endpoint.get('path', '/')
                class_name = endpoint.get('class', endpoint.get('controller', 'Controller'))
                
                lines.append(f"User -> {class_name}: {method} {path}")
                lines.append(f"activate {class_name}")
                lines.append(f"{class_name} --> User: Response")
                lines.append(f"deactivate {class_name}")
                lines.append("")
        else:
            lines.append("actor User")
            lines.append("participant System")
            lines.append("User -> System: Request")
            lines.append("System --> User: Response")
            lines.append("")
        lines.append("@enduml")
        plantuml = "\n".join(lines)
        return self._enforce_line_limit(plantuml)

    
    def build_use_case_diagram(self, schema: Dict[str, Any]) -> str:
        """
        Build PlantUML use case diagram.
        
        Args:
            schema: Analysis schema
        
        Returns:
            PlantUML use case diagram syntax
        """
        logger.info("Building PlantUML use case diagram")
        
        lines = [
            "@startuml",
            f"!theme {self.theme}",
            "left to right direction",
            "' Use Case Diagram",
            ""
        ]
        
        usecases = schema.get('usecases', []) or []
        endpoints = schema.get('endpoints', []) or []

        if usecases:
            actors: Dict[str, str] = {}
            usecase_nodes: Dict[str, str] = {}

            def sanitize(name: str, prefix: str = 'UC') -> str:
                base = ''.join(ch if ch.isalnum() else '_' for ch in (name or 'UseCase')) or prefix
                return f"{prefix}_{base}"

            for usecase in usecases[:30]:
                primary_actor = usecase.get('actor') or 'User'
                actors.setdefault(primary_actor, sanitize(primary_actor, 'ACT'))
                for supporting in usecase.get('supportingActors', []) or []:
                    actors.setdefault(supporting, sanitize(supporting, 'ACT'))

                label = usecase.get('name') or usecase.get('action') or usecase.get('goal') or 'Use Case'
                usecase_nodes.setdefault(label, sanitize(label))

            for actor_name, identifier in actors.items():
                lines.append(f"actor {identifier} as \"{actor_name}\"")

            lines.append("")
            system_name = schema.get('meta', {}).get('system') or 'System'
            lines.append(f"rectangle \"{system_name}\" {{")

            for label, identifier in usecase_nodes.items():
                lines.append(f"  usecase {identifier} as \"{label}\"")

            lines.append("}")

            for usecase in usecases[:30]:
                label = usecase.get('name') or usecase.get('action') or usecase.get('goal') or 'Use Case'
                identifier = usecase_nodes[label]
                primary_actor = usecase.get('actor') or 'User'
                if primary_actor in actors:
                    lines.append(f"{actors[primary_actor]} --> {identifier}")
                for supporting in usecase.get('supportingActors', []) or []:
                    if supporting in actors:
                        lines.append(f"{actors[supporting]} --> {identifier}")

                for include in usecase.get('includes', []) or []:
                    if include not in usecase_nodes:
                        usecase_nodes[include] = sanitize(include)
                        lines.insert(-1, f"  usecase {usecase_nodes[include]} as \"{include}\"")
                    lines.append(f"{identifier} ..> {usecase_nodes[include]} : <<include>>")

                for extends in usecase.get('extends', []) or []:
                    if extends not in usecase_nodes:
                        usecase_nodes[extends] = sanitize(extends)
                        lines.insert(-1, f"  usecase {usecase_nodes[extends]} as \"{extends}\"")
                    lines.append(f"{identifier} ..> {usecase_nodes[extends]} : <<extends>>")

        elif endpoints:
            lines.append("actor User")
            lines.append("")
            unique_actions = []
            seen = set()
            for endpoint in endpoints[:20]:
                method = endpoint.get('method', 'GET')
                path = endpoint.get('path', '/')
                action = f"{method} {path}".strip()
                if action not in seen:
                    seen.add(action)
                    unique_actions.append(action)
            for action in unique_actions:
                lines.append(f"({action})")
                lines.append(f"User --> ({action})")
        else:
            derived_usecases = self._derive_use_cases(schema, limit=8)
            if derived_usecases:
                lines.append("actor User")
                lines.append("")
                system_name = schema.get('meta', {}).get('system') or 'System'
                lines.append(f"rectangle \"{system_name}\" {{")
                for idx, uc in enumerate(derived_usecases):
                    identifier = f"UC_{idx}"
                    lines.append(f"  usecase {identifier} as \"{uc['label']}\"")
                    lines.append(f"  User --> {identifier}")
                lines.append("}")
            else:
                lines.append("actor User")
                lines.append("(Use System)")
                lines.append("User --> (Use System)")
        
        lines.append("@enduml")
        return "\n".join(lines)
    
    def build_state_diagram(self, schema: Dict[str, Any]) -> str:
        """
        Build PlantUML state machine diagram.
        
        Args:
            schema: Analysis schema
        
        Returns:
            PlantUML state diagram syntax
        """
        logger.info("Building PlantUML state diagram")
        
        lines = [
            "@startuml",
            f"!theme {self.theme}",
            "' State Machine Diagram",
            "",
            "[*] --> Initial"
        ]
        
        states_data = schema.get('states', [])
        if isinstance(states_data, list) and states_data:
            for state_block in states_data[:10]:
                if not isinstance(state_block, dict):
                    continue
                context = state_block.get('context') or state_block.get('class') or 'Component'
                context_id = ''.join(ch if ch.isalnum() else '_' for ch in context) or 'Stateful'
                lines.append(f"state \"{context}\" as {context_id} {{")

                states = state_block.get('states') or state_block.get('state_fields') or []
                if isinstance(states, list) and states:
                    first_state = states[0] if isinstance(states[0], str) else states[0].get('name', 'State')
                    lines.append(f"  [*] --> {''.join(ch if ch.isalnum() else '_' for ch in str(first_state))}")
                    for state in states:
                        if isinstance(state, str):
                            state_name = state
                            label = state
                        else:
                            state_name = state.get('name', 'State')
                            label = state.get('label', state_name)
                        identifier = ''.join(ch if ch.isalnum() else '_' for ch in str(state_name)) or 'State'
                        lines.append(f"  state {identifier} : {label}")

                transitions = state_block.get('transitions') or []
                if isinstance(transitions, list):
                    for transition in transitions:
                        if not isinstance(transition, dict):
                            continue
                        from_state = transition.get('from', 'State')
                        to_state = transition.get('to', 'State')
                        trigger = transition.get('trigger') or transition.get('event')
                        from_id = ''.join(ch if ch.isalnum() else '_' for ch in str(from_state))
                        to_id = ''.join(ch if ch.isalnum() else '_' for ch in str(to_state))
                        if trigger:
                            lines.append(f"  {from_id} --> {to_id} : {trigger}")
                        else:
                            lines.append(f"  {from_id} --> {to_id}")

                lines.append("}")
        else:
            classes = self._collect_classes(schema)
            stateful = self._stateful_classes(classes)
            if stateful:
                for cls in stateful[:4]:
                    class_name = cls.get('class', 'Component')
                    identifier = ''.join(ch if ch.isalnum() else '_' for ch in class_name) or 'Component'
                    lines.append(f"state \"{class_name}\" as {identifier} {{")
                    lines.append("  [*] --> Initialized")
                    lines.append("  Initialized --> Active : setState()")
                    lines.append("  Active --> Suspended : pause()")
                    lines.append("  Suspended --> Active : resume()")
                    lines.append("  Active --> Completed : complete()")
                    lines.append("  Completed --> [*]")
                    lines.append("}")
            elif classes:
                for cls in classes[:4]:
                    class_name = cls.get('class', 'Component')
                    identifier = ''.join(ch if ch.isalnum() else '_' for ch in class_name) or 'Component'
                    lines.append(f"state \"{class_name}\" as {identifier} {{")
                    lines.append("  [*] --> Created")
                    lines.append("  Created --> Active : initialize()")
                    lines.append("  Active --> Completed : finalize()")
                    lines.append("  Completed --> Archived : archive()")
                    lines.append("  Archived --> [*]")
                    lines.append("}")
            else:
                lines.append("Initial --> Processing")
                lines.append("Processing --> Complete")
                lines.append("Complete --> [*]")
        
        lines.append("@enduml")
        return "\n".join(lines)
    
    def build_activity_diagram(self, schema: Dict[str, Any]) -> str:
        """
        Build PlantUML activity diagram.
        
        Args:
            schema: Analysis schema
        
        Returns:
            PlantUML activity diagram syntax
        """
        logger.info("Building PlantUML activity diagram")
        
        lines = [
            "@startuml",
            f"!theme {self.theme}",
            "' Activity Diagram",
            "",
            "start"
        ]
        
        activity_items: List[Dict[str, Any]] = []
        if isinstance(schema.get('activity'), list):
            activity_items.extend([item for item in schema.get('activity') if isinstance(item, dict)])
        if isinstance(schema.get('activity_flows'), list):
            activity_items.extend([item for item in schema.get('activity_flows') if isinstance(item, dict)])

        if activity_items:
            seen_steps = set()
            for activity in activity_items[:30]:
                step = activity.get('step') or activity.get('name') or 'Activity'
                role = activity.get('role')
                class_name = activity.get('class')
                label = step
                if role:
                    label += f"\\n({role})"
                if class_name:
                    label += f"\\nin {class_name}"
                if step not in seen_steps:
                    lines.append(f":{label};")
                    seen_steps.add(step)

                next_steps = activity.get('next')
                if isinstance(next_steps, list):
                    for nxt in next_steps[:5]:
                        guard = activity.get('condition') or activity.get('trigger')
                        edge_suffix = f" : {guard}" if guard else ""
                        lines.append(f":{step}; --> :{nxt};{edge_suffix}")
        else:
            all_methods = []
            for lang in ['python', 'java', 'csharp', 'javascript', 'typescript']:
                classes = schema.get(lang, [])
                for cls in classes[:3]:
                    methods = cls.get('methods', [])
                    all_methods.extend(methods[:3])
            for method in all_methods[:10]:
                method_name = method.split('(')[0].strip()
                lines.append(f":{method_name};")
        
        lines.append("stop")
        lines.append("@enduml")
        return "\n".join(lines)
    
    def build_communication_diagram(self, schema: Dict[str, Any]) -> str:
        """
        Build PlantUML communication diagram.
        
        Args:
            schema: Analysis schema
        
        Returns:
            PlantUML communication diagram syntax
        """
        logger.info("Building PlantUML communication diagram")
        
        lines = [
            "@startuml",
            f"!theme {self.theme}",
            "' Communication Diagram",
            ""
        ]
        
        relations = schema.get('relations', []) or []
        classes = self._collect_classes(schema)
        
        if relations:
            # Create participants from classes involved in relations
            participants = set()
            for relation in relations:
                if relation.get('from'):
                    participants.add(relation.get('from'))
                if relation.get('to'):
                    participants.add(relation.get('to'))
            
            # Limit to top participants by relationship count
            top_participants = list(participants)[:8]
            
            # Declare participants
            for participant in top_participants:
                lines.append(f"participant {participant}")
            
            lines.append("")
            
            # Add communication messages
            message_count = 1
            for relation in relations[:15]:
                frm = relation.get('from')
                to = relation.get('to')
                if frm in top_participants and to in top_participants:
                    message = self._relation_message(relation)
                    lines.append(f"{frm} -> {to} : {message_count}. {message}")
                    message_count += 1
                    
                    # Add some return messages
                    if message_count % 3 == 0:
                        lines.append(f"{to} --> {frm} : {message_count - 1}. response")
        
        elif classes:
            # Fallback: create communication based on class relationships
            top_classes = [cls.get('class') for cls in classes[:6]]
            
            for participant in top_classes:
                lines.append(f"participant {participant}")
            
            lines.append("")
            
            # Add some default communication
            for i in range(min(len(top_classes) - 1, 5)):
                lines.append(f"{top_classes[i]} -> {top_classes[i+1]} : {i+1}. interacts")
                if (i + 1) % 2 == 0:
                    lines.append(f"{top_classes[i+1]} --> {top_classes[i]} : {i+1}. response")
        
        else:
            # Generic fallback (distinct from class diagram)
            lines.append("participant Client")
            lines.append("participant API")
            lines.append("participant Database")
            lines.append("")
            lines.append("Client -> API : 1. call endpoint")
            lines.append("API -> Database : 2. query")
            lines.append("Database --> API : 3. result")
            lines.append("API --> Client : 4. response")
        
        lines.append("@enduml")
        return "\n".join(lines)
    
    def build_component_diagram(self, schema: Dict[str, Any]) -> str:
        """
        Build PlantUML component diagram.
        
        Args:
            schema: Analysis schema
        
        Returns:
            PlantUML component diagram syntax
        """
        logger.info("Building PlantUML component diagram")
        
        lines = [
            "@startuml",
            f"!theme {self.theme}",
            "' Component Diagram",
            ""
        ]
        
        classes = self._collect_classes(schema)
        relations = schema.get('relations', []) or []
        endpoints = schema.get('endpoints', []) or []
        
        if classes:
            # Group classes by package/namespace
            packages = {}
            for cls in classes:
                package_name = cls.get('package') or cls.get('namespace') or 'Default'
                if package_name not in packages:
                    packages[package_name] = []
                packages[package_name].append(cls)
            
            # Create components for packages
            for package_name, package_classes in packages.items():
                if len(package_classes) > 1:
                    lines.append(f"package \"{package_name}\" {{")
                    for cls in package_classes[:5]:  # Limit classes per package
                        component_name = cls.get('class', 'Component')
                        lines.append(f"  component {component_name}")
                    lines.append("}")
                else:
                    for cls in package_classes:
                        component_name = cls.get('class', 'Component')
                        lines.append(f"component {component_name}")
            
            lines.append("")
            
            # Add relationships between components
            for relation in relations[:10]:
                frm = relation.get('from')
                to = relation.get('to')
                if frm and to:
                    relation_type = relation.get('type', 'uses')
                    lines.append(f"{frm} --> {to} : {relation_type}")
        
        elif endpoints:
            # Create components based on endpoints
            controllers = set()
            for endpoint in endpoints:
                controller = endpoint.get('controller') or endpoint.get('class') or 'API'
                controllers.add(controller)
            
            for controller in controllers:
                lines.append(f"component {controller}")
            
            lines.append("")
            lines.append("component Database")
            lines.append("")
            
            # Connect controllers to database
            for controller in list(controllers)[:3]:
                lines.append(f"{controller} --> Database : queries")
        
        else:
            # Generic fallback (distinct from class diagram)
            lines.append("component Frontend")
            lines.append("component API")
            lines.append("component AuthService")
            lines.append("component Database")
            lines.append("")
            lines.append("Frontend --> API : HTTP")
            lines.append("API --> AuthService : Auth")
            lines.append("API --> Database : queries")
        
        lines.append("@enduml")
        return "\n".join(lines)
    
    def build_deployment_diagram(self, schema: Dict[str, Any]) -> str:
        """
        Build PlantUML deployment diagram.
        
        Args:
            schema: Analysis schema
        
        Returns:
            PlantUML deployment diagram syntax
        """
        logger.info("Building PlantUML deployment diagram")
        
        lines = [
            "@startuml",
            f"!theme {self.theme}",
            "' Deployment Diagram",
            ""
        ]
        
        classes = self._collect_classes(schema)
        endpoints = schema.get('endpoints', []) or []
        
        if endpoints:
            # Create nodes based on endpoints
            lines.append("node \"Web Server\" {")
            lines.append("  component API")
            lines.append("}")
            lines.append("")
            lines.append("node \"Database Server\" {")
            lines.append("  database Database")
            lines.append("}")
            lines.append("")
            lines.append("API --> Database : queries")
        
        elif classes:
            # Create deployment based on classes
            lines.append("node \"Application Server\" {")
            for cls in classes[:3]:
                component_name = cls.get('class', 'Component')
                lines.append(f"  component {component_name}")
            lines.append("}")
            lines.append("")
            lines.append("node \"Database Server\" {")
            lines.append("  database Database")
            lines.append("}")
            lines.append("")
            
            # Connect components
            for i, cls in enumerate(classes[:3]):
                component_name = cls.get('class', 'Component')
                lines.append(f"{component_name} --> Database : data access")
        
        else:
            # Generic fallback (distinct from class diagram)
            lines.append("node \"Client Machine\" {")
            lines.append("  artifact App")
            lines.append("}")
            lines.append("")
            lines.append("node \"Web Server\" {")
            lines.append("  component Frontend")
            lines.append("}")
            lines.append("")
            lines.append("node \"API Server\" {")
            lines.append("  component API")
            lines.append("  component AuthService")
            lines.append("}")
            lines.append("")
            lines.append("node \"Database Server\" {")
            lines.append("  database Database")
            lines.append("}")
            lines.append("")
            lines.append("App --> Frontend : HTTP")
            lines.append("Frontend --> API : REST")
            lines.append("API --> AuthService : Auth")
            lines.append("API --> Database : queries")
        
        lines.append("@enduml")
        return "\n".join(lines)
    
    def validate_schema(self, schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate schema structure.
        
        Args:
            schema: Schema to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not schema:
            return False, "Schema is empty"
        
        if not isinstance(schema, dict):
            return False, "Schema must be a dictionary"
        
        # Check for at least one supported language or data
        languages = ['python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c']
        has_classes = any(
            isinstance(schema.get(lang), list) and len(schema.get(lang, [])) > 0
            for lang in languages
        )
        
        has_relations = isinstance(schema.get('relations'), list) and len(schema.get('relations', [])) > 0
        has_endpoints = isinstance(schema.get('endpoints'), list) and len(schema.get('endpoints', [])) > 0
        
        if not (has_classes or has_relations or has_endpoints):
            return False, "Schema must contain at least classes, relations, or endpoints"
        
        return True, None
    
    def get_diagram_types(self) -> List[str]:
        """
        Get list of supported diagram types.
        
        Returns:
            List of diagram type names
        """
        return ['class', 'sequence', 'usecase', 'state', 'activity', 'component', 'communication', 'deployment']
    
    def get_statistics(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get statistics about the schema.
        
        Args:
            schema: Schema to analyze
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_classes': 0,
            'total_relations': len(schema.get('relations', [])),
            'total_endpoints': len(schema.get('endpoints', [])),
            'languages': []
        }
        
        for lang in ['python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c']:
            classes = schema.get(lang, [])
            if classes:
                stats['total_classes'] += len(classes)
                stats['languages'].append(lang)
        
        return stats
