"""
Event Bus - Broadcasts agent communication events to WebSocket clients
"""
import asyncio
import json
import logging
from typing import List, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class EventBus:
    """
    Central event bus for broadcasting agent communication events
    """
    
    def __init__(self):
        self.subscribers: List[Callable] = []
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000  # Keep last 1000 events
        logger.info("EventBus initialized")
    
    def subscribe(self, callback: Callable):
        """Subscribe to events"""
        self.subscribers.append(callback)
        logger.info(f"New subscriber added. Total subscribers: {len(self.subscribers)}")
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from events"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.info(f"Subscriber removed. Total subscribers: {len(self.subscribers)}")
    
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """
        Emit an event to all subscribers
        
        Args:
            event_type: Type of event (e.g., 'agent_call', 'agent_response', 'agent_error')
            data: Event data
        """
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Broadcast to all subscribers
        for subscriber in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(event)
                else:
                    subscriber(event)
            except Exception as e:
                logger.error(f"Error calling subscriber: {e}")
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history"""
        return self.event_history[-limit:]
    
    def clear_history(self):
        """Clear event history"""
        self.event_history.clear()


# Global event bus instance
event_bus = EventBus()
