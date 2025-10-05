#!/usr/bin/env python3
"""
Agent Visualization Server
Serves the real-time agent communication visualization UI
"""
import asyncio
import logging
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.websocket_server import connection_manager
from core.agent_registry import agent_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EY Data Integration - Agent Visualization")


@app.get("/")
async def get_visualization():
    """Serve the agent visualization page"""
    html_path = Path(__file__).parent / "visualization.html"
    if html_path.exists():
        return FileResponse(html_path)
    else:
        return HTMLResponse("<h1>visualization.html not found</h1>")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Handle client messages if needed
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "get_agents":
                # Send current agent registry status
                status = agent_registry.get_registry_status()
                await websocket.send_text(json.dumps({
                    "type": "agent_registry",
                    "data": status
                }))
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


@app.get("/api/agents")
async def get_agents():
    """Get current agent registry status"""
    return agent_registry.get_registry_status()


if __name__ == "__main__":
    logger.info("🚀 Starting Agent Visualization Server...")
    logger.info("📊 Open http://localhost:8001 to view the visualization")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
