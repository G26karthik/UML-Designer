
/**
 * Other Diagram Builders
 * @module otherDiagramBuilders
 * @description Handles the generation of Use Case, Activity, Sequence, and State diagrams for Mermaid.js rendering.
 */

import { sanitizeClassName } from './diagramUtils.js';

/**
 * Builds a Use Case diagram
 */
export const buildUseCaseDiagram = (schema) => {
  const systemName = schema?.meta?.system || 'System';
  const endpoints = Array.isArray(schema?.endpoints) ? schema.endpoints : [];
  const uniqueUseCases = new Map();
  
  // Extract meaningful use cases from endpoints
  for (const endpoint of endpoints) {
    const method = (endpoint.method || 'GET').toUpperCase();
    const path = endpoint.path || '/';
    const cleanPath = path.replace(/^\//, '').replace(/\//g, '_') || 'root';
    const ucName = `${method}_${cleanPath}`;
    uniqueUseCases.set(ucName, { method, path, framework: endpoint.framework });
  }
  
  // Add default use cases if none found
  if (uniqueUseCases.size === 0) {
    uniqueUseCases.set('Analyze_Repository', { method: 'POST', path: '/analyze', framework: 'api' });
    uniqueUseCases.set('Export_Diagram', { method: 'GET', path: '/export', framework: 'ui' });
    uniqueUseCases.set('View_Diagram', { method: 'GET', path: '/', framework: 'ui' });
  }
  
  let output = 'flowchart TD\n';
  output += '  %% Use Case Diagram - Professional UML Notation\n';
  
  // Define actors
  output += '  User(("User"))\n';
  output += `  System[["${systemName}"]]\n`;
  
  // Define use cases with proper notation
  let ucIndex = 0;
  const ucIds = [];
  for (const [ucName, details] of uniqueUseCases.entries()) {
    const id = `UC${ucIndex++}`;
    ucIds.push(id);
    const displayName = `${details.method} ${details.path}`;
    output += `  ${id}("${displayName}")\n`;
  }
  
  // Add relationships
  for (const ucId of ucIds) {
    output += `  User --> ${ucId}\n`;
    output += `  ${ucId} --> System\n`;
  }
  
  // Add system boundary
  output += '  subgraph "System Boundary"\n';
  output += '    direction TB\n';
  for (const ucId of ucIds) {
    output += `    ${ucId}\n`;
  }
  output += '  end\n';
  
  return output;
};

/**
 * Builds an Activity diagram in Mermaid format
 * @function buildActivityDiagram
 * @param {Object} schema - Parsed codebase schema
 * @returns {string} Mermaid activity diagram string
 */
export const buildActivityDiagram = (schema) => {
  const systemName = schema?.meta?.system || 'Repository';
  const classes = extractAllClasses(schema);
  const relations = schema.relations || [];
  
  let output = 'flowchart TD\n';
  output += '  %% Activity Diagram - Generated from repository schema\n';

  output += '  Start((Start))\n';
  output += '  User[["User (developer / runner)"]]\n';
  
  // Find main entry points
  const mainClasses = classes.filter(c => 
    (c.methods || []).some(m => /main|run|start/i.test(m))
  );

  output += `  User --> SelectRepo["Open ${systemName} repository"]\n`;
  
  if (mainClasses.length > 0) {
    output += `  SelectRepo --> RunMain["Run main entry: ${mainClasses[0].class}"]\n`;
    output += '  RunMain --> Init["Initialize classes & resources"]\n';
  } else if (schema.endpoints && schema.endpoints.length > 0) {
    output += '  SelectRepo --> InspectAPI["Inspect API/endpoints"]\n';
    output += '  InspectAPI --> CallEndpoint["Call endpoint(s)"]\n';
    output += '  CallEndpoint --> ProcessRequest["Process request in code"]\n';
    output += '  ProcessRequest --> RenderResult["Produce output"]\n';
  } else {
    output += '  SelectRepo --> Explore["Explore classes & methods"]\n';
    output += '  Explore --> UseCases["Identify use-cases from code structure"]\n';
  }

  // Show interactions from relations
  if (relations.length > 0) {
    const topClasses = getTopClassesByRelations(relations, 6);
    
    if (topClasses.length > 0) {
      output += '  subgraph "Interactions"\n';
      
      for (const className of topClasses) {
        const id = sanitizeClassName(className);
        output += `    ${id}["${className}"]\n`;
      }
      
      output += '  end\n';

      // Draw flows between top classes
      for (const relation of relations) {
        if (topClasses.includes(relation.from) && topClasses.includes(relation.to)) {
          const fromId = sanitizeClassName(relation.from);
          const toId = sanitizeClassName(relation.to);
          // Use Mermaid edge label syntax: -->|label| 
          if (relation.type && relation.type.trim()) {
            output += `  ${fromId} -->|${relation.type}| ${toId}\n`;
          } else {
            output += `  ${fromId} --> ${toId}\n`;
          }
        }
      }
    }
  }

  output += '  End((End))\n';
  return output;
};

/**
 * Builds a Sequence diagram
 */
export const buildSequenceDiagram = (schema) => {
  const relations = schema.relations || [];
  const allClasses = new Set();
  
  // Collect all classes from relations
  for (const relation of relations) {
    if (relation.from) allClasses.add(relation.from);
    if (relation.to) allClasses.add(relation.to);
  }
  
  const topClasses = Array.from(allClasses).slice(0, 6);

  let output = 'sequenceDiagram\n';
  output += '  %% Sequence Diagram - Derived from repository relations\n';
  output += '  participant U as User\n';
  
  // Add participants
  for (const className of topClasses) {
    const safeId = sanitizeClassName(className);
    const label = `"${className.replace(/"/g, '\\"')}"`;
    output += `  participant ${safeId} as ${label}\n`;
  }

  // Handle case with no relations but endpoints
  if (topClasses.length === 0 && Array.isArray(schema.endpoints) && schema.endpoints.length > 0) {
    const endpoint = schema.endpoints[0];
    output += `  U->>API: ${endpoint.method || 'CALL'} ${endpoint.path || '/'}\n`;
    output += '  activate API\n';
    output += '  API-->>U: response\n';
    output += '  deactivate API\n';
    return output;
  }

  // Create interaction sequence from relations
  const limitedRelations = relations.slice(0, 10); // Limit for readability
  
  for (const relation of limitedRelations) {
    if (!relation.from || !relation.to) continue;
    
    const fromId = sanitizeClassName(relation.from);
    const toId = sanitizeClassName(relation.to);
    const message = (relation.type || 'call').replace(/[^A-Za-z0-9_ ]/g, ' ');
    
    output += `  ${fromId}->>${toId}: ${message}\n`;
    output += `  activate ${toId}\n`;
    output += `  ${toId}-->>${fromId}: return\n`;
    output += `  deactivate ${toId}\n`;
  }

  return output;
};

/**
 * Builds a State diagram
 */
export const buildStateDiagram = (schema) => {
  const systemName = schema?.meta?.system || 'Repository';
  const classes = extractAllClasses(schema);
  
  let output = 'stateDiagram-v2\n';
  output += `  %% State Diagram - Derived for ${systemName}\n`;

  // Find classes with state-related fields
  const statefulClasses = classes.filter(c => 
    (c.fields || []).some(f => /state|status/i.test(String(f)))
  );

  if (statefulClasses.length === 0) {
    // Fallback: generic lifecycle for top classes
    const topClasses = classes.slice(0, 4).map(c => c.class || 'Class');
    
    if (topClasses.length === 0) {
      output += '  [*] --> Idle\n';
      output += '  state "No precise state info available" as Idle\n';
      output += '  Idle --> [*]\n';
      return output;
    }
    
    for (const className of topClasses) {
      const id = sanitizeClassName(className);
      output += `  [*] --> ${id}\n`;
      output += `  ${id} : Created\n`;
      output += `  ${id} --> ${id}_Active : initialize\n`;
      output += `  ${id}_Active : Running\n`;
      output += `  ${id}_Active --> ${id}_Done : finish\n`;
      output += `  ${id}_Done : Completed\n`;
      output += `  ${id}_Done --> ${id} : reset\n`;
    }
    
    return output;
  }

  // Create state machines for stateful classes
  for (const classData of statefulClasses) {
    const className = classData.class || 'Class';
    const id = sanitizeClassName(className);
    
    output += `  [*] --> ${id}_Idle\n`;
    output += `  ${id}_Idle : ${className} idle\n`;
    output += `  ${id}_Idle --> ${id}_Active : start\n`;
    output += `  ${id}_Active : processing\n`;
    output += `  ${id}_Active --> ${id}_Done : complete\n`;
    output += `  ${id}_Done : finished\n`;
    output += `  ${id}_Done --> ${id}_Idle : reset\n`;
  }

  return output;
};

/**
 * Helper function to extract all classes from schema
 */
const extractAllClasses = (schema) => {
  const allClasses = [];
  const languages = ['python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c'];
  
  for (const language of languages) {
    if (Array.isArray(schema[language])) {
      allClasses.push(...schema[language]);
    }
  }
  
  return allClasses;
};

/**
 * Helper function to get top classes by relation count
 */
const getTopClassesByRelations = (relations, limit = 6) => {
  const classCount = {};
  
  for (const relation of relations) {
    if (relation.from) {
      classCount[relation.from] = (classCount[relation.from] || 0) + 1;
    }
    if (relation.to) {
      classCount[relation.to] = (classCount[relation.to] || 0) + 1;
    }
  }
  
  return Object.keys(classCount)
    .sort((a, b) => classCount[b] - classCount[a])
    .slice(0, limit);
};