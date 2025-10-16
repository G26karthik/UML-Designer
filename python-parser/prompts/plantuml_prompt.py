
"""Utilities for constructing flexible PlantUML-focused LLM prompts."""


from __future__ import annotations

import json
from textwrap import dedent
from typing import Any, Dict, Optional, Sequence

SUPPORTED_FORMATS = {"plantuml"}

_DIAGRAM_GUIDANCE = {
    "class": (
        "Model the core domain types, their attributes, and key operations.",
        "Use inheritance (extends), interfaces (implements), composition (--*), and aggregation (--o) to express relationships accurately.",
        "Highlight important stereotypes such as controllers, services, repositories, entities, or external systems using <<stereotype>> annotations.",
        "Group related classes into packages when it clarifies the architecture.",
        "Expose key properties and methods but keep noise (getters/setters) to a minimum."
    ),
    "sequence": (
        "Illustrate the runtime collaboration for the primary happy-path scenario.",
        "Show each participant (actors, boundary systems, services, databases) only once with concise labels.",
        "Use synchronous arrows (->) for blocking calls and asynchronous arrows (->>) for fire-and-forget interactions.",
        "Include return arrows (<-- or <<--) when responses are meaningful, plus alt/opt fragments for decisions.",
        "Annotate noteworthy steps with note over ... blocks to capture business rules or side-effects."
    ),
    "usecase": (
        "Declare actors OUTSIDE the system boundary using: actor ActorName",
        "Group use cases INSIDE a rectangle: rectangle SystemName { usecase UC1 }",
        "Create one use case per core goal using simple syntax: usecase \"Action Name\" as UC1",
        "Connect actors to use cases with simple arrows: ActorName --> UC1",
        "Model <<include>> and <<extend>> relationships when needed: UC1 .> UC2 : <<include>>",
        "CRITICAL: Do NOT use composition (*--) or aggregation (--o) syntax in use case diagrams - those are for class diagrams only"
    ),
    "state": (
        "Choose a single entity or aggregate with an interesting lifecycle and model its states.",
        "Start with [*] entry state and ensure there is a terminal [*] transition when the lifecycle completes.",
        "CRITICAL: Use correct PlantUML state syntax: state \"Display Name\" as StateId",
        "Label transitions with: StateId1 --> StateId2 : trigger/action",
        "Use state blocks for nested states: state StateId { [*] --> SubState1 }",
        "NEVER use invalid syntax like: State[label=\"Label\"] or State as State[label=\"Label\"]"
    ),
    "activity": (
        "Represent the primary workflow as a sequence of actions between start and stop nodes.",
        "Use :Action Description; syntax for each activity step (end with semicolon)",
        "Use decision diamonds: if (condition?) then (yes) ... else (no) ... endif",
        "Use swim lanes with |PartitionName| syntax when responsibilities span teams",
        "Start with 'start' keyword and end with 'stop' keyword",
        "Keep each activity label short yet outcome-focused (verb + object)"
    ),
    "communication": (
        "Use @startuml and @enduml to wrap the diagram.",
        "Declare each participant with: participant Name",
        "Show messages as arrows: A -> B : message",
        "Use 'alt', 'opt', 'loop' blocks for conditional or repeated communication.",
        "Keep the diagram focused on message flow, not internal logic.",
    ),
    "component": (
        "Use @startuml and @enduml to wrap the diagram.",
        "Declare components with [ComponentName] or component ComponentName.",
        "Show interfaces with () or interface InterfaceName.",
        "Connect components with arrows: [A] --> [B]",
        "Group related components with package blocks.",
        "Label connections with interface names or protocols if relevant.",
    ),
    "deployment": (
        "Use @startuml and @enduml to wrap the diagram.",
        "Declare nodes with node NodeName or cloud CloudName.",
        "Show artifacts with artifact ArtifactName or database DatabaseName.",
        "Connect nodes and artifacts with arrows: node1 --> node2",
        "Group artifacts within nodes using curly braces.",
        "Label connections with protocols or network types if relevant.",
    ),
}

# Forbidden lists for PlantUML diagram types
_PLANTUML_FORBIDDEN = {
    "communication": (
    "",
        "Use ONLY PlantUML communication diagram syntax: participant, ->, alt, opt, loop, etc.",
        "Do not use classDiagram, component, or deployment keywords.",
    ),
    "component": (
    "",
        "Use ONLY PlantUML component diagram syntax: [Component], component, interface, etc.",
        "Do not use classDiagram, sequenceDiagram, or deployment keywords.",
    ),
    "deployment": (
    "",
        "Use ONLY PlantUML deployment diagram syntax: node, artifact, database, cloud, etc.",
        "Do not use classDiagram, sequenceDiagram, or component keywords.",
    ),
}

# Supported diagram types for PlantUML
PLANTUML_DIAGRAM_TYPES = {
    "class",
    "sequence",
    "usecase",
    "activity",
    "state",
    "communication",
    "component",
    "deployment",
}

_PLANTUML_FORBIDDEN: Dict[str, Sequence[str]] = {
    "communication": (
    "",
        "Use ONLY PlantUML communication diagram syntax: participant, ->, alt, opt, loop, etc.",
        "Do not use classDiagram, component, or deployment keywords.",
    ),
    "component": (
    "",
        "Use ONLY PlantUML component diagram syntax: [Component], component, interface, etc.",
        "Do not use classDiagram, sequenceDiagram, or deployment keywords.",
    ),
    "deployment": (
    "",
        "Use ONLY PlantUML deployment diagram syntax: node, artifact, database, cloud, etc.",
        "Do not use classDiagram, sequenceDiagram, or component keywords.",
    ),
}


def _format_context(context: Optional[Dict[str, Any]]) -> str:
    if not context:
        return "None"

    formatted_sections = []

    for key, value in context.items():
        if value is None:
            continue
        normalized_key = key.replace("_", " ").title()
        if isinstance(value, str):
            formatted_sections.append(f"- {normalized_key}: {value.strip()}")
        elif isinstance(value, (list, tuple, set)):
            items = [str(item).strip() for item in value if str(item).strip()]
            if not items:
                continue
            formatted_sections.append(f"- {normalized_key}:" + "\n    - " + "\n    - ".join(items))
        else:
            try:
                serialized = json.dumps(value, indent=2, ensure_ascii=False)
            except TypeError:
                serialized = str(value)
            formatted_sections.append(f"- {normalized_key}:\n{serialized}")

    return "\n".join(formatted_sections) if formatted_sections else "None"


def build_plantuml_prompt(
    user_prompt: str,
    *,
    diagram_type: str = "class",
    output_format: str = "plantuml",
    context: Optional[Dict[str, Any]] = None,
    schema: Optional[Dict[str, Any]] = None,
    style_preferences: Optional[Dict[str, Any]] = None,
    focus: Optional[Sequence[str]] = None,
) -> str:
    """Construct a rich prompt for an LLM to emit diagram code.

    Args:
        user_prompt: Raw natural-language instructions from the user.
        diagram_type: Desired UML diagram variant (class, sequence, usecase, state, activity).
    output_format: Target syntax. Supports "plantuml" (default).
        context: Optional supplemental context (e.g., existing schema, architecture notes).
        style_preferences: Optional hints for visual style or layout.
        focus: Optional list of emphasis areas (e.g., ["security", "scalability"]).

    Returns:
        A single formatted prompt string ready to send to the LLM.
    """
    if not isinstance(user_prompt, str) or not user_prompt.strip():
        raise ValueError("user_prompt must be a non-empty string")

    diagram_key = diagram_type.lower().strip()
    if diagram_key not in _DIAGRAM_GUIDANCE:
        valid = ", ".join(sorted(_DIAGRAM_GUIDANCE))
        raise ValueError(f"Unsupported diagram_type '{diagram_type}'. Valid options: {valid}")

    fmt = output_format.lower().strip()
    if fmt not in SUPPORTED_FORMATS:
        valid_formats = ", ".join(sorted(SUPPORTED_FORMATS))
        raise ValueError(f"Unsupported output_format '{output_format}'. Valid options: {valid_formats}")

    guidance_lines = "\n".join(f"- {line.strip()}" for line in _DIAGRAM_GUIDANCE[diagram_key])

    # Add strict, type-specific rules and minimal valid examples
    strict_examples = {
        "class": """\nSTRICT RULES:\n- Only use PlantUML class diagram syntax.\n- Do not use state, activity, deployment, or component diagram syntax.\n- Minimal valid example:\n@startuml\nclass User {\n  +id: int\n  +name: string\n}\n@enduml\n""",
        "state": """\nSTRICT RULES:\n- Only use PlantUML state diagram syntax.\n- Do not use @startuml as a state name.\n- Always start with [*] and have at least one valid state and transition.\n- Minimal valid example:\n@startuml\n[*] --> Idle\nIdle --> Processing : start\nProcessing --> [*] : finish\n@enduml\n""",
        "activity": """\nSTRICT RULES:\n- Only use PlantUML activity diagram syntax.\n- Do not use class, state, deployment, or component diagram syntax.\n- Always start with 'start' and end with 'stop'.\n- Minimal valid example:\n@startuml\nstart\n:Do something;\nstop\n@enduml\n""",
        "deployment": """\nSTRICT RULES:\n- Only use PlantUML deployment diagram syntax.\n- Do not use class, state, activity, or component diagram syntax.\n- Always declare at least one node and one relationship.\n- Minimal valid example:\n@startuml\nnode WebServer\nnode Database\nWebServer --> Database : connects\n@enduml\n""",
        "component": """\nSTRICT RULES:\n- Only use PlantUML component diagram syntax.\n- Do not use class, state, activity, or deployment diagram syntax.\n- Minimal valid example:\n@startuml\ncomponent API\ncomponent DB\nAPI --> DB : queries\n@enduml\n""",
    }
    strict_section = strict_examples.get(diagram_key, "")
    context_section = _format_context(context)

    schema_section = "None"
    if schema:
        try:
            schema_section = json.dumps(schema, indent=2, ensure_ascii=False)
        except TypeError:
            schema_section = str(schema)

    style_section = "None"
    if style_preferences:
        try:
            style_section = json.dumps(style_preferences, indent=2, ensure_ascii=False)
        except TypeError:
            style_section = str(style_preferences)

    focus_section = "None"
    if focus:
        cleaned = [item.strip() for item in focus if str(item).strip()]
        if cleaned:
            focus_section = "\n".join(f"- {item}" for item in cleaned)

    syntax_directive = (
        "Return PlantUML code starting with '@startuml' and ending with '@enduml'."
        if fmt == "plantuml"
    else "Return raw PlantUML syntax without wrapping it in markdown fences."
    )

    # Add diagram-specific examples for PlantUML
    examples_section = ""
    if fmt == "plantuml":
        examples_map = {
            "usecase": dedent("""
                EXAMPLE USE CASE SYNTAX:
                @startuml
                actor User
                rectangle System {
                    usecase "Browse Products" as UC1
                    usecase "Place Order" as UC2
                }
                User --> UC1
                User --> UC2
                @enduml
                """).strip(),
            "state": dedent("""
                EXAMPLE STATE SYNTAX:
                @startuml
                [*] --> Draft
                state "Pending Payment" as Pending
                Draft --> Pending : submit
                Pending --> [*] : complete
                @enduml
                """).strip(),
            "activity": dedent("""
                EXAMPLE ACTIVITY SYNTAX:
                @startuml
                start
                :User enters prompt;
                if (valid?) then (yes)
                  :Generate diagram;
                else (no)
                  :Show error;
                endif
                stop
                @enduml
                """).strip(),
        }
        examples_section = examples_map.get(diagram_key, "")


    # Inject stricter forbidden syntax and explicit rules for problematic types
    strict_rules = ""
    if diagram_key in ("state", "activity", "component", "deployment"):
        forbidden = _PLANTUML_FORBIDDEN.get(diagram_key, [])
        forbidden_section = "\n".join(f"- {line}" for line in forbidden)
        # Add explicit rules for simplicity and no nesting
        if diagram_key in ("state", "activity"):
            extra = """
- NEVER use nested blocks or curly braces.
- NEVER use more than 8 lines in the diagram (excluding @startuml/@enduml).
- NEVER use swimlanes (|PartitionName|) or any syntax except direct transitions/actions.
- ONLY use direct transitions (-->), actions (:) and start/stop for activity.
- NEVER use state blocks or nested states for state diagrams.
"""
        elif diagram_key in ("component", "deployment"):
            extra = """
- NEVER use nested packages, nodes, or curly braces.
- NEVER use more than 8 lines in the diagram (excluding @startuml/@enduml).
- ONLY use direct component/node/interface/artifact/database/cloud declarations and direct relationships (arrows).
- NEVER use any block or grouping syntax.
"""
        else:
            extra = ""
        strict_rules = f"\nSTRICT RULES\n------------\n{forbidden_section}\n{extra.strip()}\n"

    prompt = dedent(
        f"""
        You are an expert software architect and UML diagram author. Craft a high-impact, detailed, and plausible {diagram_key} diagram that
        captures the intent of the following request. If the user prompt is vague or incomplete, IMAGINE a realistic system and fill in plausible details using your knowledge of typical architectures and best practices. Invent classes, actions, nodes, and relationships as needed to create a meaningful and illustrative diagram. Think step-by-step, validate that the design is cohesive, and then emit only the requested diagram code with no commentary or markdown fences.

        USER GOAL
        ---------
        {user_prompt.strip()}

        OUTPUT REQUIREMENTS
        --------------------
        - Diagram type: {diagram_key}
        - Output syntax: {fmt}
        - {syntax_directive}
        - Do not include explanations, markdown, or surrounding prose.
        - Ensure identifiers are deterministic, concise, and readable.
        - Prefer industry-standard UML notation and consistent theming.
        {examples_section}

        CONTEXT (OPTIONAL)
        ------------------
        {context_section}

        SCHEMA SNAPSHOT (OPTIONAL)
        -------------------------
        {schema_section}

        STYLE PREFERENCES (OPTIONAL)
        -----------------------------
        {style_section}

        EMPHASIS AREAS (OPTIONAL)
        -------------------------
        {focus_section}

        DIAGRAM-SPECIFIC GUIDANCE
        -------------------------
        {guidance_lines}

        {strict_rules}
        {strict_section}

        QUALITY CHECKLIST
        -----------------
        - The diagram must reflect every major element from the user goal and context.
        - If the user prompt is vague, invent plausible details and structure for a realistic system.
        - Highlight external systems, user roles, or boundaries when relevant.
        - Avoid duplicate nodes and ensure relationships are semantically accurate.
        - Keep line count reasonable (< 250 lines) and layout balanced for readability.
        - When uncertain, make a reasonable, professional assumption and proceed.
        """
    ).strip()

    return prompt


__all__ = ["build_plantuml_prompt", "SUPPORTED_FORMATS"]
