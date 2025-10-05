"""
Resource manager - decides agent allocation based on workload complexity
Implements the autonomous decision-making for agent spawning
"""
from typing import Dict, Any
import logging
from core.config import settings
from sf_infrastructure.warehouse_manager import WarehouseSize

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Autonomously decides resource allocation for merge operations
    Implements the decision matrix from the roadmap
    """
    
    def determine_complexity(
        self,
        row_count: int,
        column_count: int,
        has_nested_data: bool = False,
        potential_join_keys: int = 1
    ) -> str:
        """
        Determine schema complexity level
        
        Returns: "low", "medium", or "high"
        """
        complexity_score = 0
        
        # Column count factor
        if column_count < 10:
            complexity_score += 1
        elif column_count <= 30:
            complexity_score += 2
        else:
            complexity_score += 3
        
        # Join key ambiguity
        if potential_join_keys > 3:
            complexity_score += 2
        elif potential_join_keys > 1:
            complexity_score += 1
        
        # Nested data
        if has_nested_data:
            complexity_score += 2
        
        # Determine level
        if complexity_score <= 2:
            return "low"
        elif complexity_score <= 5:
            return "medium"
        else:
            return "high"
    
    def calculate_agent_allocation(
        self,
        dataset_size: int,
        schema_complexity: str
    ) -> Dict[str, Any]:
        """
        Calculate agent allocation based on workload
        
        Implements the decision matrix from roadmap:
        - < 10K rows, low complexity: minimal agents
        - 100K-1M rows, high complexity: heavy parallelization
        - > 1M rows: maximum agents
        
        Args:
            dataset_size: Total row count
            schema_complexity: "low", "medium", or "high"
        
        Returns:
            Dict with agent counts and warehouse size
        """
        logger.info(
            f"Calculating allocation for: size={dataset_size}, "
            f"complexity={schema_complexity}"
        )
        
        # Decision matrix based on roadmap
        if dataset_size > 1_000_000:
            # Very large dataset
            allocation = {
                "gemini_agents": min(3, settings.MAX_GEMINI_AGENTS),
                "merge_agents": min(10, settings.MAX_MERGE_AGENTS),
                "quality_agents": 5,
                "snowflake_warehouse": WarehouseSize.X_LARGE.value
            }
        
        elif dataset_size > 100_000:
            # Large dataset
            if schema_complexity == "high":
                allocation = {
                    "gemini_agents": min(3, settings.MAX_GEMINI_AGENTS),
                    "merge_agents": min(7, settings.MAX_MERGE_AGENTS),
                    "quality_agents": 5,
                    "snowflake_warehouse": WarehouseSize.X_LARGE.value
                }
            elif schema_complexity == "medium":
                allocation = {
                    "gemini_agents": min(2, settings.MAX_GEMINI_AGENTS),
                    "merge_agents": min(5, settings.MAX_MERGE_AGENTS),
                    "quality_agents": 5,
                    "snowflake_warehouse": WarehouseSize.LARGE.value
                }
            else:  # low
                allocation = {
                    "gemini_agents": min(2, settings.MAX_GEMINI_AGENTS),
                    "merge_agents": min(3, settings.MAX_MERGE_AGENTS),
                    "quality_agents": 4,
                    "snowflake_warehouse": WarehouseSize.MEDIUM.value
                }
        
        elif dataset_size > 10_000:
            # Medium dataset
            if schema_complexity == "high":
                allocation = {
                    "gemini_agents": min(2, settings.MAX_GEMINI_AGENTS),
                    "merge_agents": min(5, settings.MAX_MERGE_AGENTS),
                    "quality_agents": 5,
                    "snowflake_warehouse": WarehouseSize.LARGE.value
                }
            elif schema_complexity == "medium":
                allocation = {
                    "gemini_agents": 2,
                    "merge_agents": 3,
                    "quality_agents": 4,
                    "snowflake_warehouse": WarehouseSize.MEDIUM.value
                }
            else:  # low
                allocation = {
                    "gemini_agents": 1,
                    "merge_agents": 2,
                    "quality_agents": 3,
                    "snowflake_warehouse": WarehouseSize.SMALL.value
                }
        
        else:
            # Small dataset
            allocation = {
                "gemini_agents": 1,
                "merge_agents": 1,
                "quality_agents": 3,
                "snowflake_warehouse": WarehouseSize.X_SMALL.value
            }
        
        logger.info(f"Allocation decision: {allocation}")
        
        return allocation
    
    def should_escalate_to_jira(self, confidence: int) -> bool:
        """
        Determine if mapping should be escalated to Jira
        
        Args:
            confidence: Confidence score (0-100)
        
        Returns:
            True if should create Jira ticket
        """
        return confidence < settings.JIRA_ESCALATION_THRESHOLD
    
    def estimate_duration(
        self,
        dataset_size: int,
        schema_complexity: str,
        operation_type: str = "merge"
    ) -> float:
        """
        Estimate operation duration in seconds
        
        Args:
            dataset_size: Row count
            schema_complexity: Complexity level
            operation_type: Type of operation
        
        Returns:
            Estimated duration in seconds
        """
        # Base time per row (seconds)
        base_time_per_row = 0.0001
        
        # Complexity multiplier
        complexity_multipliers = {
            "low": 1.0,
            "medium": 1.5,
            "high": 2.5
        }
        
        multiplier = complexity_multipliers.get(schema_complexity, 1.0)
        
        # Calculate estimate
        estimated_seconds = dataset_size * base_time_per_row * multiplier
        
        # Add overhead
        estimated_seconds += 10  # Startup overhead
        
        logger.info(f"Estimated duration: {estimated_seconds:.2f} seconds")
        
        return round(estimated_seconds, 2)


# Global resource manager instance
resource_manager = ResourceManager()

