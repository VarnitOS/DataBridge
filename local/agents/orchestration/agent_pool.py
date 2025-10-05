"""
Agent pool management - spawns and manages agent instances
"""
from typing import List, Type, Any, Dict
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentInstance:
    """Represents a single agent instance"""
    
    def __init__(self, agent_class: Type, agent_id: str, config: Dict = None):
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.instance = agent_class(agent_id=agent_id, config=config or {})
        self.created_at = datetime.utcnow()
        self.status = "idle"
        self.tasks_completed = 0
    
    async def execute_task(self, task: Dict[str, Any]) -> Any:
        """Execute a task with this agent instance"""
        try:
            self.status = "busy"
            logger.info(f"Agent {self.agent_id} executing task: {task.get('type')}")
            
            result = await self.instance.execute(task)
            
            self.tasks_completed += 1
            self.status = "idle"
            
            return result
        except Exception as e:
            self.status = "error"
            logger.error(f"Agent {self.agent_id} task failed: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent instance status"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_class.__name__,
            "status": self.status,
            "tasks_completed": self.tasks_completed,
            "uptime_seconds": (datetime.utcnow() - self.created_at).total_seconds()
        }


class AgentPool:
    """
    Manages a pool of agent instances
    Simulates Kubernetes-style horizontal pod scaling
    """
    
    def __init__(self, agent_class: Type, pool_name: str):
        self.agent_class = agent_class
        self.pool_name = pool_name
        self.agents: List[AgentInstance] = []
        self._next_agent_idx = 0
    
    def spawn_agents(self, count: int, config: Dict = None) -> List[str]:
        """
        Spawn N agent instances
        
        Args:
            count: Number of agents to spawn
            config: Configuration to pass to agents
        
        Returns:
            List of spawned agent IDs
        """
        spawned_ids = []
        
        for i in range(count):
            agent_id = f"{self.pool_name}_{len(self.agents) + 1}_{str(uuid.uuid4())[:8]}"
            agent_instance = AgentInstance(
                agent_class=self.agent_class,
                agent_id=agent_id,
                config=config
            )
            
            self.agents.append(agent_instance)
            spawned_ids.append(agent_id)
            
            logger.info(f"Spawned agent: {agent_id}")
        
        return spawned_ids
    
    def get_next_available_agent(self) -> AgentInstance:
        """
        Get next available agent using round-robin
        Simulates load balancing
        """
        if not self.agents:
            raise RuntimeError(f"No agents available in pool {self.pool_name}")
        
        # Find idle agent
        for agent in self.agents:
            if agent.status == "idle":
                return agent
        
        # If all busy, use round-robin
        agent = self.agents[self._next_agent_idx % len(self.agents)]
        self._next_agent_idx += 1
        
        return agent
    
    async def execute_task(self, task: Dict[str, Any]) -> Any:
        """Execute task with next available agent"""
        agent = self.get_next_available_agent()
        return await agent.execute_task(task)
    
    async def execute_tasks_parallel(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple tasks in parallel across pool"""
        import asyncio
        
        # Distribute tasks across agents
        task_assignments = []
        for i, task in enumerate(tasks):
            agent = self.agents[i % len(self.agents)]
            task_assignments.append(agent.execute_task(task))
        
        # Execute all in parallel
        results = await asyncio.gather(*task_assignments, return_exceptions=True)
        
        return results
    
    def scale_down(self, target_count: int):
        """Scale down pool to target count"""
        if target_count >= len(self.agents):
            return
        
        # Remove idle agents first
        idle_agents = [a for a in self.agents if a.status == "idle"]
        to_remove = len(self.agents) - target_count
        
        for agent in idle_agents[:to_remove]:
            self.agents.remove(agent)
            logger.info(f"Scaled down agent: {agent.agent_id}")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get pool status"""
        return {
            "pool_name": self.pool_name,
            "agent_type": self.agent_class.__name__,
            "total_agents": len(self.agents),
            "idle_agents": len([a for a in self.agents if a.status == "idle"]),
            "busy_agents": len([a for a in self.agents if a.status == "busy"]),
            "error_agents": len([a for a in self.agents if a.status == "error"]),
            "total_tasks_completed": sum(a.tasks_completed for a in self.agents)
        }
    
    def shutdown(self):
        """Shutdown all agents in pool"""
        logger.info(f"Shutting down pool: {self.pool_name}")
        self.agents.clear()


class AgentPoolManager:
    """
    Global manager for all agent pools
    Coordinates multiple agent types
    """
    
    def __init__(self):
        self.pools: Dict[str, AgentPool] = {}
    
    def create_pool(self, agent_class: Type, pool_name: str) -> AgentPool:
        """Create a new agent pool"""
        if pool_name in self.pools:
            return self.pools[pool_name]
        
        pool = AgentPool(agent_class, pool_name)
        self.pools[pool_name] = pool
        
        logger.info(f"Created agent pool: {pool_name}")
        return pool
    
    def get_pool(self, pool_name: str) -> AgentPool:
        """Get existing pool"""
        if pool_name not in self.pools:
            raise KeyError(f"Pool {pool_name} not found")
        
        return self.pools[pool_name]
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all pools"""
        return {
            pool_name: pool.get_pool_status()
            for pool_name, pool in self.pools.items()
        }
    
    def shutdown_all(self):
        """Shutdown all pools"""
        for pool in self.pools.values():
            pool.shutdown()
        
        self.pools.clear()


# Global agent pool manager
agent_pool_manager = AgentPoolManager()

