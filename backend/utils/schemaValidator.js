/**
 * Schema validation utilities for UML Designer API responses
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Validates if a response object matches the expected UML schema structure
 * @param {Object} data - The response data to validate
 * @returns {Object} - { isValid: boolean, errors: string[] }
 */
export function validateUmlSchema(data) {
  const errors = [];

  // Must be an object
  if (!data || typeof data !== 'object') {
    errors.push('Response must be an object');
    return { isValid: false, errors };
  }

  // Must have schema property
  if (!data.schema || typeof data.schema !== 'object') {
    errors.push('Response must have a "schema" object property');
    return { isValid: false, errors };
  }

  const schema = data.schema;

  // Schema must have meta property
  if (!schema.meta || typeof schema.meta !== 'object') {
    errors.push('Schema must have a "meta" object property');
    return { isValid: false, errors };
  }

  // Validate meta structure
  const meta = schema.meta;
  if (typeof meta.classes_found !== 'number' || meta.classes_found < 0) {
    errors.push('meta.classes_found must be a non-negative number');
  }
  if (typeof meta.files_scanned !== 'number' || meta.files_scanned < 0) {
    errors.push('meta.files_scanned must be a non-negative number');
  }
  if (!Array.isArray(meta.languages)) {
    errors.push('meta.languages must be an array');
  } else {
    // Check that languages are valid strings
    for (const lang of meta.languages) {
      if (typeof lang !== 'string' || lang.trim().length === 0) {
        errors.push('meta.languages must contain non-empty strings');
        break;
      }
    }
  }

  // Validate language arrays (should be arrays if present)
  const expectedLanguages = ['python', 'java', 'javascript', 'typescript', 'csharp', 'cpp', 'c', 'css', 'html', 'php', 'ruby', 'go', 'rust'];
  for (const lang of expectedLanguages) {
    if (schema[lang] !== undefined && !Array.isArray(schema[lang])) {
      errors.push(`schema.${lang} must be an array if present`);
    }
  }

  // Validate relations array
  if (!Array.isArray(schema.relations)) {
    errors.push('schema.relations must be an array');
  }

  // Validate endpoints array
  if (!Array.isArray(schema.endpoints)) {
    errors.push('schema.endpoints must be an array');
  }

  // Validate patterns array
  if (!Array.isArray(schema.patterns)) {
    errors.push('schema.patterns must be an array');
  }

  // Validate layers array
  if (!Array.isArray(schema.layers)) {
    errors.push('schema.layers must be an array');
  }

  // If there are any validation errors, return them
  if (errors.length > 0) {
    return { isValid: false, errors };
  }

  return { isValid: true, errors: [] };
}

/**
 * Loads the expected schema from the schema file for reference
 * @returns {Promise<Object>} The expected schema structure
 */
export async function loadExpectedSchema() {
  try {
    const schemaPath = path.join(__dirname, '..', '..', 'backend_last_schema.json');
    const schemaContent = await fs.readFile(schemaPath, 'utf8');
    return JSON.parse(schemaContent);
  } catch (error) {
    console.warn('Could not load expected schema file:', error.message);
    return null;
  }
}