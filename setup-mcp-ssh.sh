#!/bin/bash

# Setup script for MCP SSH server
echo "Setting up MCP SSH server..."

# Check if mcp-server-ssh directory exists
if [ ! -d "mcp-server-ssh" ]; then
    echo "Cloning MCP SSH server repository..."
    git clone https://github.com/shaike1/mcp-server-ssh.git
fi

# Install dependencies and build
echo "Installing dependencies..."
cd mcp-server-ssh
npm install

echo "MCP SSH server setup complete!"
echo "The server is now configured in .claude_mcp_config.json"
echo ""
echo "To use with Claude Code:"
echo "1. Make sure your SSH config is set up at ~/.ssh/config"
echo "2. Start Claude Code with: claude-code --mcp-config .claude_mcp_config.json"