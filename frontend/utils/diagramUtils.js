/**
 * Diagram Building Utilities
 * Modular functions for building different types of UML diagrams
 */

/**
 * Sanitizes class names for Mermaid compatibility
 */
export const sanitizeClassName = (name) => {
  if (!name) return 'UnknownClass';
  
  // Remove invalid characters and ensure valid Mermaid ID
  let sanitized = String(name).replace(/[^A-Za-z0-9_]/g, '_');
  
  // Ensure it starts with a letter or underscore
  if (!/^[A-Za-z_]/.test(sanitized)) {
    sanitized = `C_${sanitized}`;
  }
  
  return sanitized;
};

/**
 * Creates a safe label for Mermaid diagrams
 */
export const createLabel = (name) => {
  return `"${String(name).replace(/"/g, '\\"')}"`;
};

/**
 * Filters invalid class names
 */
export const isValidClassName = (className) => {
  if (!className || typeof className !== 'string') return false;
  
  // Filter out classes with spaces or file extensions
  if (/\s/.test(className)) return false;
  if (/\.(java|python|csharp|cpp|typescript|javascript|js|py|cs|cpp)$/i.test(className)) return false;
  
  return true;
};

/**
 * Maps relationship types to Mermaid syntax
 */
export const getRelationshipSyntax = (relationType, fromClass, toClass, label = '') => {
  const from = sanitizeClassName(fromClass);
  const to = sanitizeClassName(toClass);
  
  if (!from || !to || from === to) return '';
  
  const relationMap = {
    'extends': `${from} <|-- ${to}${label}`,
    'implements': `${from} <|.. ${to}${label}`,
    'composes': `${from} *-- ${to}${label}`,
    'composition': `${from} *-- ${to}${label}`,
    'aggregates': `${from} o-- ${to}${label}`,
    'aggregation': `${from} o-- ${to}${label}`,
    'uses': `${from} ..> ${to}${label}`,
    'depends': `${from} ..> ${to}${label}`,
    'dependency': `${from} ..> ${to}${label}`,
    'associates': `${from} --> ${to}${label}`,
    'association': `${from} --> ${to}${label}`,
  };
  
  return relationMap[relationType.toLowerCase()] || `${from} ..> ${to}${label}`;
};

/**
 * Builds a class definition for Mermaid UML diagrams
 * @function buildClassDefinition
 * @param {Object} classData - Class metadata (name, fields, methods, stereotype)
 * @param {boolean} showFields - Whether to include fields in output
 * @param {boolean} showMethods - Whether to include methods in output
 * @returns {string} Mermaid class definition string
 */
export const buildClassDefinition = (classData, showFields, showMethods) => {
  if (!isValidClassName(classData.class)) return '';
  
  const className = sanitizeClassName(classData.class);
  const fields = (classData.fields || []).filter(f => f && f.trim());
  const methods = (classData.methods || []).filter(m => m && m.trim());
  
  const isInterface = (classData.stereotype || '').toLowerCase() === 'interface';
  const stereo = isInterface ? ' <<interface>>' : '';
  
  let definition = '';
  
  // Check if we need braces
  const hasVisibleContent = (showFields && fields.length > 0) || (showMethods && methods.length > 0);
  
  if (hasVisibleContent) {
    definition += `class ${className}${stereo} {\n`;
    
    if (showFields) {
      fields.forEach(field => {
        definition += `  ${field}\n`;
      });
    }
    
    if (showMethods) {
      methods.forEach(method => {
        definition += `  ${method}()\n`;
      });
    }
    
    definition += '}\n';
  } else {
    // Empty class - no braces
    definition += `class ${className}${stereo}\n`;
  }
  
  // Add label if needed
  if (className !== classData.class) {
    definition += `class ${className} as ${createLabel(classData.class)}\n`;
  }
  
  return definition;
};

/**
 * Creates placeholder classes for relation endpoints in Mermaid diagrams
 * @function createPlaceholderClass
 * @param {string} className - Name of the class to create
 * @param {Set<string>} existingClasses - Set of already defined class names
 * @returns {string} Mermaid class definition string for placeholder
 */
export const createPlaceholderClass = (className, existingClasses) => {
  if (!className || existingClasses.has(className)) return '';
  
  const id = sanitizeClassName(className);
  let definition = `class ${id}\n`;
  
  if (id !== className) {
    definition += `class ${id} as ${createLabel(className)}\n`;
  }
  
  return definition;
};

/**
 * Filters and validates relations
 */
export const filterRelations = (relations, showRelations, relationFilter) => {
  if (!showRelations || !Array.isArray(relations)) return [];
  
  return relations.filter(relation => {
    // Basic validation
    if (!relation || !relation.from || !relation.to || !relation.type) return false;
    
    // Filter by source
    if (relationFilter !== 'all') {
      const source = relation.source || 'heuristic';
      if (source !== relationFilter) return false;
    }
    
    return true;
  });
};

/**
 * Language color palette for UI
 */
export const LANGUAGE_COLORS = {
  java: '#fde68a',
  python: '#bfdbfe',
  csharp: '#fca5a5',
  javascript: '#fcd34d',
  typescript: '#93c5fd',
  cpp: '#c7d2fe',
  c: '#a7f3d0',
  default: '#e5e7eb'
};

/**
 * Gets color for a language
 */
export const getLanguageColor = (language) => {
  return LANGUAGE_COLORS[language] || LANGUAGE_COLORS.default;
};