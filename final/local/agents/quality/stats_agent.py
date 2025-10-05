"""
Stats Agent - Generates statistical profile of data
"""
from typing import Dict, Any
import logging
from agents.quality.base_quality_agent import BaseQualityAgent
from core.agent_registry import AgentCapability, AgentTool

logger = logging.getLogger(__name__)


class StatsAgent(BaseQualityAgent):
    """
    Generates statistical profile and summary statistics
    
    Provides:
    - Row and column counts
    - Data type distribution
    - Basic statistics (for numeric columns)
    - Cardinality analysis
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type="stats",
            capabilities=[AgentCapability.DATA_QUALITY],
            config=config
        )
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="generate_statistics",
                description="Generate statistical profile and summary statistics for a table",
                capability=AgentCapability.DATA_QUALITY,
                parameters={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Table to profile"}
                    },
                    "required": ["table_name"]
                },
                handler=self._handle_stats,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for stats tool (called via A2A)"""
        return await self.generate_stats(
            table_name=params["table_name"]
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute stats generation task"""
        task_type = task.get("type")
        
        if task_type == "generate_stats":
            return await self.generate_stats(
                table_name=task["table_name"]
            )
        else:
            raise ValueError(f"Unknown task type for StatsAgent: {task_type}")
    
    async def generate_stats(
        self,
        table_name: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive statistics for a table
        
        Args:
            table_name: Table to profile
        
        Returns:
            Statistical profile with row counts, cardinality, etc.
        """
        logger.info(f"[{self.agent_id}] Generating statistics for {table_name}")
        
        try:
            # Get basic info
            schema = await self.get_table_info(table_name)
            total_rows = await self.get_row_count(table_name)
            
            if total_rows == 0:
                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "status": "WARNING",
                    "message": "Table is empty"
                }
            
            # Build query for cardinality analysis
            cardinality_selects = []
            for col in schema:
                col_name = col.get('name') or col.get('NAME')
                cardinality_selects.append(
                    f'COUNT(DISTINCT "{col_name}") AS "{col_name}_distinct"'
                )
            
            cardinality_query = f"""
            SELECT
                {',\n                '.join(cardinality_selects)}
            FROM {table_name}
            """
            
            cardinality_results = await self.run_quality_query(cardinality_query, "Cardinality analysis")
            
            if not cardinality_results:
                raise ValueError("No results from cardinality query")
            
            cardinality_row = cardinality_results[0]
            
            # Analyze each column
            column_stats = []
            for col in schema:
                col_name = col.get('name') or col.get('NAME')
                col_type = col.get('type') or col.get('TYPE')
                distinct_count = cardinality_row.get(f"{col_name}_distinct", 0)
                cardinality_ratio = round((distinct_count / total_rows * 100), 2) if total_rows > 0 else 0
                
                # Determine if this is likely a key column
                is_likely_key = cardinality_ratio > 95
                
                column_stats.append({
                    "column": col_name,
                    "type": col_type,
                    "distinct_count": distinct_count,
                    "cardinality_ratio": cardinality_ratio,
                    "is_likely_key": is_likely_key
                })
            
            # Calculate summary statistics
            high_cardinality_cols = len([c for c in column_stats if c['cardinality_ratio'] > 90])
            low_cardinality_cols = len([c for c in column_stats if c['cardinality_ratio'] < 10])
            likely_keys = [c['column'] for c in column_stats if c['is_likely_key']]
            
            logger.info(f"[{self.agent_id}] ✅ Statistics generation complete")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "operation": "generate_statistics",
                "table_name": table_name,
                "status": "PASSED",
                "summary": {
                    "total_rows": total_rows,
                    "total_columns": len(schema),
                    "high_cardinality_columns": high_cardinality_cols,
                    "low_cardinality_columns": low_cardinality_cols,
                    "likely_primary_keys": likely_keys
                },
                "column_statistics": column_stats[:15],  # Show first 15 columns
                "recommendations": self._generate_recommendations(column_stats, total_rows)
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] ❌ Statistics generation failed: {e}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "operation": "generate_statistics",
                "error": str(e)
            }
    
    def _generate_recommendations(self, column_stats: list, total_rows: int) -> list:
        """Generate data quality recommendations based on statistics"""
        recommendations = []
        
        # Find potential primary keys
        likely_keys = [c['column'] for c in column_stats if c['is_likely_key']]
        if likely_keys:
            recommendations.append(f"Potential primary keys: {', '.join(likely_keys[:3])}")
        else:
            recommendations.append("No unique key columns detected - consider adding a primary key")
        
        # Find low cardinality columns (good for indexing)
        low_card_cols = [c['column'] for c in column_stats if c['cardinality_ratio'] < 5]
        if low_card_cols:
            recommendations.append(f"Low cardinality columns suitable for indexing: {', '.join(low_card_cols[:3])}")
        
        # Check if table is large
        if total_rows > 1000000:
            recommendations.append(f"Large table ({total_rows:,} rows) - consider partitioning for better performance")
        
        return recommendations
