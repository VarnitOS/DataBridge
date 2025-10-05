"""
Internal metrics collection and telemetry
"""
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Telemetry:
    """Telemetry collection for internal monitoring"""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {
            "api_requests": 0,
            "agent_spawns": {},
            "snowflake_queries": 0,
            "gemini_calls": 0,
            "errors": 0
        }
    
    def track_api_request(self, endpoint: str, duration: float):
        """Track API request"""
        self._metrics["api_requests"] += 1
        logger.info(f"API request: {endpoint}, duration: {duration}s")
    
    def track_agent_spawn(self, agent_type: str, count: int = 1):
        """Track agent spawning"""
        if agent_type not in self._metrics["agent_spawns"]:
            self._metrics["agent_spawns"][agent_type] = 0
        
        self._metrics["agent_spawns"][agent_type] += count
        logger.info(f"Agent spawned: {agent_type}, count: {count}")
    
    def track_snowflake_query(self, query_type: str, duration: float):
        """Track Snowflake query execution"""
        self._metrics["snowflake_queries"] += 1
        logger.info(f"Snowflake query: {query_type}, duration: {duration}s")
    
    def track_gemini_call(self, prompt_type: str, tokens_used: int = 0):
        """Track Gemini API call"""
        self._metrics["gemini_calls"] += 1
        logger.info(f"Gemini call: {prompt_type}, tokens: {tokens_used}")
    
    def track_error(self, error_type: str, message: str):
        """Track error occurrence"""
        self._metrics["errors"] += 1
        logger.error(f"Error tracked: {error_type} - {message}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return self._metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics"""
        self._metrics = {
            "api_requests": 0,
            "agent_spawns": {},
            "snowflake_queries": 0,
            "gemini_calls": 0,
            "errors": 0
        }


# Global telemetry instance
telemetry = Telemetry()

