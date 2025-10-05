"""
Snowflake compute cost tracking
"""
from typing import Dict, Any
from datetime import datetime
import logging
from core.config import settings

logger = logging.getLogger(__name__)


class CostTracker:
    """Tracks Snowflake compute costs"""
    
    def __init__(self):
        self._cost_log: list = []
        self._total_credits_used: float = 0.0
    
    def log_query_cost(
        self, 
        query_id: str, 
        warehouse_size: str, 
        duration_seconds: float, 
        row_count: int = 0
    ):
        """
        Log cost for a query execution
        
        Args:
            query_id: Unique query identifier
            warehouse_size: Warehouse size used
            duration_seconds: Query duration
            row_count: Rows processed
        """
        if not settings.ENABLE_COST_TRACKING:
            return
        
        # Approximate credit calculation
        credits_per_hour = {
            "X-SMALL": 1,
            "SMALL": 2,
            "MEDIUM": 4,
            "LARGE": 8,
            "X-LARGE": 16,
        }
        
        hours = duration_seconds / 3600
        credits = credits_per_hour.get(warehouse_size, 1) * hours
        cost_usd = credits * settings.SNOWFLAKE_COST_PER_CREDIT
        
        self._total_credits_used += credits
        
        cost_entry = {
            "query_id": query_id,
            "timestamp": datetime.utcnow().isoformat(),
            "warehouse_size": warehouse_size,
            "duration_seconds": duration_seconds,
            "row_count": row_count,
            "credits_used": round(credits, 4),
            "cost_usd": round(cost_usd, 4)
        }
        
        self._cost_log.append(cost_entry)
        
        logger.info(
            f"Query cost logged: {credits:.4f} credits (${cost_usd:.4f})",
            extra=cost_entry
        )
    
    def get_session_cost(self, session_id: str) -> Dict[str, Any]:
        """Get total cost for a session"""
        session_entries = [
            entry for entry in self._cost_log 
            if session_id in entry.get("query_id", "")
        ]
        
        total_credits = sum(e["credits_used"] for e in session_entries)
        total_cost = sum(e["cost_usd"] for e in session_entries)
        
        return {
            "session_id": session_id,
            "total_credits": round(total_credits, 4),
            "total_cost_usd": round(total_cost, 4),
            "queries": len(session_entries)
        }
    
    def get_total_cost(self) -> Dict[str, Any]:
        """Get total accumulated cost"""
        total_cost = self._total_credits_used * settings.SNOWFLAKE_COST_PER_CREDIT
        
        return {
            "total_credits_used": round(self._total_credits_used, 4),
            "total_cost_usd": round(total_cost, 4),
            "total_queries": len(self._cost_log)
        }


# Global cost tracker instance
cost_tracker = CostTracker()

