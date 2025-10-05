"""
WebSocket support for real-time updates
"""
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, List
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a client to a session"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        
        self.active_connections[session_id].append(websocket)
        logger.info(f"Client connected to session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Disconnect a client"""
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            logger.info(f"Client disconnected from session {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Send message to all clients connected to a session"""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
    
    async def broadcast_agent_log(
        self, 
        session_id: str, 
        agent_type: str, 
        agent_id: str, 
        message: str
    ):
        """Broadcast agent log to clients"""
        await self.send_message(session_id, {
            "type": "agent_log",
            "data": {
                "agent": f"{agent_type}_{agent_id}",
                "message": message,
                "timestamp": asyncio.get_event_loop().time()
            }
        })
    
    async def broadcast_status_update(
        self, 
        session_id: str, 
        progress: int, 
        current_step: str
    ):
        """Broadcast status update to clients"""
        await self.send_message(session_id, {
            "type": "status_update",
            "data": {
                "progress": progress,
                "current_step": current_step
            }
        })
    
    async def broadcast_completion(self, session_id: str, result: dict):
        """Broadcast completion message"""
        await self.send_message(session_id, {
            "type": "complete",
            "data": result
        })
    
    async def broadcast_error(self, session_id: str, error: str):
        """Broadcast error message"""
        await self.send_message(session_id, {
            "type": "error",
            "data": {
                "error": error
            }
        })


# Global connection manager
connection_manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time updates
    
    Clients connect to receive live updates about merge progress,
    agent logs, and status changes
    """
    await connection_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back for heartbeat
            await websocket.send_json({
                "type": "heartbeat",
                "data": {"status": "connected"}
            })
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, session_id)
        logger.info(f"WebSocket disconnected for session {session_id}")

