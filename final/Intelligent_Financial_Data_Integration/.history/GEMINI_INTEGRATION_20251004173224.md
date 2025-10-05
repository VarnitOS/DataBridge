# Gemini AI Chatbot Integration

This document describes the integration of Google's Gemini AI into the Financial Data Integration platform using the Model Context Protocol (MCP) server architecture.

## Architecture Overview

```
Frontend (React) → Backend API (Node.js) → MCP Server (Python) → Gemini API
```

## Components

### 1. MCP Server (`scripts/hello_mcp.py`)
- Python-based MCP server that communicates with Gemini API
- Handles chatbot queries and generates intelligent responses
- Implements safety settings and content filtering
- Supports context-aware conversations

### 2. Backend API (`server/index.js`)
- Express.js server that acts as a bridge between frontend and MCP server
- Handles HTTP requests from the frontend
- Manages MCP server processes
- Provides health checks and error handling

### 3. Frontend Integration (`src/components/AIChatbotPanel.tsx`)
- Updated React component with Gemini API integration
- Real-time chat interface with loading states
- Error handling and user feedback
- Context-aware conversations

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API key from Google AI Studio

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the example file
cp env.example .env

# Edit the .env file with your actual API key
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 2. Python Dependencies

```bash
# Navigate to scripts directory
cd scripts

# Run the setup script
./setup.sh

# Or install manually
pip3 install -r requirements.txt
```

### 3. Node.js Dependencies

```bash
# Navigate to server directory
cd server

# Install dependencies
npm install
```

### 4. Running the System

#### Option 1: Development Mode (Recommended)

```bash
# Terminal 1: Start the backend server
cd server
npm run dev

# Terminal 2: Start the frontend
cd ../
npm run dev
```

#### Option 2: Production Mode

```bash
# Terminal 1: Start the backend server
cd server
npm start

# Terminal 2: Start the frontend
cd ../
npm run build
npm run preview
```

## API Endpoints

### Backend API Endpoints

- `GET /api/health` - Server health check
- `POST /api/chatbot` - Send message to Gemini AI
- `GET /api/chatbot/health` - MCP server health check

### Request Format

```json
{
  "message": "How do I resolve data conflicts?",
  "context": {
    "currentStep": "conflicts",
    "mappings": [...],
    "conflicts": [...]
  },
  "history": [
    {
      "role": "user",
      "content": "Previous message"
    },
    {
      "role": "assistant", 
      "content": "Previous response"
    }
  ]
}
```

### Response Format

```json
{
  "response": "AI-generated response text",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "model": "gemini-pro",
  "context": {...}
}
```

## Features

### 1. Context-Aware Conversations
- Maintains conversation history
- Includes current application context
- Provides relevant responses based on user's workflow

### 2. Safety and Content Filtering
- Implements Google's safety settings
- Filters harmful content
- Maintains professional tone for business use

### 3. Error Handling
- Graceful degradation on API failures
- User-friendly error messages
- Automatic retry mechanisms

### 4. Loading States
- Visual feedback during API calls
- Prevents duplicate requests
- Clear status indicators

## Configuration

### MCP Server Configuration

The MCP server follows the Kubernetes-style configuration:

```yaml
apiVersion: kagent.dev/v1alpha1
kind: MCPServer
metadata:
  name: hello-mcp
  namespace: kagent
spec:
  transportType: stdio
  stdioTransport: {}
  deployment:
    image: python:3.11-slim
    args:
      - python3
      - /scripts/hello_mcp.py
    volumeMounts:
      - name: script-vol
        mountPath: /scripts
    volumes:
      - name: script-vol
        configMap:
          name: hello-mcp-script
```

## Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```
   Error: GEMINI_API_KEY environment variable is required
   ```
   Solution: Set the GEMINI_API_KEY environment variable

2. **Python Dependencies Missing**
   ```
   ModuleNotFoundError: No module named 'google.generativeai'
   ```
   Solution: Run `pip3 install -r scripts/requirements.txt`

3. **Backend Server Not Starting**
   ```
   Error: Cannot find module 'express'
   ```
   Solution: Run `npm install` in the server directory

4. **Frontend API Connection Failed**
   ```
   API request failed: 500 Internal Server Error
   ```
   Solution: Check if backend server is running and MCP server is accessible

### Debug Mode

Enable debug logging by setting:
```bash
export DEBUG=true
export LOG_LEVEL=debug
```

## Security Considerations

1. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables or secure secret management
   - Rotate keys regularly

2. **Content Filtering**
   - Gemini API includes built-in safety filters
   - Additional content validation on the backend
   - User input sanitization

3. **Rate Limiting**
   - Implement rate limiting for API calls
   - Monitor usage to prevent abuse
   - Set appropriate timeouts

## Performance Optimization

1. **Caching**
   - Cache frequent responses
   - Implement conversation context caching
   - Use Redis for session storage

2. **Connection Pooling**
   - Reuse MCP server processes
   - Implement connection pooling
   - Monitor resource usage

3. **Response Streaming**
   - Implement streaming responses for long answers
   - Progressive loading of content
   - Better user experience

## Monitoring and Logging

### Health Checks
- Backend server health: `GET /api/health`
- MCP server health: `GET /api/chatbot/health`
- Gemini API connectivity: Automatic testing

### Logging
- Request/response logging
- Error tracking and reporting
- Performance metrics collection

## Future Enhancements

1. **Multi-Model Support**
   - Support for different AI models
   - Model selection based on query type
   - A/B testing capabilities

2. **Advanced Context**
   - File upload and analysis
   - Schema-aware responses
   - Integration with data sources

3. **User Personalization**
   - User-specific conversation history
   - Custom response preferences
   - Learning from user interactions
