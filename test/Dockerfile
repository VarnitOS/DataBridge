# Dockerfile
FROM python:3.11-slim

# Install MCP SDK
RUN pip install mcp

# Copy your script into the image
COPY hello_mcp.py /app/hello_mcp.py

WORKDIR /app

CMD ["python3", "hello_mcp.py"]

