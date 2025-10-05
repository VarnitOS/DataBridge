const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Store active MCP processes
const mcpProcesses = new Map();

/**
 * Start MCP server process
 */
function startMCPServer() {
  const scriptPath = path.join(__dirname, '../scripts/hello_mcp.py');
  
  const mcpProcess = spawn('python3', [scriptPath], {
    env: {
      ...process.env,
      GEMINI_API_KEY: process.env.GEMINI_API_KEY
    },
    stdio: ['pipe', 'pipe', 'pipe']
  });

  mcpProcess.on('error', (error) => {
    console.error('MCP Server error:', error);
  });

  mcpProcess.on('exit', (code) => {
    console.log(`MCP Server exited with code ${code}`);
  });

  return mcpProcess;
}

/**
 * Send request to MCP server
 */
function sendToMCPServer(process, request) {
  return new Promise((resolve, reject) => {
    let responseData = '';
    let errorData = '';

    const timeout = setTimeout(() => {
      reject(new Error('MCP Server timeout'));
    }, 30000); // 30 second timeout

    const onData = (data) => {
      responseData += data.toString();
      try {
        const response = JSON.parse(responseData);
        clearTimeout(timeout);
        process.stdout.removeListener('data', onData);
        process.stderr.removeListener('data', onError);
        resolve(response);
      } catch (e) {
        // Continue collecting data
      }
    };

    const onError = (data) => {
      errorData += data.toString();
    };

    process.stdout.on('data', onData);
    process.stderr.on('data', onError);

    // Send request to MCP server
    process.stdin.write(JSON.stringify(request) + '\n');
  });
}

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    mcp_servers: mcpProcesses.size
  });
});

// Chatbot endpoint
app.post('/api/chatbot', async (req, res) => {
  try {
    const { message, context = {}, history = [] } = req.body;

    if (!message) {
      return res.status(400).json({ 
        error: 'Message is required' 
      });
    }

    // Get or create MCP server process
    let mcpProcess = mcpProcesses.get('main');
    if (!mcpProcess || mcpProcess.killed) {
      mcpProcess = startMCPServer();
      mcpProcesses.set('main', mcpProcess);
    }

    // Prepare request for MCP server
    const mcpRequest = {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'chatbot/query',
      params: {
        message,
        context,
        history
      }
    };

    // Send to MCP server and get response
    const response = await sendToMCPServer(mcpProcess, mcpRequest);

    if (response.error) {
      return res.status(500).json({ 
        error: response.error.message 
      });
    }

    res.json(response.result);

  } catch (error) {
    console.error('Chatbot API error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      details: error.message 
    });
  }
});

// Health check for MCP server
app.get('/api/chatbot/health', async (req, res) => {
  try {
    let mcpProcess = mcpProcesses.get('main');
    if (!mcpProcess || mcpProcess.killed) {
      mcpProcess = startMCPServer();
      mcpProcesses.set('main', mcpProcess);
    }

    const mcpRequest = {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'chatbot/health',
      params: {}
    };

    const response = await sendToMCPServer(mcpProcess, mcpRequest);
    res.json(response);

  } catch (error) {
    console.error('MCP Health check error:', error);
    res.status(500).json({ 
      error: 'MCP Server health check failed',
      details: error.message 
    });
  }
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down server...');
  mcpProcesses.forEach((process, key) => {
    if (!process.killed) {
      process.kill();
    }
  });
  process.exit(0);
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Gemini API Key configured: ${process.env.GEMINI_API_KEY ? 'Yes' : 'No'}`);
});


