"""
Snowflake warehouse sizing and management
"""
from typing import Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WarehouseSize(Enum):
    """Snowflake warehouse sizes"""
    X_SMALL = "X-SMALL"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    X_LARGE = "X-LARGE"
    XX_LARGE = "2X-LARGE"
    XXX_LARGE = "3X-LARGE"


class WarehouseManager:
    """Manages Snowflake warehouse allocation decisions"""
    
    def select_warehouse(
        self, 
        row_count: int, 
        complexity: str, 
        operation_type: str = "merge"
    ) -> WarehouseSize:
        """
        Autonomously decide warehouse size based on workload
        
        Args:
            row_count: Number of rows in dataset(s)
            complexity: "low", "medium", or "high"
            operation_type: Type of operation (merge, join, etc.)
        
        Returns:
            WarehouseSize enum
        """
        logger.info(
            f"Selecting warehouse for: rows={row_count}, "
            f"complexity={complexity}, operation={operation_type}"
        )
        
        # Decision matrix based on roadmap
        if row_count > 1_000_000:
            warehouse = WarehouseSize.X_LARGE
        elif row_count > 100_000 and complexity == "high":
            warehouse = WarehouseSize.LARGE
        elif row_count > 100_000:
            warehouse = WarehouseSize.MEDIUM
        elif row_count > 10_000:
            warehouse = WarehouseSize.SMALL
        else:
            warehouse = WarehouseSize.X_SMALL
        
        logger.info(f"Selected warehouse: {warehouse.value}")
        return warehouse
    
    def estimate_cost(self, warehouse: WarehouseSize, duration_seconds: float) -> float:
        """
        Estimate cost for warehouse usage
        
        Args:
            warehouse: Warehouse size
            duration_seconds: Estimated duration in seconds
        
        Returns:
            Estimated cost in dollars
        """
        # Approximate credits per hour for each warehouse size
        credits_per_hour = {
            WarehouseSize.X_SMALL: 1,
            WarehouseSize.SMALL: 2,
            WarehouseSize.MEDIUM: 4,
            WarehouseSize.LARGE: 8,
            WarehouseSize.X_LARGE: 16,
            WarehouseSize.XX_LARGE: 32,
            WarehouseSize.XXX_LARGE: 64,
        }
        
        hours = duration_seconds / 3600
        credits = credits_per_hour[warehouse] * hours
        cost = credits * 3.00  # $3 per credit (configurable)
        
        return round(cost, 4)


# Global warehouse manager instance
warehouse_manager = WarehouseManager()

