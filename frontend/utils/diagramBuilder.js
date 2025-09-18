/**
 * Main Diagram Builder
 * Coordinates different diagram types and provides a unified interface
 */

import { buildClassDiagram } from './classDiagramBuilder.js';
import { 
  buildUseCaseDiagram, 
  buildActivityDiagram, 
  buildSequenceDiagram, 
  buildStateDiagram 
} from './otherDiagramBuilders.js';

/**
 * Main function to build any type of UML diagram
 */
export const buildDiagram = (schema, diagramType = 'class', languageVisibility = {}, options = {}) => {
  try {
    const type = diagramType.toLowerCase();
    // Prefer new AI-populated fields if present
    if (type === 'usecase' || type === 'use-case') {
      if (Array.isArray(schema.usecases) && schema.usecases.length > 0) {
        // If AI-populated usecases field exists, build from it
        return buildUseCaseDiagram({ ...schema, endpoints: schema.usecases });
      }
      return buildUseCaseDiagram(schema);
    }
    if (type === 'activity') {
      if (typeof schema.activity === 'string' && schema.activity.trim().length > 0) {
        // If AI-populated activity diagram string exists, use it directly
        return schema.activity;
      }
      return buildActivityDiagram(schema);
    }
    if (type === 'sequence') {
      if (typeof schema.sequence === 'string' && schema.sequence.trim().length > 0) {
        // If AI-populated sequence diagram string exists, use it directly
        return schema.sequence;
      }
      return buildSequenceDiagram(schema);
    }
    if (type === 'state' || type === 'statediagram') {
      if (typeof schema.states === 'string' && schema.states.trim().length > 0) {
        // If AI-populated state diagram string exists, use it directly
        return schema.states;
      }
      return buildStateDiagram(schema);
    }
    // Class diagram
    if (typeof schema.classdiagram === 'string' && schema.classdiagram.trim().length > 0) {
      // If AI-populated class diagram string exists, use it directly
      return schema.classdiagram;
    }
    return buildClassDiagram(schema, languageVisibility, options);
  } catch (error) {
    console.error('Diagram building error:', error);
    return `%% Error building diagram: ${error.message || 'Unknown error'}`;
  }
};

/**
 * Validates schema before diagram building
 */
export const validateSchema = (schema) => {
  if (!schema || typeof schema !== 'object') {
    return { isValid: false, error: 'Schema is required and must be an object' };
  }
  
  // Check for at least one supported language or relations
  const languages = ['python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c'];
  const hasClasses = languages.some(lang => 
    Array.isArray(schema[lang]) && schema[lang].length > 0
  );
  
  const hasRelations = Array.isArray(schema.relations) && schema.relations.length > 0;
  const hasEndpoints = Array.isArray(schema.endpoints) && schema.endpoints.length > 0;
  
  if (!hasClasses && !hasRelations && !hasEndpoints) {
    return { 
      isValid: false, 
      error: 'Schema must contain at least classes, relations, or endpoints' 
    };
  }
  
  return { isValid: true };
};

/**
 * Gets available languages from schema
 */
export const getAvailableLanguages = (schema) => {
  if (!schema) return [];
  
  const languages = ['python', 'java', 'csharp', 'javascript', 'typescript', 'cpp', 'c'];
  return languages.filter(lang => 
    Array.isArray(schema[lang]) && schema[lang].length > 0
  );
};

/**
 * Gets diagram statistics
 */
export const getDiagramStats = (schema) => {
  if (!schema) return null;
  
  const languages = getAvailableLanguages(schema);
  const stats = {
    languages: languages.length,
    classes: 0,
    relations: Array.isArray(schema.relations) ? schema.relations.length : 0,
    endpoints: Array.isArray(schema.endpoints) ? schema.endpoints.length : 0,
    byLanguage: {}
  };
  
  for (const lang of languages) {
    const classes = schema[lang] || [];
    stats.classes += classes.length;
    stats.byLanguage[lang] = classes.length;
  }
  
  return stats;
};