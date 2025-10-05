"""
Agent Registry - MCP-style Agent Discovery and Communication

Agents register themselves as "tool servers" that other agents can discover and invoke.
This enables Agent-to-Agent (A2A) communication without user intervention.
"""
from typing import Dict, Any, List, Optional, Callable
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AgentCapability(str, Enum):
    """Types of capabilities agents can provide"""
    DATA_INGESTION = "data_ingestion"
    SCHEMA_ANALYSIS = "schema_analysis"
    SQL_GENERATION = "sql_generation"
    CONFLICT_DETECTION = "conflict_detection"
    DATA_QUALITY = "data_quality"
    MERGE_EXECUTION = "merge_execution"
    JIRA_INTEGRATION = "jira_integration"
    MONITORING = "monitoring"


@dataclass
class AgentTool:
    """A tool (capability) exposed by an agent"""
    name: str
    description: str
    capability: AgentCapability
    parameters: Dict[str, Any]
    handler: Callable  # Async function to execute the tool
    agent_id: str


class AgentRegistry:
    """
    Central registry for all agents (MCP-style tool server)
    
    Agents register their capabilities as "tools" that other agents can invoke.
    This enables:
    - Agent discovery
    - Agent-to-Agent communication
    - Automatic orchestration
    """
    
    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._tools: Dict[str, AgentTool] = {}
        self._capabilities: Dict[AgentCapability, List[str]] = {}
        logger.info("🔧 Agent Registry initialized (MCP-style)")
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        tools: List[AgentTool],
        metadata: Dict[str, Any] = None
    ):
        """
        Register an agent and its tools (like MCP server registration)
        """
        self._agents[agent_id] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "tools": [t.name for t in tools],
            "metadata": metadata or {},
            "status": "active"
        }
        
        # Register each tool
        for tool in tools:
            self._tools[tool.name] = tool
            
            # Index by capability
            if tool.capability not in self._capabilities:
                self._capabilities[tool.capability] = []
            self._capabilities[tool.capability].append(tool.name)
        
        logger.info(f"✅ Registered agent [{agent_id}] with {len(tools)} tools")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self._agents:
            # Remove tools
            tool_names = self._agents[agent_id]["tools"]
            for tool_name in tool_names:
                if tool_name in self._tools:
                    del self._tools[tool_name]
            
            del self._agents[agent_id]
            logger.info(f"🗑️ Unregistered agent [{agent_id}]")
    
    def discover_agents(
        self,
        capability: Optional[AgentCapability] = None,
        agent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover agents by capability or type
        """
        results = []
        
        for agent_id, agent_info in self._agents.items():
            if capability and capability not in agent_info["capabilities"]:
                continue
            if agent_type and agent_info["agent_type"] != agent_type:
                continue
            
            results.append(agent_info)
        
        return results
    
    def discover_tools(
        self,
        capability: Optional[AgentCapability] = None
    ) -> List[AgentTool]:
        """
        Discover available tools by capability
        """
        if capability:
            tool_names = self._capabilities.get(capability, [])
            return [self._tools[name] for name in tool_names if name in self._tools]
        
        return list(self._tools.values())
    
    def get_tool(self, tool_name: str) -> Optional[AgentTool]:
        """Get a specific tool by name"""
        return self._tools.get(tool_name)
    
    async def invoke_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        requester_agent_id: str = None
    ) -> Dict[str, Any]:
        """
        Invoke a tool (Agent-to-Agent call)
        
        This is the core of A2A communication - one agent calling another
        """
        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        logger.info(f"🔄 A2A Call: [{requester_agent_id or 'unknown'}] → [{tool.agent_id}].{tool_name}")
        
        # Emit event: agent communication started
        try:
            from core.event_bus import event_bus
            await event_bus.emit("agent_call", {
                "from_agent": requester_agent_id or "unknown",
                "to_agent": tool.agent_id,
                "tool_name": tool_name,
                "capability": tool.capability.value,
                "parameters": parameters
            })
        except Exception as emit_error:
            logger.warning(f"Failed to emit event: {emit_error}")
        
        try:
            # Invoke the tool's handler (async function)
            result = await tool.handler(parameters)
            
            logger.info(f"✅ A2A Call completed: {tool_name}")
            
            # Emit event: agent communication completed
            try:
                await event_bus.emit("agent_response", {
                    "from_agent": tool.agent_id,
                    "to_agent": requester_agent_id or "unknown",
                    "tool_name": tool_name,
                    "capability": tool.capability.value,
                    "success": True
                })
            except Exception as emit_error:
                logger.warning(f"Failed to emit event: {emit_error}")
            
            return {
                "success": True,
                "tool": tool_name,
                "agent": tool.agent_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"❌ A2A Call failed: {tool_name} - {e}")
            
            # Emit event: agent communication failed
            try:
                await event_bus.emit("agent_error", {
                    "from_agent": tool.agent_id,
                    "to_agent": requester_agent_id or "unknown",
                    "tool_name": tool_name,
                    "capability": tool.capability.value,
                    "error": str(e)
                })
            except Exception as emit_error:
                logger.warning(f"Failed to emit event: {emit_error}")
            
            return {
                "success": False,
                "tool": tool_name,
                "agent": tool.agent_id,
                "error": str(e)
            }
    
    async def invoke_capability(
        self,
        capability: AgentCapability,
        parameters: Dict[str, Any],
        requester_agent_id: str = None,
        prefer_agent_id: str = None
    ) -> Dict[str, Any]:
        """
        Invoke any agent that provides a capability
        
        This is for high-level requests where you don't care which specific agent handles it
        """
        tools = self.discover_tools(capability)
        
        if not tools:
            raise ValueError(f"No agents available for capability: {capability}")
        
        # Prefer specific agent if specified
        if prefer_agent_id:
            tool = next((t for t in tools if t.agent_id == prefer_agent_id), None)
            if tool:
                return await self.invoke_tool(tool.name, parameters, requester_agent_id)
        
        # Otherwise, use first available
        tool = tools[0]
        return await self.invoke_tool(tool.name, parameters, requester_agent_id)
    
    def get_all_tools_for_gemini(self) -> List[Dict[str, Any]]:
        """
        Get all tools in Gemini function-calling format
        So Gemini can see what agents are available
        """
        gemini_tools = []
        
        for tool in self._tools.values():
            gemini_tools.append({
                "name": tool.name,
                "description": f"{tool.description} (provided by {tool.agent_id})",
                "parameters": tool.parameters
            })
        
        return gemini_tools
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status for monitoring"""
        return {
            "total_agents": len(self._agents),
            "total_tools": len(self._tools),
            "agents": list(self._agents.keys()),
            "capabilities": {
                cap.value: len(tools) for cap, tools in self._capabilities.items()
            }
        }


# Global registry instance (singleton)
agent_registry = AgentRegistry()
