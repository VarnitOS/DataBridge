"""
Dedupe Agent - Removes duplicate rows from merged datasets
"""
from typing import Dict, Any, List
import logging
from agents.merge.base_merge_agent import BaseMergeAgent
from core.agent_registry import AgentCapability, AgentTool

logger = logging.getLogger(__name__)


class DedupeAgent(BaseMergeAgent):
    """
    Removes duplicate rows using SQL QUALIFY and ROW_NUMBER()
    
    Strategies:
    - Keep most recent record (by timestamp)
    - Keep record with most complete data (fewest NULLs)
    - Custom priority rules
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type="dedupe_agent",
            capabilities=[AgentCapability.MERGE_EXECUTION],
            config=config
        )
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="remove_duplicates",
                description="Remove duplicate rows from a table using SQL QUALIFY",
                capability=AgentCapability.MERGE_EXECUTION,
                parameters={
                    "type": "object",
                    "properties": {
                        "input_table": {"type": "string", "description": "Table to deduplicate"},
                        "output_table": {"type": "string", "description": "Output deduplicated table"},
                        "unique_key": {"type": "string", "description": "Column to use as unique key"},
                        "order_by": {"type": "string", "description": "Column to order by (keep most recent)", "default": "_MERGE_TIMESTAMP"}
                    },
                    "required": ["input_table", "output_table", "unique_key"]
                },
                handler=self._handle_dedupe,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_dedupe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for dedupe tool (called via A2A)"""
        return await self.deduplicate(
            input_table=params["input_table"],
            output_table=params["output_table"],
            unique_key=params["unique_key"],
            order_by=params.get("order_by", "_MERGE_TIMESTAMP")
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dedupe task"""
        task_type = task.get("type")
        
        if task_type == "dedupe":
            return await self.deduplicate(
                input_table=task["input_table"],
                output_table=task["output_table"],
                unique_key=task["unique_key"],
                order_by=task.get("order_by", "_MERGE_TIMESTAMP")
            )
        else:
            raise ValueError(f"Unknown task type for DedupeAgent: {task_type}")
    
    async def deduplicate(
        self,
        input_table: str,
        output_table: str,
        unique_key: str,
        order_by: str = "_MERGE_TIMESTAMP"
    ) -> Dict[str, Any]:
        """
        Remove duplicate rows based on a unique key
        
        Args:
            input_table: Table with potential duplicates
            output_table: Output table with duplicates removed
            unique_key: Column to identify duplicates
            order_by: Column to determine which record to keep (DESC)
        
        Returns:
            Deduplication results with statistics
        """
        logger.info(f"[{self.agent_id}] Deduplicating {input_table} by {unique_key}")
        
        try:
            # Validate input table exists
            if not await self.validate_table_exists(input_table):
                raise ValueError(f"Table {input_table} does not exist")
            
            # Get count before deduplication
            before_count = await self.get_row_count(input_table)
            
            # Generate dedupe SQL using QUALIFY
            # Note: Use uppercase for Snowflake column names
            unique_key_upper = unique_key.upper()
            order_by_upper = order_by.upper()
            
            dedupe_sql = f"""
CREATE OR REPLACE TABLE {output_table} AS
SELECT *
FROM {input_table}
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY {unique_key_upper}
    ORDER BY {order_by_upper} DESC NULLS LAST
) = 1
"""
            
            result = await self.execute_sql(
                sql=dedupe_sql,
                description="Deduplication"
            )
            
            if not result["success"]:
                return result
            
            # Get count after deduplication
            after_count = await self.get_row_count(output_table)
            duplicates_removed = before_count - after_count
            
            logger.info(f"[{self.agent_id}] ✅ Deduplication complete: {duplicates_removed:,} duplicates removed")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "operation": "deduplication",
                "input_table": input_table,
                "output_table": output_table,
                "unique_key": unique_key,
                "statistics": {
                    "before_count": before_count,
                    "after_count": after_count,
                    "duplicates_removed": duplicates_removed,
                    "duplicate_percentage": round((duplicates_removed / before_count * 100), 2) if before_count > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] ❌ Deduplication failed: {e}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "operation": "deduplication",
                "error": str(e)
            }
