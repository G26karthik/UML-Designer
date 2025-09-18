#!/bin/bash

# Render.com Start Script for UML Backend
# This script runs when starting the service on Render

echo "🚀 Starting UML Backend service..."

# Set production environment
export NODE_ENV=production

# Create directories if they don't exist
mkdir -p logs cache uploads

# Set default port if not provided by Render
export PORT=${PORT:-10000}

echo "🌐 Server will start on port: $PORT"
echo "🔧 Environment: $NODE_ENV"

# Start the application with PM2 in production mode
if [ "$NODE_ENV" = "production" ]; then
    echo "🏭 Starting with PM2 in production mode..."
    npx pm2-runtime start ecosystem.config.json --env production
else
    echo "🔨 Starting in development mode..."
    node server.js
fi