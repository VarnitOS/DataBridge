const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    gemini_configured: !!process.env.GEMINI_API_KEY
  });
});

// Chatbot endpoint with direct Gemini API integration
app.post('/api/chatbot', async (req, res) => {
  try {
    const { message, context = {}, history = [] } = req.body;

    if (!message) {
      return res.status(400).json({ 
        error: 'Message is required' 
      });
    }

    if (!process.env.GEMINI_API_KEY) {
      return res.status(500).json({ 
        error: 'Gemini API key not configured' 
      });
    }

    // Build context-aware prompt
    const prompt = buildContextualPrompt(message, context, history);

    // Call Gemini API directly
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${process.env.GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: prompt
          }]
        }],
        generationConfig: {
          temperature: 0.7,
          topP: 0.8,
          topK: 40,
          maxOutputTokens: 1024,
        },
        safetySettings: [
          {
            category: "HARM_CATEGORY_HARASSMENT",
            threshold: "BLOCK_MEDIUM_AND_ABOVE"
          },
          {
            category: "HARM_CATEGORY_HATE_SPEECH", 
            threshold: "BLOCK_MEDIUM_AND_ABOVE"
          },
          {
            category: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold: "BLOCK_MEDIUM_AND_ABOVE"
          },
          {
            category: "HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold: "BLOCK_MEDIUM_AND_ABOVE"
          }
        ]
      })
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Gemini API error: ${response.status} ${errorData}`);
    }

    const data = await response.json();
    
    if (data.candidates && data.candidates[0] && data.candidates[0].content) {
      const aiResponse = data.candidates[0].content.parts[0].text;
      
      res.json({
        response: aiResponse,
        timestamp: new Date().toISOString(),
        model: 'gemini-1.5-flash',
        context: context
      });
    } else {
      throw new Error('Invalid response from Gemini API');
    }

  } catch (error) {
    console.error('Chatbot API error:', error);
    res.status(500).json({ 
      error: 'Failed to generate response',
      details: error.message 
    });
  }
});

function buildContextualPrompt(message, context, history) {
  const promptParts = [
    "You are an intelligent AI assistant for a Financial Data Integration platform.",
    "You help users with data integration, mapping, analysis, and technical questions.",
    "Provide helpful, accurate, and professional responses.",
    ""
  ];
  
  // Add context information
  if (context && Object.keys(context).length > 0) {
    promptParts.push("Current context:");
    for (const [key, value] of Object.entries(context)) {
      if (value !== null && value !== undefined) {
        promptParts.push(`- ${key}: ${JSON.stringify(value)}`);
      }
    }
    promptParts.push("");
  }
  
  // Add conversation history
  if (history && history.length > 0) {
    promptParts.push("Recent conversation:");
    for (const entry of history.slice(-5)) { // Last 5 exchanges
      const role = entry.role || 'user';
      const content = entry.content || '';
      promptParts.push(`${role}: ${content}`);
    }
    promptParts.push("");
  }
  
  // Add current message
  promptParts.push(`User: ${message}`);
  promptParts.push("Assistant:");
  
  return promptParts.join("\n");
}

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`🔑 Gemini API Key configured: ${process.env.GEMINI_API_KEY ? 'Yes' : 'No'}`);
  console.log(`🌐 API Base URL: http://localhost:${PORT}`);
});
