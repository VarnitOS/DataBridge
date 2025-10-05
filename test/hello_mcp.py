#!/usr/bin/env python3
# hello_mcp.py
from mcp.server.fastmcp import FastMCP

# Create the server
mcp = FastMCP("hello-mcp")

# Register a tool
@mcp.tool()
def hello() -> str:
    """Return a Hello World message"""
    return "Hello World"

if __name__ == "__main__":
    mcp.run()
