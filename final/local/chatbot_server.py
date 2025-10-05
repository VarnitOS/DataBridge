#!/usr/bin/env python3
"""
EY Data Integration - Conversational AI Interface
Beautiful web UI + Gemini-powered chatbot + Multi-agent orchestration
"""
import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.models import ChatRequest, ChatResponse
from agents.orchestration.conversational_agent import ConversationalAgent
from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
from agents.gemini.mapping_agent import GeminiMappingAgent
from agents.merge.join_agent import JoinAgent
from agents.quality.validation_monitor_agent import ValidationMonitorAgent
from agents.quality.stats_agent import StatsAgent
from core.event_bus import event_bus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EY Data Integration AI Assistant")

# Initialize all agents on startup
system_agents = {}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active agents by session
active_agents = {}

@app.on_event("startup")
async def startup_agents():
    """Initialize all system agents on startup"""
    logger.info("🚀 Initializing system agents...")
    
    # Initialize core agents
    system_agents['validation_monitor'] = ValidationMonitorAgent(agent_id="system_monitor")
    system_agents['ingestion'] = SnowflakeIngestionAgent(agent_id="system_ingestion")
    system_agents['schema_reader'] = GeminiSchemaReaderAgent(agent_id="system_schema")
    system_agents['mapping'] = GeminiMappingAgent(agent_id="system_mapping")
    system_agents['join'] = JoinAgent(agent_id="system_join")
    system_agents['stats'] = StatsAgent(agent_id="system_stats")
    
    logger.info(f"✅ Initialized {len(system_agents)} system agents")
    logger.info("🎯 All agents registered and ready for orchestration")

@app.on_event("shutdown")
async def shutdown_agents():
    """Cleanup on shutdown"""
    logger.info("🛑 System agents shut down")

@app.get("/", response_class=HTMLResponse)
async def get_chat_ui():
    """Serve the beautiful chat UI"""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EY Data Integration AI Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh; display: flex; justify-content: center; align-items: center;
        }
        .chat-container {
            width: 90%; max-width: 900px; height: 85vh; background: white;
            border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex; flex-direction: column; overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 25px; text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .chat-header h1 { font-size: 24px; margin-bottom: 5px; }
        .chat-header p { font-size: 14px; opacity: 0.9; }
        .status-indicator {
            display: inline-block; width: 10px; height: 10px; border-radius: 50%;
            background: #4ade80; margin-right: 8px; animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .chat-messages {
            flex: 1; overflow-y: auto; padding: 20px; background: #f8f9fa;
        }
        .message { margin-bottom: 20px; animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .message.user { text-align: right; }
        .message-content {
            display: inline-block; max-width: 70%; padding: 15px 20px;
            border-radius: 18px; word-wrap: break-word;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border-bottom-right-radius: 5px;
        }
        .message.assistant .message-content {
            background: white; color: #333; border: 1px solid #e5e7eb;
            border-bottom-left-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .message-meta { font-size: 12px; color: #6b7280; margin-top: 5px; }
        .typing-indicator { display: none; padding: 15px; margin-bottom: 20px; }
        .typing-indicator.active { display: block; }
        .typing-indicator span {
            display: inline-block; width: 8px; height: 8px; border-radius: 50%;
            background: #667eea; margin: 0 2px; animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        .chat-input-container { padding: 20px; background: white; border-top: 1px solid #e5e7eb; }
        .chat-input-wrapper { display: flex; gap: 10px; }
        #messageInput {
            flex: 1; padding: 15px 20px; border: 2px solid #e5e7eb;
            border-radius: 25px; font-size: 15px; outline: none;
            transition: border-color 0.3s;
        }
        #messageInput:focus { border-color: #667eea; }
        #sendButton {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 25px;
            font-size: 15px; font-weight: 600; cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        #sendButton:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        #sendButton:active { transform: translateY(0); }
        #sendButton:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .quick-actions { display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
        .quick-action-btn {
            padding: 8px 15px; background: #f3f4f6; border: 1px solid #d1d5db;
            border-radius: 15px; font-size: 13px; cursor: pointer;
            transition: all 0.2s;
        }
        .quick-action-btn:hover { background: #e5e7eb; border-color: #9ca3af; }
        .chat-messages::-webkit-scrollbar { width: 8px; }
        .chat-messages::-webkit-scrollbar-track { background: #f1f1f1; }
        .chat-messages::-webkit-scrollbar-thumb { background: #667eea; border-radius: 4px; }
        .chat-messages::-webkit-scrollbar-thumb:hover { background: #764ba2; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🤖 EY Data Integration AI Assistant</h1>
            <p><span class="status-indicator"></span>Connected to Multi-Agent System</p>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="message assistant">
                <div class="message-content">
                    👋 Hi! I'm your AI assistant for data integration. I can help you:
                    <br><br>
                    • Upload and merge datasets from multiple sources
                    <br>• Analyze schemas and propose intelligent mappings
                    <br>• Execute complex data transformations
                    <br>• Validate data quality in real-time
                    <br><br>
                    What would you like to do today?
                </div>
                <div class="message-meta">Assistant • Now</div>
            </div>
        </div>
        <div class="typing-indicator" id="typingIndicator">
            <span></span><span></span><span></span>
        </div>
        <div class="chat-input-container">
            <div class="quick-actions">
                <button class="quick-action-btn" onclick="sendQuickMessage('Show me what tables are available in Snowflake')">📊 Available Data</button>
                <button class="quick-action-btn" onclick="sendQuickMessage('Merge UNIFIED_ACCOUNTS and UNIFIED_TRANSACTIONS')">🔗 Join Tables</button>
                <button class="quick-action-btn" onclick="sendQuickMessage('Validate data quality in UNIFIED_ACCOUNTS')">✅ Quality Check</button>
                <button class="quick-action-btn" onclick="sendQuickMessage('What can you do?')">❓ Capabilities</button>
            </div>
            <div class="chat-input-wrapper">
                <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
                <button id="sendButton" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>
    <script>
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');
        
        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = content.replace(/\\n/g, '<br>');
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';
            metaDiv.textContent = `${isUser ? 'You' : 'Assistant'} • ${new Date().toLocaleTimeString()}`;
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(metaDiv);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function showTypingIndicator() {
            typingIndicator.classList.add('active');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function hideTypingIndicator() {
            typingIndicator.classList.remove('active');
        }
        
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            addMessage(message, true);
            messageInput.value = '';
            sendButton.disabled = true;
            messageInput.disabled = true;
            
            // Create LIVE progress message (shows agent communication in real-time!)
            const progressDiv = document.createElement('div');
            progressDiv.className = 'message assistant';
            progressDiv.innerHTML = '<div class="message-content" id="live-progress" style="font-family: monospace; font-size: 13px; max-width: 85%;"><div class="typing-indicator active" style="display:block"><span></span><span></span><span></span></div><div id="progress-text"></div></div>';
            chatMessages.appendChild(progressDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            const progressText = document.getElementById('progress-text');
            
            try {
                const response = await fetch('/chat/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        session_id: 'demo_session_' + Date.now()
                    })
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const {value, done} = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\\n\\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.substring(6));
                            
                            if (data.type === 'step_start') {
                                progressText.innerHTML += `<br><strong>🔹 Step ${data.step}/${data.total_steps}:</strong> ${data.description}<br><small style="color: #666;">⏱️  ${data.time} | 🎯 ${data.capability}</small><br>`;
                            } else if (data.type === 'agent_call') {
                                progressText.innerHTML += `<small style="color: #888;">   📞 Calling agent...</small><br>`;
                            } else if (data.type === 'info') {
                                progressText.innerHTML += `<small style="color: #555;">   ${data.message}</small><br>`;
                            } else if (data.type === 'step_complete') {
                                progressText.innerHTML += `<small style="color: #22c55e;">   ✅ Done in ${data.duration} by <strong>${data.agent}</strong></small><br>`;
                                if (data.details) {
                                    progressText.innerHTML += `<small style="color: #22c55e;">   ${data.details}</small><br>`;
                                }
                            } else if (data.type === 'step_error') {
                                progressText.innerHTML += `<small style="color: #ef4444;">   ❌ Failed in ${data.duration}: ${data.error}</small><br>`;
                            } else if (data.type === 'complete') {
                                // Remove typing indicator
                                const typingInd = document.querySelector('#live-progress .typing-indicator');
                                if (typingInd) typingInd.remove();
                                // Add final response
                                progressText.innerHTML += `<br><hr style="border-color: #ddd;"><br><div style="font-family: 'Segoe UI', sans-serif; font-size: 14px;">${data.response.replace(/\\n/g, '<br>')}</div>`;
                            } else if (data.type === 'error') {
                                const typingInd = document.querySelector('#live-progress .typing-indicator');
                                if (typingInd) typingInd.remove();
                                progressText.innerHTML += `<br><strong style="color: #ef4444;">❌ Error:</strong> ${data.error}`;
                            }
                            
                            // Auto-scroll to show latest updates
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }
                    }
                }
                
            } catch (error) {
                const typingInd = document.querySelector('#live-progress .typing-indicator');
                if (typingInd) typingInd.remove();
                if (progressText) progressText.innerHTML += `<br><strong style="color: #ef4444;">❌ Connection error:</strong> ${error.message}`;
            }
            
            sendButton.disabled = false;
            messageInput.disabled = false;
            messageInput.focus();
        }
        
        function sendQuickMessage(message) {
            messageInput.value = message;
            sendMessage();
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') sendMessage();
        }
        
        messageInput.focus();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for the conversational AI (non-streaming)"""
    try:
        session_id = request.session_id or "default"
        
        # Get or create agent for this session
        if session_id not in active_agents:
            active_agents[session_id] = ConversationalAgent(agent_id=f"assistant_{session_id}")
        
        agent = active_agents[session_id]
        
        # Chat
        response = await agent.chat(
            user_message=request.message,
            context={"session_id": session_id}
        )
        
        confidence = 95 if response.get("success") else 50
        reasoning = None
        if response.get("actions_taken"):
            actions = [a.get("description", "") for a in response["actions_taken"]]
            reasoning = f"Executed {len(actions)} actions: {', '.join(actions)}"
        
        return ChatResponse(
            answer=response.get("message", "I'm not sure about that."),
            confidence=confidence,
            reasoning=reasoning
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return ChatResponse(
            answer=f"Error: {str(e)}",
            confidence=0,
            reasoning=f"Exception: {type(e).__name__}"
        )

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    STREAMING chat endpoint - sends real-time progress updates as agents work
    Uses Server-Sent Events (SSE) for live updates
    """
    import asyncio
    from fastapi.responses import StreamingResponse
    import json
    
    async def event_generator():
        try:
            session_id = request.session_id or f"stream_{int(time.time()*1000)}"
            
            # Get or create agent for this session
            if session_id not in active_agents:
                active_agents[session_id] = ConversationalAgent(agent_id=f"assistant_{session_id}")
            
            agent = active_agents[session_id]
            
            # Queue for progress updates
            progress_queue = asyncio.Queue()
            
            # Progress callback that feeds the queue
            async def progress_callback(data):
                await progress_queue.put(data)
            
            # Set the callback on the agent
            agent.progress_callback = progress_callback
            
            # Start the chat task
            async def run_chat():
                try:
                    response = await agent.chat(
                        user_message=request.message,
                        context={"session_id": session_id}
                    )
                    # Signal completion
                    await progress_queue.put({"type": "complete", "response": response.get("message", "")})
                except Exception as e:
                    await progress_queue.put({"type": "error", "error": str(e)})
            
            # Start chat in background
            chat_task = asyncio.create_task(run_chat())
            
            # Stream progress updates
            while True:
                try:
                    # Wait for next progress update (with timeout)
                    progress = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                    
                    # Send progress as SSE event
                    yield f"data: {json.dumps(progress)}\n\n"
                    
                    # If complete or error, break
                    if progress.get("type") in ["complete", "error"]:
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
                    # Check if chat task is done
                    if chat_task.done():
                        break
            
            # Clean up
            agent.progress_callback = None
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    print("="*80)
    print("🤖 EY DATA INTEGRATION AI ASSISTANT")
    print("="*80)
    print("\n✨ Starting chatbot server...")
    print("\n📺 Open your browser to: http://localhost:8002")
    print("\n🎯 Features:")
    print("   • Natural language conversation")
    print("   • Multi-agent orchestration")
    print("   • Real-time data operations")
    print("   • Beautiful UI interface")
    print("\n" + "="*80)
    
    uvicorn.run(app, host="0.0.0.0", port=8002)
