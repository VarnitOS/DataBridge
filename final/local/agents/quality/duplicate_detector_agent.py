"""
Duplicate Detector Agent - Finds duplicate records
"""
from typing import Dict, Any
import logging
from agents.quality.base_quality_agent import BaseQualityAgent
from core.agent_registry import AgentCapability, AgentTool

logger = logging.getLogger(__name__)


class DuplicateDetectorAgent(BaseQualityAgent):
    """
    Detects duplicate records based on key columns
    
    Validates:
    - Exact duplicates (all columns match)
    - Key-based duplicates (specified columns match)
    - Duplicate percentage
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type="duplicate_detector",
            capabilities=[AgentCapability.DATA_QUALITY],
            config=config
        )
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="detect_duplicates",
                description="Detect duplicate records based on key columns",
                capability=AgentCapability.DATA_QUALITY,
                parameters={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Table to analyze"},
                        "key_columns": {"type": "array", "description": "Columns to use as unique key", "items": {"type": "string"}},
                        "duplicate_threshold": {"type": "number", "description": "Max acceptable duplicate percentage", "default": 1.0}
                    },
                    "required": ["table_name"]
                },
                handler=self._handle_duplicate_check,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_duplicate_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for duplicate check tool (called via A2A)"""
        return await self.detect_duplicates(
            table_name=params["table_name"],
            key_columns=params.get("key_columns"),
            duplicate_threshold=params.get("duplicate_threshold", 1.0)
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute duplicate detection task"""
        task_type = task.get("type")
        
        if task_type == "detect_duplicates":
            return await self.detect_duplicates(
                table_name=task["table_name"],
                key_columns=task.get("key_columns"),
                duplicate_threshold=task.get("duplicate_threshold", 1.0)
            )
        else:
            raise ValueError(f"Unknown task type for DuplicateDetectorAgent: {task_type}")
    
    async def detect_duplicates(
        self,
        table_name: str,
        key_columns: list = None,
        duplicate_threshold: float = 1.0
    ) -> Dict[str, Any]:
        """
        Detect duplicate records
        
        Args:
            table_name: Table to analyze
            key_columns: Columns to use as unique key (if None, finds likely ID column)
            duplicate_threshold: Maximum acceptable duplicate percentage
        
        Returns:
            Duplicate analysis with examples
        """
        logger.info(f"[{self.agent_id}] Detecting duplicates in {table_name}")
        
        try:
            total_rows = await self.get_row_count(table_name)
            
            if total_rows == 0:
                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "status": "WARNING",
                    "message": "Table is empty"
                }
            
            # If no key columns specified, find likely ID column
            if not key_columns:
                schema = await self.get_table_info(table_name)
                key_columns = []
                for col in schema:
                    col_name = col.get('name') or col.get('NAME')
                    if any(indicator in col_name.lower() for indicator in ['id', 'key', 'customer']):
                        key_columns.append(col_name)
                        break
                
                if not key_columns:
                    # Use first column as key
                    key_columns = [schema[0].get('name') or schema[0].get('NAME')]
            
            logger.info(f"[{self.agent_id}] Using key columns: {key_columns}")
            
            # Build GROUP BY clause
            key_cols_quoted = [f'"{col}"' for col in key_columns]
            key_cols_str = ', '.join(key_cols_quoted)
            
            # Find duplicates
            duplicate_query = f"""
            SELECT
                {key_cols_str},
                COUNT(*) as duplicate_count
            FROM {table_name}
            GROUP BY {key_cols_str}
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 100
            """
            
            duplicates = await self.run_quality_query(duplicate_query, "Duplicate detection")
            
            total_duplicate_records = sum(d.get('DUPLICATE_COUNT', 0) for d in duplicates)
            unique_duplicate_keys = len(duplicates)
            duplicate_percentage = round((total_duplicate_records / total_rows * 100), 2) if total_rows > 0 else 0
            
            status = self.determine_status(
                unique_duplicate_keys,
                threshold=int(total_rows * duplicate_threshold / 100)
            )
            
            logger.info(f"[{self.agent_id}] ✅ Duplicate detection complete: {unique_duplicate_keys} duplicate keys found")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "operation": "duplicate_detection",
                "table_name": table_name,
                "status": status,
                "statistics": {
                    "total_rows": total_rows,
                    "unique_duplicate_keys": unique_duplicate_keys,
                    "total_duplicate_records": total_duplicate_records,
                    "duplicate_percentage": duplicate_percentage
                },
                "key_columns": key_columns,
                "sample_duplicates": duplicates[:10],  # Show first 10 examples
                "threshold_used": duplicate_threshold
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] ❌ Duplicate detection failed: {e}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "operation": "duplicate_detection",
                "error": str(e)
            }
