/**
 * Main Diagram Builder
 * Coordinates different diagram types and provides a unified interface
 * Supports PlantUML output format only (renderer is now hardcoded per diagram type)
 */

import logger from './logger';
// errorHandler.js and related exports removed. Use standard Error and generic messages below.


const extractErrorMessage = (payload, fallbackMessage) => {
  if (!payload) return fallbackMessage;
  if (payload instanceof Error) return payload.message;
  if (typeof payload === 'string') return payload;
  if (typeof payload === 'object') {
    if (typeof payload.message === 'string') return payload.message;
    if (typeof payload.error === 'string') return payload.error;
    if (payload.error && typeof payload.error.message === 'string') return payload.error.message;
    if (Array.isArray(payload.errors) && payload.errors.length > 0) {
      return extractErrorMessage(payload.errors[0], fallbackMessage);
    }
  }
  return fallbackMessage;
};



/**
 * Main function to build any type of UML diagram
 * @param {Object} schema - Analysis schema
 * @param {string} diagramType - Type of diagram: 'class' | 'usecase' | 'sequence' | 'activity' | 'state'
 * @param {Object} languageVisibility - Language filter settings
 * @param {Object} options - Additional options
 * @param {string} options.format - Output format: 'plantuml' (default: 'plantuml')
 * @param {Object} options.plantUMLConfig - PlantUML-specific configuration
 * @returns {Promise<string>} Diagram syntax string
 */

/**
 * Main function to build any type of UML diagram
 * @param {Object} schema - Analysis schema
 * @param {string} diagramType - Type of diagram: 'class' | 'usecase' | 'sequence' | 'activity' | 'state'
 * @param {Object} languageVisibility - Language filter settings
 * @param {Object} options - Additional options
 * @param {string} options.format - Output format: 'plantuml' (default: 'plantuml')
 * @param {Object} options.plantUMLConfig - PlantUML-specific configuration
 * @returns {Promise<string>} Diagram syntax string
 */
export const buildDiagram = async (schema, diagramType = 'class', languageVisibility = {}, options = {}) => {
  // Validate schema first
  const validation = validateSchema(schema);
  if (!validation.isValid) {
    const error = validation.error;
    error.correlationId = options.correlationId;
    throw error;
  }

  const type = diagramType.toLowerCase();
  // Always use PlantUML for all diagram types
  return await buildPlantUMLDiagram(schema, type, languageVisibility, options);
};

/**
 * Build PlantUML diagram via backend API
 * @param {Object} schema - Analysis schema
 * @param {string} diagramType - Type of diagram
 * @param {Object} languageVisibility - Language filter settings
 * @param {Object} options - Additional options
 * @returns {Promise<string>} PlantUML syntax string
 */
export const buildPlantUMLDiagram = async (schema, diagramType, languageVisibility = {}, options = {}) => {
  try {
    // Get enabled languages from languageVisibility
    const languageFilter = Object.keys(languageVisibility || {})
      .filter(lang => languageVisibility[lang] !== false);

    // Prepare request payload
    const payload = {
      schema,
      diagram_type: diagramType,
      language_filter: languageFilter.length > 0 ? languageFilter : undefined,
      config: options.plantUMLConfig || {}
    };

    // Call backend API
    const apiUrl = (() => {
      const directUrl = process.env.NEXT_PUBLIC_API_URL;
      if (typeof directUrl === 'string' && directUrl.trim().length > 0) {
        return directUrl.replace(/\/$/, '');
      }

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      if (typeof backendUrl === 'string' && backendUrl.trim().length > 0) {
        return `${backendUrl.replace(/\/$/, '')}/api`;
      }

      return '/api';
    })();

    const response = await fetch(`${apiUrl}/generate-plantuml`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': options.correlationId || 'unknown'
      },
      body: JSON.stringify(payload)
    });

    let data;
    const rawBody = await response.text();
    try {
      data = rawBody ? JSON.parse(rawBody) : {};
    } catch (parseError) {
      data = { error: rawBody, parseError: parseError instanceof Error ? parseError.message : 'unknown' };
    }

    if (!response.ok) {
      const errorMessage = extractErrorMessage(data, `API error: ${response.status}`);
  throw new Error(errorMessage);
    }

    if (data && data.success === false) {
      const errorMessage = extractErrorMessage(data.error, 'PlantUML generation failed');
  throw new Error(errorMessage);
    }

    if (!data?.plantuml) {
  throw new Error('No PlantUML syntax returned from API');
    }

    logger.info('PlantUML diagram generated', {
      diagramType,
      statistics: data.statistics,
      correlationId: options.correlationId
    });

    return data.plantuml;

  } catch (error) {
    throw error;
  }
};

/**
 * Validates schema before diagram building
 */
export const validateSchema = (schema) => {
  if (!schema || typeof schema !== 'object') {
  return { isValid: false, error: new Error('Schema is required and must be an object') };
  }

  // Check for schema wrapper (backend response format)
  const schemaData = schema.schema || schema;

  // Inject default meta if missing or invalid
  if (!schemaData.meta || typeof schemaData.meta !== 'object') {
    schemaData.meta = {
      classes_found: 0,
      files_scanned: 0,
      languages: [],
      system: 'UnknownSystem'
    };
  }

  const meta = schemaData.meta;

  // Validate meta structure
  if (typeof meta.classes_found !== 'number' || meta.classes_found < 0) {
  return { isValid: false, error: new Error('meta.classes_found must be a non-negative number') };
  }
  if (typeof meta.files_scanned !== 'number' || meta.files_scanned < 0) {
  return { isValid: false, error: new Error('meta.files_scanned must be a non-negative number') };
  }
  if (!Array.isArray(meta.languages)) {
  return { isValid: false, error: new Error('meta.languages must be an array') };
  } else {
    // Check that languages are valid strings
    for (const lang of meta.languages) {
      if (typeof lang !== 'string' || lang.trim().length === 0) {
  return { isValid: false, error: new Error('meta.languages must contain non-empty strings') };
      }
    }
  }

  // Validate language arrays (should be arrays if present)
  const expectedLanguages = ['python', 'java', 'javascript', 'typescript', 'csharp', 'cpp', 'c', 'css', 'html', 'php', 'ruby', 'go', 'rust'];
  for (const lang of expectedLanguages) {
    if (schemaData[lang] !== undefined && !Array.isArray(schemaData[lang])) {
  return { isValid: false, error: new Error(`schema.${lang} must be an array if present`) };
    }
  }

  // Validate relations array
  if (!Array.isArray(schemaData.relations)) {
  return { isValid: false, error: new Error('schema.relations must be an array') };
  }

  // Validate endpoints array
  if (!Array.isArray(schemaData.endpoints)) {
  return { isValid: false, error: new Error('schema.endpoints must be an array') };
  }

  // Validate patterns array
  if (!Array.isArray(schemaData.patterns)) {
  return { isValid: false, error: new Error('schema.patterns must be an array') };
  }

  // Validate layers array
  if (!Array.isArray(schemaData.layers)) {
  return { isValid: false, error: new Error('schema.layers must be an array') };
  }

  // Check for at least one supported language or relations/endpoints
  const hasClasses = expectedLanguages.some(lang =>
    Array.isArray(schemaData[lang]) && schemaData[lang].length > 0
  );

  const hasRelations = Array.isArray(schemaData.relations) && schemaData.relations.length > 0;
  const hasEndpoints = Array.isArray(schemaData.endpoints) && schemaData.endpoints.length > 0;

  if (!hasClasses && !hasRelations && !hasEndpoints) {
    return {
      isValid: false,
      error: new Error('Schema must contain at least classes, relations, or endpoints')
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