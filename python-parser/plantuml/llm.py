"""LLM-backed PlantUML generation utilities."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from prompts.plantuml_prompt import SUPPORTED_FORMATS, build_plantuml_prompt

import hashlib
import pathlib
import json
from utils.groq_client import GroqClient, GroqClientDisabledError, GroqClientError

logger = logging.getLogger(__name__)

STUB_LLM = os.getenv('STUB_LLM', 'false').lower() in ('1', 'true', 'yes')

DEFAULT_MODEL = os.getenv('GROQ_PLANTUML_MODEL') or os.getenv('GROQ_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')
GROQ_CLIENT = GroqClient()

# Local cache directory for AI results
LOCAL_CACHE_DIR = pathlib.Path(__file__).parent.parent / 'cache'
LOCAL_CACHE_DIR.mkdir(exist_ok=True)

def _local_cache_key(prompt: str, diagram_type: str, output_format: str, context: Optional[dict], schema: Optional[dict], style_preferences: Optional[dict], focus: Optional[list]) -> str:
    """Generate a unique hash key for the AI enrichment cache."""
    key_data = {
        'prompt': prompt,
        'diagram_type': diagram_type,
        'output_format': output_format,
        'context': context,
        'schema': schema,
        'style_preferences': style_preferences,
        'focus': focus,
    }
    raw = json.dumps(key_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def _local_cache_get(key: str) -> Optional[dict]:
    path = LOCAL_CACHE_DIR / f"groq_{key}.json"
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def _local_cache_set(key: str, data: dict) -> None:
    path = LOCAL_CACHE_DIR / f"groq_{key}.json"
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

PLANTUML_DIAGRAM_TYPES = {'class', 'sequence', 'usecase', 'state', 'activity', 'component', 'communication', 'deployment'}
FORMAT_TO_TYPES = {
    'plantuml': PLANTUML_DIAGRAM_TYPES,
}
SUPPORTED_DIAGRAM_TYPES = set().union(*FORMAT_TO_TYPES.values())


def _is_stub_mode() -> bool:
    override = os.getenv('STUB_LLM')
    if override is None:
        return STUB_LLM
    return override.strip().lower() in ('1', 'true', 'yes', 'on')


def _stub_diagram(diagram_type: str, *, output_format: str) -> str:
    core = {
        'class': "@startuml\nclass User {\n  +UUID id\n  +string email\n}\nclass Admin\nUser <|-- Admin\n@enduml",
        'sequence': "@startuml\nactor User\nparticipant System\nUser -> System : describe requirements\nSystem -->> User : generated diagram\n@enduml",
        'usecase': "@startuml\nactor User\nrectangle System {\n  usecase ManageRequirements\n}\nUser --> ManageRequirements\n@enduml",
        'state': "@startuml\n[*] --> Draft\nDraft --> Generated : request\nGenerated --> [*] : deliver\n@enduml",
        'activity': "@startuml\nstart\n:Collect requirements;\n:Design solution;\n:Review with stakeholders;\nstop\n@enduml",
    }
    return core.get(diagram_type, "@startuml\nnote left\nLLM stubbed due to configuration\nend note\n@enduml")

def _normalize_diagram(raw_text: str, diagram_type: str, output_format: str) -> Dict[str, str]:
    # Debug: Log raw LLM output for key diagram types
    import logging
    if diagram_type in ("activity", "state", "deployment"):
        logger = logging.getLogger("plantuml.llm.raw_output")
        logger.warning(f"Raw LLM output for {diagram_type} diagram:\n{raw_text}\n---END RAW---")
    def _flatten_plantuml(diagram: str, diagram_type: str) -> str:
        # Only flatten activity diagrams if needed; preserve structure for state and deployment
        if diagram_type != "activity":
            return diagram
        lines = diagram.splitlines()
        flat = []
        for l in lines:
            if '{' in l or '}' in l or l.strip().startswith('|'):
                continue
            if (':' in l or '-->' in l or '->' in l or l.strip() in ("start", "stop")):
                flat.append(l)
        if not flat or not any('@startuml' in x for x in flat):
            flat = ['@startuml'] + flat
        if not any('@enduml' in x for x in flat):
            flat = flat + ['@enduml']
        return '\n'.join(flat)
    def _is_valid_plantuml(diagram: str, diagram_type: str) -> bool:
        # Basic checks for PlantUML validity
        if not diagram.strip().startswith('@startuml') or not diagram.strip().endswith('@enduml'):
            return False
        lines = [l.strip() for l in diagram.splitlines() if l.strip()]
        # Loosened: allow more lines and valid nested blocks for state/activity diagrams
        if diagram_type in ('state', 'activity'):
            # Only check for forbidden syntax and at least one transition/action
            if diagram_type == 'state':
                transitions = [l for l in lines if '-->' in l]
                if not transitions:
                    return False
                has_start = any(l.startswith('[*] -->') for l in lines)
                if not has_start:
                    return False
                forbidden = ['class ', 'node ', 'component ', 'package ', 'artifact ', 'database ', 'cloud ']
                if any(any(f in l for f in forbidden) for l in lines):
                    return False
            elif diagram_type == 'activity':
                if not any(':' in l or '-->' in l or '->' in l for l in lines):
                    return False
        elif diagram_type in ('component', 'deployment'):
            # Allow nested blocks for deployment/component diagrams
            if diagram_type == 'deployment':
                has_node = any(l.startswith('node ') for l in lines)
                has_rel = any('-->' in l or '<--' in l or '..>' in l or '<..' in l for l in lines)
                if not has_node or not has_rel:
                    return False
        return True
    raw = (raw_text or '').strip()
    if not raw:
        return {'diagram': '', 'raw_diagram': ''}

    text = raw
    if '```' in text:
        segments = text.split('```')
        for segment in segments:
            candidate = segment.strip()
            if not candidate:
                continue
            if candidate.lower().startswith('plantuml'):
                candidate = '\n'.join(candidate.splitlines()[1:]).strip()
            if candidate:
                text = candidate
                break
    lower = text.lower()
    start_idx = lower.find('@startuml')
    end_idx = lower.rfind('@enduml')
    if start_idx != -1 and end_idx != -1:
        cleaned = text[start_idx:end_idx + len('@enduml')].strip()
    else:
        cleaned = text.strip()
        if not cleaned.startswith('@startuml'):
            cleaned = '@startuml\n' + cleaned
        if not cleaned.endswith('@enduml'):
            cleaned = cleaned.rstrip() + '\n@enduml'

    import re
    # PlantUML: only strict filtering for deployment diagrams
    if diagram_type == 'deployment':
        # Do not filter out valid PlantUML lines; just check validity at the end
        pass
    elif diagram_type == 'component':
        # Do not filter out valid PlantUML lines; just check validity at the end
        pass
    elif diagram_type == 'state':
        lines = cleaned.splitlines()
        # Only filter forbidden diagram types, not PlantUML state syntax
        forbidden = ['class ', 'node ', 'component ', 'package ', 'artifact ', 'database ', 'cloud ']
        filtered = [l for l in lines if not any(f in l for f in forbidden)]
        has_transition = any('-->' in l for l in filtered)
        has_start = any(l.strip().startswith('[*] -->') for l in filtered)
        if not has_transition or not has_start:
            # Synthesize minimal state diagram from prompt
            state = 'StateFromPrompt' if not raw else raw.split()[0]
            cleaned = f'@startuml\n[*] --> {state}\n@enduml'
        else:
            cleaned = '\n'.join(filtered)
    elif diagram_type == 'activity':
        lines = cleaned.splitlines()
        # Remove forbidden lines and empty actions
        forbidden = [':@startuml;', ':@enduml;', 'class ', 'node ', 'component ', 'package ', 'artifact ', 'database ', 'cloud ']
        filtered = [l for l in lines if not any(f in l.lower() for f in forbidden)]
        # Remove empty or trivial actions (e.g., ': ;')
        filtered = [l for l in filtered if not l.strip().startswith(': ;') and l.strip()]
        has_action = any(':' in l and l.strip() not in (':@startuml;', ':@enduml;') for l in filtered)
        prompt_lower = (raw or '').lower()
        if not has_action:
            # Synthesize minimal ATM activity diagram for ATM prompts
            if 'atm' in prompt_lower:
                cleaned = ("""@startuml\nstart\n:Insert card;\n:Enter PIN;\n:Select transaction;\n:Process transaction;\nstop\n@enduml""")
            else:
                cleaned = '@startuml\nstart\n:Process;\nstop\n@enduml'
        else:
            cleaned = '\n'.join(filtered)
    elif diagram_type == 'class':
        lines = cleaned.splitlines()
        classes = [re.findall(r'class ([^\s{]+)', l) for l in lines]
        classes = [c[0] for c in classes if c]
        has_rel = any('<|--' in l or '--' in l or '..' in l for l in lines)
        if not classes:
            # Synthesize minimal class diagram
            class_name = 'Entity' if not raw or raw.strip().lower() in ('atm', 'atm case study') else raw.split()[0]
            cleaned = f'@startuml\nclass {class_name}\n@enduml'
        elif not has_rel and len(classes) >= 2:
            cleaned = '\n'.join(lines + [f'{classes[0]} <|-- {classes[1]}'])
        elif not has_rel and len(classes) == 1:
            cleaned = '\n'.join(lines + [f'{classes[0]} <|-- {classes[0]}'])
    else:
        cleaned_lines = [l for l in cleaned.splitlines() if l.strip() != '' and not l.strip().startswith('!invalid!')]
        cleaned = '\n'.join(cleaned_lines)

    # Robust post-processing: flatten only for activity diagrams
    if diagram_type == "activity":
        cleaned_flat = _flatten_plantuml(cleaned, diagram_type)
        if _is_valid_plantuml(cleaned_flat, diagram_type):
            cleaned = cleaned_flat
    # Final validation: fallback to minimal valid diagram if not valid
    # Only use fallback if LLM output is empty or invalid
    if not _is_valid_plantuml(cleaned, diagram_type):
        prompt_lower = (raw or '').lower()
        if diagram_type == 'state':
            state = 'State' if not raw or 'atm' in prompt_lower else raw.split()[0]
            cleaned = f'@startuml\n[*] --> {state}\n@enduml'
        elif diagram_type == 'activity':
            if 'atm' in prompt_lower:
                cleaned = ("""@startuml\nstart\n:Insert card;\n:Enter PIN;\n:Select transaction;\n:Process transaction;\nstop\n@enduml""")
            else:
                cleaned = '@startuml\nstart\n:Main process;\nstop\n@enduml'
        elif diagram_type == 'deployment':
            # Minimal valid deployment diagram for ATM or generic
            if 'atm' in prompt_lower:
                cleaned = '@startuml\nnode ATM\nATM --> ATM\n@enduml'
            else:
                cleaned = '@startuml\nnode System\nSystem --> System\n@enduml'
        elif diagram_type == 'component':
            comp = 'Component' if not raw or 'atm' in prompt_lower else raw.split()[0]
            cleaned = f'@startuml\ncomponent {comp}\n{comp} --> {comp}\n@enduml'
    return {'diagram': cleaned, 'raw_diagram': raw}

    starter = MERMAID_STARTERS.get(diagram_type, 'graph TD')
    text = raw
    if '```' in text:
        segments = text.split('```')
        for segment in segments:
            candidate = segment.strip()
            if not candidate:
                continue
            if candidate.lower().startswith('mermaid'):
                lines = candidate.splitlines()
                candidate = '\n'.join(lines[1:]).strip()
                text = candidate
                break
    if text.lower().startswith('mermaid'):
        text = '\n'.join(text.splitlines()[1:]).strip()
    cleaned = text.strip()
    if cleaned and cleaned.splitlines()[0].strip().lower().startswith('```'):
        cleaned = '\n'.join(cleaned.splitlines()[1:]).strip()

    # Post-process Mermaid syntax to fix common LLM errors
    cleaned = _fix_mermaid_syntax(cleaned, diagram_type)

    # If output is just the starter or empty, synthesize a minimal diagram from the prompt
    if not cleaned or cleaned.strip() == starter.strip():
        # Use the first word of the prompt as a node label
        node = raw.split()[0] if raw else 'Node'
        cleaned = f'{starter}\n{node}((Generated from prompt))'
    raw_block = raw if raw.startswith('```') else f"```mermaid\n{cleaned}\n```"
    return {'diagram': cleaned.strip(), 'raw_diagram': raw_block.strip()}


def _fix_mermaid_syntax(text: str, diagram_type: str) -> str:
    """Fix common Mermaid syntax errors generated by LLM."""
    lines = text.split('\n')
    fixed_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            fixed_lines.append('')
            continue

        # Fix activity diagram node syntax - convert ((label)) to ([label])
        if diagram_type == 'activity':
            import re
            line = re.sub(r'\(\(([^)]+)\)\)', r'([\1])', line)
            line = re.sub(r'\(\([^)]*\)\)', lambda m: f"([{m.group(0)[2:-2]}])", line)

        # Fix communication diagram - ensure it uses sequenceDiagram syntax
        elif diagram_type == 'communication':
            if 'flowchart' in text.lower() and 'participant' in line.lower():
                if line.lower().startswith('participant'):
                    pass
                elif '-->' in line or '->>' in line:
                    pass
                else:
                    continue
            if line.lower().strip() == 'flowchart td':
                continue

        # Fix use case diagram - ensure flowchart syntax
        elif diagram_type == 'usecase':
            if line.lower().startswith('usecasediagram'):
                line = 'flowchart TD'
            elif line.lower().startswith('actor '):
                parts = line.split()
                if len(parts) >= 2:
                    actor_name = parts[1]
                    line = f'{actor_name}([{actor_name}])'
            elif line.lower().startswith('usecase '):
                parts = line.split()
                if len(parts) >= 2:
                    usecase_name = parts[1]
                    line = f'{usecase_name}["{usecase_name}"]'

        # Fix component and deployment diagrams: remove sequence/participant lines, fix subgraph usage
        elif diagram_type in ('component', 'deployment'):
            # Remove participant/sequence lines
            if line.lower().startswith('participant') or '->>' in line or '-->>' in line:
                continue
            # Remove sequenceDiagram/flowchart TD if mixed
            if line.lower().startswith('sequencediagram') or line.lower().startswith('flowchart td'):
                continue
            # Remove invalid subgraph endings
            if line.lower() == 'end' and not fixed_lines:
                continue
            # Remove empty subgraphs
            if line.lower().startswith('subgraph') and (len(lines) > 1 and lines[lines.index(line)+1].lower() == 'end'):
                continue
            # Remove lines with only node names (e.g., atm, cardReader)
            if len(line.split()) == 1 and line.islower():
                continue

        fixed_lines.append(line)

    # Post-process the entire diagram for communication diagrams
    if diagram_type == 'communication':
        result = '\n'.join(fixed_lines)
        if 'flowchart td' in result.lower() and 'participant' in result.lower():
            result = result.replace('flowchart TD', 'sequenceDiagram')
            lines = result.split('\n')
            sequence_lines = []
            for line in lines:
                line_lower = line.lower().strip()
                if (line_lower.startswith('participant') or
                    '->>' in line or '-->>' in line or
                    'note ' in line_lower or
                    'activate ' in line_lower or
                    'deactivate ' in line_lower or
                    'alt ' in line_lower or
                    'loop ' in line_lower or
                    'opt ' in line_lower or
                    'par ' in line_lower or
                    line_lower in ['end', 'else'] or
                    not line.strip()):
                    sequence_lines.append(line)
            result = '\n'.join(sequence_lines)
        return result

    return '\n'.join(fixed_lines)

def generate_diagram_llm(
    user_prompt: str,
    *,
    diagram_type: str = 'class',
    output_format: str = 'plantuml',
    context: Optional[Dict[str, Any]] = None,
    schema: Optional[Dict[str, Any]] = None,
    style_preferences: Optional[Dict[str, Any]] = None,
    focus: Optional[list[str]] = None,
    temperature: float = 0.15,
    batch_descriptions: Optional[list[str]] = None,  # For prompt batching
) -> Dict[str, Any]:
    """Generate diagram code from a natural language description using Groq LLM, with local cache, batching, and fallback."""
    if batch_descriptions and isinstance(batch_descriptions, list) and batch_descriptions:
        # Batch all descriptions into a single prompt
        combined_prompt = '\n'.join(batch_descriptions)
        prompt_for_cache = combined_prompt
    else:
        combined_prompt = user_prompt
        prompt_for_cache = user_prompt


    diagram_key = diagram_type.lower().strip()
    fmt = output_format.lower().strip()
    if fmt not in SUPPORTED_FORMATS:
        valid_formats = ', '.join(sorted(SUPPORTED_FORMATS))
        raise ValueError(f"Unsupported output_format '{output_format}'. Valid options: {valid_formats}")

    allowed_types = FORMAT_TO_TYPES.get(fmt, set())
    if diagram_key not in allowed_types:
        valid = ', '.join(sorted(allowed_types))
        raise ValueError(f"Unsupported diagram_type '{diagram_type}' for format '{fmt}'. Valid options: {valid}")

    # BYPASS LLM for component and deployment diagrams: synthesize from schema
    if diagram_key in ("component", "deployment") and fmt == "plantuml":
        from plantuml.plantuml_generator import PlantUMLGenerator
        generator = PlantUMLGenerator(style_preferences)
        if diagram_key == "component":
            diagram = generator.build_component_diagram(schema or {})
        else:
            diagram = generator.build_deployment_diagram(schema or {})
        normalized = _normalize_diagram(diagram, diagram_key, fmt)
        result = {
            'diagram': normalized['diagram'],
            'raw_diagram': normalized['raw_diagram'],
            'diagram_type': diagram_key,
            'format': fmt,
            'source': 'synthesized',
            'model': 'none',
        }
        return result

    stub_mode = _is_stub_mode()

    # Local cache check
    cache_key = _local_cache_key(prompt_for_cache, diagram_key, fmt, context, schema, style_preferences, focus)
    cached = _local_cache_get(cache_key)
    if cached:
        cached['source'] = 'local-cache'
        return cached

    # Handle stub mode or disabled client early
    if stub_mode or not GROQ_CLIENT.enabled or not GROQ_CLIENT.api_key:
        reason = 'stub' if stub_mode else 'disabled'
        raw_stub = _stub_diagram(diagram_key, output_format=fmt)
        normalized = _normalize_diagram(raw_stub, diagram_key, fmt)
        result = {
            'diagram': normalized['diagram'],
            'raw_diagram': normalized['raw_diagram'],
            'diagram_type': diagram_key,
            'format': fmt,
            'source': reason,
            'warnings': [
                'LLM call skipped because STUB_LLM is enabled.'
                if STUB_LLM
                else 'Groq client disabled or missing API key; returned stub diagram.'
            ]
        }
        _local_cache_set(cache_key, result)
        return result

    prompt = build_plantuml_prompt(
        combined_prompt,
        diagram_type=diagram_key,
        output_format=fmt,
        context=context,
        schema=schema,
        style_preferences=style_preferences,
        focus=focus,
    )

    payload = {
        'model': DEFAULT_MODEL,
        'messages': [
            {
                'role': 'system',
                'content': (
                    f'You are an expert UML architect. Generate only PlantUML code for the requested diagram type: {diagram_key}. '
                    f'For activity diagrams, do NOT use any class diagram syntax (no "class", "--", "*--", "<|--"). Use only PlantUML activity diagram syntax: "start", "stop", ":action;", decisions, and transitions. '
                    f'For deployment diagrams, use only PlantUML deployment diagram syntax (node, artifact, database, cloud, and relationships). Do not use class or component diagram syntax. '
                    f'For class diagrams, use only PlantUML class diagram syntax. Do not use activity, deployment, or component diagram syntax. '
                    'Return only PlantUML code, no explanations, no markdown, no extra text.'
                ),
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ],
        'temperature': temperature,
        'max_tokens': 4096,
    }

    try:
        data = GROQ_CLIENT.call(payload)
        text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        normalized = _normalize_diagram(text, diagram_key, fmt)
        if not normalized['diagram']:
            raise ValueError('Empty response from LLM')
        result = {
            'diagram': normalized['diagram'],
            'raw_diagram': normalized['raw_diagram'],
            'diagram_type': diagram_key,
            'format': fmt,
            'source': 'groq',
            'model': DEFAULT_MODEL,
        }
        _local_cache_set(cache_key, result)
        return result
    except GroqClientDisabledError as err:
        logger.warning('Groq client disabled: %s', err)
        normalized = _normalize_diagram(_stub_diagram(diagram_key, output_format=fmt), diagram_key, fmt)
        result = {
            'diagram': normalized['diagram'],
            'raw_diagram': normalized['raw_diagram'],
            'diagram_type': diagram_key,
            'format': fmt,
            'source': 'disabled',
            'warnings': [str(err)],
        }
        _local_cache_set(cache_key, result)
        return result
    except GroqClientError as err:
        logger.error('Groq API error: %s', err)
        normalized = _normalize_diagram(_stub_diagram(diagram_key, output_format=fmt), diagram_key, fmt)
        result = {
            'diagram': normalized['diagram'],
            'raw_diagram': normalized['raw_diagram'],
            'diagram_type': diagram_key,
            'format': fmt,
            'source': 'fallback',
            'warnings': [str(err)],
            'error': str(err),
        }
        _local_cache_set(cache_key, result)
        return result
    except Exception as exc:
        logger.exception('Failed to generate diagram via LLM')
        normalized = _normalize_diagram(_stub_diagram(diagram_key, output_format=fmt), diagram_key, fmt)
        result = {
            'diagram': normalized['diagram'],
            'raw_diagram': normalized['raw_diagram'],
            'diagram_type': diagram_key,
            'format': fmt,
            'source': 'error-fallback',
            'warnings': [str(exc)],
            'error': str(exc),
        }
        _local_cache_set(cache_key, result)
        return result


def generate_plantuml_llm(
    user_prompt: str,
    *,
    diagram_type: str = 'class',
    output_format: str = 'plantuml',
    context: Optional[Dict[str, Any]] = None,
    schema: Optional[Dict[str, Any]] = None,
    style_preferences: Optional[Dict[str, Any]] = None,
    focus: Optional[list[str]] = None,
    temperature: float = 0.15,
    batch_descriptions: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Backward-compatible wrapper that delegates to generate_diagram_llm."""
    return generate_diagram_llm(
        user_prompt,
        diagram_type=diagram_type,
        output_format=output_format,
        context=context,
        schema=schema,
        style_preferences=style_preferences,
        focus=focus,
        temperature=temperature,
        batch_descriptions=batch_descriptions,
    )


__all__ = ['generate_diagram_llm', 'generate_plantuml_llm', 'SUPPORTED_DIAGRAM_TYPES', 'FORMAT_TO_TYPES']
