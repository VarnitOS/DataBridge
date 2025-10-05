"""
Null Checker Agent - Validates data completeness by checking for NULL values
"""
from typing import Dict, Any
import logging
from agents.quality.base_quality_agent import BaseQualityAgent
from core.agent_registry import AgentCapability, AgentTool

logger = logging.getLogger(__name__)


class NullCheckerAgent(BaseQualityAgent):
    """
    Checks for NULL values and missing data
    
    Validates:
    - NULL percentage per column
    - Critical columns with NULLs
    - Overall data completeness score
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type="null_checker",
            capabilities=[AgentCapability.DATA_QUALITY],
            config=config
        )
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="check_nulls",
                description="Check for NULL values and calculate completeness score",
                capability=AgentCapability.DATA_QUALITY,
                parameters={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Table to validate"},
                        "null_threshold": {"type": "number", "description": "Max acceptable NULL percentage", "default": 5.0}
                    },
                    "required": ["table_name"]
                },
                handler=self._handle_null_check,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_null_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for null check tool (called via A2A)"""
        return await self.check_nulls(
            table_name=params["table_name"],
            null_threshold=params.get("null_threshold", 5.0)
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute null check task"""
        task_type = task.get("type")
        
        if task_type == "check_nulls":
            return await self.check_nulls(
                table_name=task["table_name"],
                null_threshold=task.get("null_threshold", 5.0)
            )
        else:
            raise ValueError(f"Unknown task type for NullCheckerAgent: {task_type}")
    
    async def check_nulls(
        self,
        table_name: str,
        null_threshold: float = 5.0
    ) -> Dict[str, Any]:
        """
        Check for NULL values in all columns
        
        Args:
            table_name: Table to analyze
            null_threshold: Maximum acceptable NULL percentage
        
        Returns:
            NULL analysis with per-column statistics
        """
        logger.info(f"[{self.agent_id}] Checking NULLs in {table_name}")
        
        try:
            # Get table schema
            schema = await self.get_table_info(table_name)
            total_rows = await self.get_row_count(table_name)
            
            if total_rows == 0:
                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "status": "WARNING",
                    "message": "Table is empty"
                }
            
            # Build query to check NULLs for all columns
            column_checks = []
            for col in schema:
                col_name = col.get('name') or col.get('NAME')
                column_checks.append(f"""
                    SUM(CASE WHEN "{col_name}" IS NULL THEN 1 ELSE 0 END) AS "{col_name}_nulls"
                """)
            
            query = f"""
            SELECT
                {','.join(column_checks)}
            FROM {table_name}
            """
            
            results = await self.run_quality_query(query, "NULL count analysis")
            
            if not results:
                raise ValueError("No results from NULL check query")
            
            result_row = results[0]
            
            # Analyze each column
            column_analysis = []
            columns_with_issues = []
            
            for col in schema:
                col_name = col.get('name') or col.get('NAME')
                null_count = result_row.get(f"{col_name}_nulls", 0)
                null_percentage = (null_count / total_rows * 100) if total_rows > 0 else 0
                
                status = "PASSED"
                if null_percentage > null_threshold:
                    status = "FAILED"
                    columns_with_issues.append(col_name)
                elif null_percentage > 0:
                    status = "WARNING"
                
                column_analysis.append({
                    "column": col_name,
                    "null_count": null_count,
                    "null_percentage": round(null_percentage, 2),
                    "status": status
                })
            
            # Calculate overall completeness
            total_cells = total_rows * len(schema)
            total_nulls = sum(c['null_count'] for c in column_analysis)
            completeness_score = round((1 - (total_nulls / total_cells)) * 100, 2) if total_cells > 0 else 100
            
            overall_status = self.determine_status(len(columns_with_issues), threshold=3)
            
            logger.info(f"[{self.agent_id}] ✅ NULL check complete: {len(columns_with_issues)} columns with issues")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "operation": "null_check",
                "table_name": table_name,
                "status": overall_status,
                "statistics": {
                    "total_rows": total_rows,
                    "total_columns": len(schema),
                    "columns_with_nulls": len([c for c in column_analysis if c['null_count'] > 0]),
                    "columns_exceeding_threshold": len(columns_with_issues),
                    "completeness_score": completeness_score
                },
                "column_analysis": column_analysis[:10],  # Limit to first 10 for display
                "columns_with_issues": columns_with_issues,
                "threshold_used": null_threshold
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] ❌ NULL check failed: {e}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "operation": "null_check",
                "error": str(e)
            }