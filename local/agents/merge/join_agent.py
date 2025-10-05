"""
Join Agent - Executes SQL JOIN operations for data merging
"""
from typing import Dict, Any, List
import logging
from agents.merge.base_merge_agent import BaseMergeAgent
from core.agent_registry import AgentCapability, AgentTool

logger = logging.getLogger(__name__)


class JoinAgent(BaseMergeAgent):
    """
    Executes SQL JOIN operations to merge datasets
    
    Supports:
    - FULL OUTER JOIN (merge all data)
    - INNER JOIN (only matching records)
    - LEFT JOIN / RIGHT JOIN
    - Handles column renaming and conflicts
    - Uses COALESCE for duplicate columns
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type="join_agent",
            capabilities=[AgentCapability.MERGE_EXECUTION],
            config=config
        )
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="execute_join_merge",
                description="Execute SQL JOIN operation to merge two datasets",
                capability=AgentCapability.MERGE_EXECUTION,
                parameters={
                    "type": "object",
                    "properties": {
                        "table1": {"type": "string", "description": "First table name"},
                        "table2": {"type": "string", "description": "Second table name"},
                        "output_table": {"type": "string", "description": "Output merged table name"},
                        "mappings": {
                            "type": "array",
                            "description": "Column mappings from mapping agent",
                            "items": {"type": "object"}
                        },
                        "join_type": {
                            "type": "string",
                            "enum": ["full_outer", "inner", "left", "right"],
                            "description": "Type of SQL JOIN"
                        }
                    },
                    "required": ["table1", "table2", "output_table", "mappings"]
                },
                handler=self._handle_join,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_join(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for join tool (called via A2A)"""
        return await self.execute_join(
            table1=params["table1"],
            table2=params["table2"],
            output_table=params["output_table"],
            mappings=params["mappings"],
            join_type=params.get("join_type", "full_outer")
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute join task"""
        task_type = task.get("type")
        
        if task_type == "join":
            return await self.execute_join(
                table1=task["table1"],
                table2=task["table2"],
                output_table=task["output_table"],
                mappings=task["mappings"],
                join_type=task.get("join_type", "full_outer")
            )
        else:
            raise ValueError(f"Unknown task type for JoinAgent: {task_type}")
    
    async def execute_join(
        self,
        table1: str,
        table2: str,
        output_table: str,
        mappings: List[Dict[str, Any]],
        join_type: str = "full_outer"
    ) -> Dict[str, Any]:
        """
        Execute JOIN operation to merge two tables
        
        Args:
            table1: First table name
            table2: Second table name
            output_table: Name for merged output table
            mappings: Column mappings (from Mapping Agent)
            join_type: Type of join (full_outer, inner, left, right)
        
        Returns:
            Merge results with row count and statistics
        """
        logger.info(f"[{self.agent_id}] Executing {join_type} JOIN: {table1} + {table2} → {output_table}")
        
        try:
            # Validate input tables exist
            if not await self.validate_table_exists(table1):
                raise ValueError(f"Table {table1} does not exist")
            if not await self.validate_table_exists(table2):
                raise ValueError(f"Table {table2} does not exist")
            
            # Generate JOIN SQL
            join_sql = await self._generate_join_sql(
                table1=table1,
                table2=table2,
                mappings=mappings,
                join_type=join_type
            )
            
            # Execute merge
            create_sql = f"CREATE OR REPLACE TABLE {output_table} AS\n{join_sql}"
            
            result = await self.execute_sql(
                sql=create_sql,
                description=f"{join_type.upper()} JOIN merge"
            )
            
            if not result["success"]:
                return result
            
            # Get result statistics
            row_count = await self.get_row_count(output_table)
            table1_count = await self.get_row_count(table1)
            table2_count = await self.get_row_count(table2)
            
            logger.info(f"[{self.agent_id}] ✅ Merge complete: {row_count} rows (from {table1_count} + {table2_count})")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "operation": "join_merge",
                "output_table": output_table,
                "input_tables": [table1, table2],
                "join_type": join_type,
                "statistics": {
                    "output_rows": row_count,
                    "table1_rows": table1_count,
                    "table2_rows": table2_count,
                    "mappings_applied": len(mappings)
                },
                "sql_generated": join_sql[:1000] + "..." if len(join_sql) > 1000 else join_sql
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] ❌ JOIN merge failed: {e}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "operation": "join_merge",
                "error": str(e)
            }
    
    async def _generate_join_sql(
        self,
        table1: str,
        table2: str,
        mappings: List[Dict[str, Any]],
        join_type: str
    ) -> str:
        """
        Generate SQL for JOIN operation based on mappings
        
        Handles:
        - Column selection with COALESCE for mapped columns
        - Proper aliasing for unmapped columns  
        - Metadata columns (_SOURCE_TABLE, _MERGE_TIMESTAMP)
        
        IMPORTANT: This preserves ALL columns from BOTH tables, not just mapped ones.
        """
        # Identify join key from mappings
        join_key_mapping = next((m for m in mappings if m.get('is_join_key')), None)
        
        if not join_key_mapping:
            # Fallback: use first high-confidence mapping as join key
            join_key_mapping = next((m for m in mappings if m.get('confidence', 0) >= 90), mappings[0] if mappings else None)
        
        if not join_key_mapping:
            raise ValueError("No suitable join key found in mappings")
        
        join_col1 = join_key_mapping['dataset_a_col']
        join_col2 = join_key_mapping['dataset_b_col']
        
        logger.info(f"[{self.agent_id}] Using join key: {table1}.{join_col1} = {table2}.{join_col2}")
        
        # Get ALL columns from both tables
        from sf_infrastructure.connector import snowflake_connector
        schema1 = await snowflake_connector.get_table_info(table1)
        schema2 = await snowflake_connector.get_table_info(table2)
        
        all_cols1 = {col.get('name') or col.get('NAME'): col for col in schema1}
        all_cols2 = {col.get('name') or col.get('NAME'): col for col in schema2}
        
        # Track which columns are mapped
        mapped_cols1 = {m['dataset_a_col'] for m in mappings}
        mapped_cols2 = {m['dataset_b_col'] for m in mappings}
        
        # Build SELECT clause
        select_cols = []
        
        # 1. Add mapped columns (use COALESCE to prefer non-null values)
        logger.info(f"[{self.agent_id}] Adding {len(mappings)} mapped columns with COALESCE")
        for mapping in mappings:
            col1 = mapping['dataset_a_col']
            col2 = mapping['dataset_b_col']
            unified = mapping['unified_name']
            
            select_cols.append(
                f"COALESCE(t1.\"{col1}\", t2.\"{col2}\") AS \"{unified}\""
            )
        
        # 2. Add unmapped columns from TABLE 1 (with prefix to avoid conflicts)
        unmapped1 = [col for col in all_cols1.keys() if col not in mapped_cols1]
        logger.info(f"[{self.agent_id}] Adding {len(unmapped1)} unmapped columns from {table1}")
        for col in unmapped1:
            # Use ds1_ prefix to indicate source
            select_cols.append(f"t1.\"{col}\" AS \"ds1_{col}\"")
        
        # 3. Add unmapped columns from TABLE 2 (with prefix to avoid conflicts)
        unmapped2 = [col for col in all_cols2.keys() if col not in mapped_cols2]
        logger.info(f"[{self.agent_id}] Adding {len(unmapped2)} unmapped columns from {table2}")
        for col in unmapped2:
            # Use ds2_ prefix to indicate source
            select_cols.append(f"t2.\"{col}\" AS \"ds2_{col}\"")
        
        # 4. Add metadata columns
        select_cols.append("CASE "
                          f"WHEN t1.\"{join_col1}\" IS NOT NULL AND t2.\"{join_col2}\" IS NOT NULL THEN 'BOTH' "
                          f"WHEN t1.\"{join_col1}\" IS NOT NULL THEN 'TABLE1' "
                          "ELSE 'TABLE2' "
                          "END AS \"_SOURCE_TABLE\"")
        
        select_cols.append("CURRENT_TIMESTAMP() AS \"_MERGE_TIMESTAMP\"")
        
        # Map join type to SQL
        join_type_sql = {
            "full_outer": "FULL OUTER JOIN",
            "inner": "INNER JOIN",
            "left": "LEFT JOIN",
            "right": "RIGHT JOIN"
        }.get(join_type, "FULL OUTER JOIN")
        
        # Build final SQL
        sql = f"""
SELECT
    {',\n    '.join(select_cols)}
FROM {table1} t1
{join_type_sql} {table2} t2
    ON t1.\"{join_col1}\" = t2.\"{join_col2}\"
"""
        
        logger.info(f"[{self.agent_id}] ✅ Generated SQL with {len(select_cols)} total columns:")
        logger.info(f"   • {len(mappings)} mapped (unified)")
        logger.info(f"   • {len(unmapped1)} from table1 (ds1_* prefix)")
        logger.info(f"   • {len(unmapped2)} from table2 (ds2_* prefix)")
        logger.info(f"   • 2 metadata columns")
        
        return sql.strip()
