"""
Base Quality Agent - Foundation for all quality validation agents
"""
from typing import Dict, Any, List
import logging
from abc import abstractmethod
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool
from sf_infrastructure.connector import snowflake_connector

logger = logging.getLogger(__name__)


class BaseQualityAgent(BaseAgent):
    """
    Base class for all Quality Agents
    
    Provides common functionality:
    - SQL-based validation queries
    - Result aggregation
    - Pass/Fail determination
    - A2A registration
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str = "base_quality",
        capabilities: List[AgentCapability] = None,
        config: Dict[str, Any] = None
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities or [AgentCapability.DATA_QUALITY],
            config=config,
            auto_register=True
        )
        logger.info(f"Initialized {agent_type} agent: {agent_id}")
    
    def _define_tools(self):
        """Base quality agent doesn't expose tools directly - subclasses will"""
        self._tools = []
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a quality check task - must be implemented by subclasses"""
        pass
    
    async def run_quality_query(
        self,
        query: str,
        description: str = "Quality check"
    ) -> List[Dict[str, Any]]:
        """
        Execute quality validation query
        """
        logger.info(f"[{self.agent_id}] Running: {description}")
        logger.debug(f"[{self.agent_id}] Query: {query[:200]}...")
        
        try:
            results = await snowflake_connector.execute_query(query)
            logger.info(f"[{self.agent_id}] ✅ {description} completed: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] ❌ {description} failed: {e}")
            raise
    
    async def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        try:
            return await snowflake_connector.get_table_info(table_name)
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to get table info for {table_name}: {e}")
            return []
    
    async def get_row_count(self, table_name: str) -> int:
        """Get total row count"""
        try:
            return await snowflake_connector.get_row_count(table_name)
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to get row count: {e}")
            return 0
    
    def determine_status(self, issues_found: int, threshold: int = 0) -> str:
        """Determine overall status based on issues found"""
        if issues_found == 0:
            return "PASSED"
        elif issues_found <= threshold:
            return "WARNING"
        else:
            return "FAILED"
