"""
Base Agent with A2A Communication Support

All agents inherit from this to get:
- Agent registry integration
- Tool exposure (MCP-style)
- Agent-to-Agent communication
"""
from typing import Dict, Any, List, Optional
import logging
from abc import ABC, abstractmethod
from core.agent_registry import agent_registry, AgentTool, AgentCapability

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents with A2A communication support
    
    Agents can:
    1. Register themselves with the registry
    2. Expose tools that other agents can invoke
    3. Invoke tools from other agents
    4. Discover other agents by capability
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        config: Dict[str, Any] = None,
        auto_register: bool = True
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.config = config or {}
        
        # Subclasses define their tools
        self._tools: List[AgentTool] = []
        
        # Register with registry
        if auto_register:
            self._register()
        
        logger.info(f"🤖 Initialized {agent_type} [{agent_id}]")
    
    def _register(self):
        """Register this agent with the registry"""
        # Define tools (subclasses override this)
        self._define_tools()
        
        # Register
        agent_registry.register_agent(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            capabilities=self.capabilities,
            tools=self._tools,
            metadata=self.config
        )
    
    def _define_tools(self):
        """
        Define tools this agent exposes (override in subclasses)
        
        Example:
        self._tools = [
            AgentTool(
                name="read_schema",
                description="Read table schema from Snowflake",
                capability=AgentCapability.SCHEMA_ANALYSIS,
                parameters={...},
                handler=self._handle_read_schema,
                agent_id=self.agent_id
            )
        ]
        """
        pass
    
    async def invoke_agent(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke another agent's tool (A2A communication)
        """
        return await agent_registry.invoke_tool(
            tool_name=tool_name,
            parameters=parameters,
            requester_agent_id=self.agent_id
        )
    
    async def invoke_capability(
        self,
        capability: AgentCapability,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke any agent that provides a capability
        """
        return await agent_registry.invoke_capability(
            capability=capability,
            parameters=parameters,
            requester_agent_id=self.agent_id
        )
    
    def discover_agents(
        self,
        capability: Optional[AgentCapability] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover other agents
        """
        return agent_registry.discover_agents(capability=capability)
    
    def discover_tools(
        self,
        capability: Optional[AgentCapability] = None
    ) -> List[AgentTool]:
        """
        Discover available tools
        """
        return agent_registry.discover_tools(capability=capability)
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method (subclasses implement)
        """
        pass
    
    def __del__(self):
        """Unregister on deletion"""
        try:
            agent_registry.unregister_agent(self.agent_id)
        except:
            pass
