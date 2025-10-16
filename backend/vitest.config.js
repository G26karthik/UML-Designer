import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
  },
  optimizeDeps: {
    include: ['pino', 'express-pino-logger']
  }
})