
/**
 * Class Diagram Builder
 * @module classDiagramBuilder
 * @description Handles the generation of UML class diagrams in Mermaid format for Mermaid.js rendering.
 */

import {
  sanitizeClassName,
  createLabel,
  isValidClassName,
  getRelationshipSyntax,
  buildClassDefinition,
  createPlaceholderClass,
  filterRelations
} from './diagramUtils.js';

/**
 * Builds a complete UML class diagram in Mermaid format
 * @function buildClassDiagram
 * @param {Object} schema - Parsed codebase schema with classes and relations
 * @param {Object} languageVisibility - Map of language to visibility boolean
 * @param {Object} options - Diagram options (showFields, showMethods, showRelations, relationFilter, colorEdgesBySource)
 * @returns {string} Mermaid diagram string
 */
export const buildClassDiagram = (schema, languageVisibility = {}, options = {}) => {
  const {
    showFields = true,
    showMethods = true,
    showRelations = true,
    relationFilter = 'all',
    colorEdgesBySource = false
  } = options;

  let output = 'classDiagram\n';
  let classFound = false;
  const allClasses = new Set();
  const classAliases = new Map(); // original -> safe id

  // Get supported languages
  const languages = Object.keys(schema).filter(k => 
    k !== 'relations' && 
    Array.isArray(schema[k]) && 
    schema[k].length > 0
  );

  // Build classes for each language
  for (const language of languages) {
    if (!languageVisibility[language]) continue;
    
    const classes = schema[language] || [];
    for (const classData of classes) {
      const classDef = buildClassDefinition(classData, showFields, showMethods);
      if (classDef) {
        output += classDef;
        allClasses.add(classData.class);
        classFound = true;
      }
    }
  }

  // Handle relations
  const relations = filterRelations(schema.relations || [], showRelations, relationFilter);
  
  // Create placeholder classes for relation endpoints
  for (const relation of relations) {
    const fromClass = relation.from || relation.parent;
    const toClass = relation.to || relation.child;
    
    if (fromClass && !allClasses.has(fromClass)) {
      output += createPlaceholderClass(fromClass, allClasses);
      allClasses.add(fromClass);
    }
    
    if (toClass && !allClasses.has(toClass)) {
      output += createPlaceholderClass(toClass, allClasses);
      allClasses.add(toClass);
    }
  }

  // Add relationships
  const relationLines = [];
  for (const relation of relations) {
    const fromClass = relation.from || relation.parent;
    const toClass = relation.to || relation.child;
    
    if (!fromClass || !toClass) continue;
    
    const label = relation.source === 'ai' ? ' : AI' : 
                 relation.source === 'heuristic' ? ' : H' : '';
    
    const relationSyntax = getRelationshipSyntax(
      relation.type, 
      fromClass, 
      toClass, 
      label
    );
    
    if (relationSyntax) {
      relationLines.push(relationSyntax);
    }
  }

  if (relationLines.length > 0) {
    output += relationLines.join('\n') + '\n';
  }

  // Clean up any invalid Mermaid lines
  output = cleanupMermaidOutput(output);

  // Handle empty diagram
  if (!classFound && relations.length === 0) {
    return 'classDiagram\n  note "No supported classes found in the repository."';
  }

  return output;
};

/**
 * Cleans up invalid Mermaid syntax from the output
 */
const cleanupMermaidOutput = (output) => {
  return output
    .split('\n')
    .filter(line => {
      // Remove lines with invalid patterns
      const invalidPatterns = [
        /class\s+\w+\s+(java|python|csharp|cpp|typescript|javascript);/,
        /class\s+\w+\s+(java|python|csharp|cpp|typescript|javascript)\s+fill:/,
        /classA\s+(java|python|csharp|cpp|typescript|javascript)\s+fill:/
      ];
      
      return !invalidPatterns.some(pattern => pattern.test(line));
    })
    .join('\n');
};