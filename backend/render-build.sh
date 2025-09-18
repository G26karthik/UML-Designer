#!/bin/bash

# Render.com Build Script for UML Backend
# This script runs during the build phase on Render

echo "🚀 Starting UML Backend build process..."

# Install dependencies
echo "📦 Installing dependencies..."
npm ci --only=production

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p logs
mkdir -p cache
mkdir -p uploads

# Set appropriate permissions
echo "🔒 Setting directory permissions..."
chmod 755 logs cache uploads

# Verify installation
echo "✅ Verifying installation..."
node --version
npm --version

# Run tests to ensure everything is working
echo "🧪 Running tests..."
npm test

echo "✅ Build completed successfully!"
echo "🎯 Ready for deployment on Render!"