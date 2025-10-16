#!/usr/bin/env node

/**
 * Cross-platform directory preparation for backend runtime assets.
 * Ensures logs/, cache/, and uploads/ exist before the server starts.
 */

import fs from 'fs';
import path from 'path';

const REQUIRED_DIRECTORIES = ['logs', 'cache', 'uploads'];

for (const dir of REQUIRED_DIRECTORIES) {
  const resolved = path.resolve(dir);
  try {
    if (!fs.existsSync(resolved)) {
      fs.mkdirSync(resolved, { recursive: true });
      console.log(`Created directory: ${resolved}`);
    }
  } catch (error) {
    console.error(`Failed to ensure directory ${resolved}:`, error);
    process.exitCode = 1;
  }
}
