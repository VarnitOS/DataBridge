"""
Base Merge Agent - Foundation for all merge operations

All merge agents inherit from this and implement specific merge strategies
"""
from typing import Dict, Any, List
import logging
from abc import abstractmethod
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool
from sf_infrastructure.connector import snowflake_connector

logger = logging.getLogger(__name__)


class BaseMergeAgent(BaseAgent):
    """
    Base class for all Merge Agents
    
    Provides common functionality:
    - SQL execution on Snowflake
    - Result validation
    - Error handling
    - A2A registration
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str = "base_merge",
        capabilities: List[AgentCapability] = None,
        config: Dict[str, Any] = None
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities or [AgentCapability.MERGE_EXECUTION],
            config=config,
            auto_register=True
        )
        logger.info(f"Initialized {agent_type} agent: {agent_id}")
    
    def _define_tools(self):
        """Base merge agent doesn't expose tools directly - subclasses will"""
        self._tools = []
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a merge task - must be implemented by subclasses"""
        pass
    
    async def execute_sql(
        self,
        sql: str,
        description: str = "Merge operation"
    ) -> Dict[str, Any]:
        """
        Execute SQL and return structured result
        """
        logger.info(f"[{self.agent_id}] Executing: {description}")
        logger.debug(f"[{self.agent_id}] SQL: {sql[:200]}...")
        
        try:
            await snowflake_connector.execute_non_query(sql)
            
            logger.info(f"[{self.agent_id}] ✅ {description} completed")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "operation": description,
                "sql_executed": sql[:500] + "..." if len(sql) > 500 else sql
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] ❌ {description} failed: {e}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "operation": description,
                "error": str(e),
                "sql_attempted": sql[:500] + "..." if len(sql) > 500 else sql
            }
    
    async def validate_table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            await snowflake_connector.get_table_info(table_name)
            return True
        except Exception:
            return False
    
    async def get_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        try:
            return await snowflake_connector.get_row_count(table_name)
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to get row count for {table_name}: {e}")
            return 0