"""
WebSocket Server - Real-time agent communication broadcasting
"""
import asyncio
import json
import logging
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
from core.event_bus import event_bus

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.event_bus_subscribed = False
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Subscribe to event bus if this is the first connection
        if not self.event_bus_subscribed:
            event_bus.subscribe(self.broadcast_event)
            self.event_bus_subscribed = True
            logger.info("Subscribed to event bus")
        
        # Send recent history to new connection
        history = event_bus.get_history(limit=50)
        if history:
            try:
                await websocket.send_text(json.dumps({
                    "type": "history",
                    "events": history
                }))
            except Exception as e:
                logger.error(f"Failed to send history: {e}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_event(self, event: dict):
        """Broadcast an event to all connected clients"""
        if not self.active_connections:
            return
        
        message = json.dumps(event)
        
        # Send to all connections, remove dead ones
        dead_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                dead_connections.add(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.active_connections.discard(connection)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")


# Global connection manager
connection_manager = ConnectionManager()
