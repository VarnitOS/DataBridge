"""
Event-driven messaging system for agent communication
"""
from typing import Dict, Any, Callable, List
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """Event bus for agent-to-agent communication"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict[str, Any]] = []
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to all subscribers"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._event_history.append(event)
        logger.info(f"Event published: {event_type}", extra=event)
        
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}")
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(callback)
        logger.info(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
    
    def get_event_history(self, event_type: str = None) -> List[Dict[str, Any]]:
        """Get event history, optionally filtered by type"""
        if event_type:
            return [e for e in self._event_history if e["type"] == event_type]
        return self._event_history


# Global event bus instance
event_bus = EventBus()

