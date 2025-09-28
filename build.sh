#!/bin/bash
echo "Building VRP Backend for Netlify..."

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p functions

echo "Build completed successfully!"

