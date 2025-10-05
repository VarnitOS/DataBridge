#!/bin/bash

# Setup script for Gemini MCP Server
echo "Setting up Gemini MCP Server..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Make the MCP script executable
chmod +x hello_mcp.py

echo "Setup complete!"
echo ""
echo "To run the MCP server:"
echo "1. Set your GEMINI_API_KEY environment variable"
echo "2. Run: python3 hello_mcp.py"
echo ""
echo "To run the backend server:"
echo "1. Navigate to the server directory: cd ../server"
echo "2. Install Node.js dependencies: npm install"
echo "3. Set your GEMINI_API_KEY environment variable"
echo "4. Run: npm start"
