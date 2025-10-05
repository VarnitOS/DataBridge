"""
Agent Pool Manager
Dynamically spawns and manages pools of agents for parallel processing
"""
from typing import Dict, Any, List, Type
import logging
import asyncio
from core.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentPoolManager:
    """
    Manages dynamic pools of agents
    
    - Spawns agents on demand
    - Distributes tasks across pool
    - Monitors agent health
    - Cleans up completed agents
    """
    
    def __init__(self):
        self._pools: Dict[str, List[BaseAgent]] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        logger.info("AgentPoolManager initialized")
    
    async def spawn_pool(
        self,
        agent_class: Type[BaseAgent],
        pool_size: int,
        pool_name: str,
        config: Dict[str, Any] = None
    ) -> List[BaseAgent]:
        """
        Spawn a pool of agents
        
        Args:
            agent_class: The agent class to instantiate
            pool_size: Number of agents to spawn
            pool_name: Name for this pool
            config: Configuration for agents
        
        Returns:
            List of spawned agent instances
        """
        logger.info(f"Spawning pool '{pool_name}' with {pool_size} agents")
        
        agents = []
        for i in range(pool_size):
            agent_id = f"{pool_name}_{i+1:03d}"
            agent = agent_class(agent_id=agent_id, config=config)
            agents.append(agent)
            logger.info(f"  ✓ Spawned agent: {agent_id}")
        
        self._pools[pool_name] = agents
        logger.info(f"✅ Pool '{pool_name}' ready with {pool_size} agents")
        
        return agents
    
    async def distribute_tasks(
        self,
        pool_name: str,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Distribute tasks across agents in a pool
        
        Uses round-robin distribution for load balancing
        """
        if pool_name not in self._pools:
            raise ValueError(f"Pool '{pool_name}' does not exist")
        
        pool = self._pools[pool_name]
        if not pool:
            raise ValueError(f"Pool '{pool_name}' is empty")
        
        logger.info(f"Distributing {len(tasks)} tasks across {len(pool)} agents in pool '{pool_name}'")
        
        # Create async tasks for parallel execution
        async_tasks = []
        for i, task in enumerate(tasks):
            agent = pool[i % len(pool)]  # Round-robin distribution
            async_tasks.append(agent.execute(task))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # Handle any exceptions
        successful = 0
        failed = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {result}")
                failed += 1
            else:
                successful += 1
        
        logger.info(f"Task distribution complete: {successful} succeeded, {failed} failed")
        
        return results
    
    async def execute_single_task(
        self,
        pool_name: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single task using the first available agent from pool
        """
        if pool_name not in self._pools:
            raise ValueError(f"Pool '{pool_name}' does not exist")
        
        pool = self._pools[pool_name]
        if not pool:
            raise ValueError(f"Pool '{pool_name}' is empty")
        
        # Use first agent in pool
        agent = pool[0]
        logger.info(f"Executing task with agent {agent.agent_id} from pool '{pool_name}'")
        
        result = await agent.execute(task)
        return result
    
    def get_pool(self, pool_name: str) -> List[BaseAgent]:
        """Get agents in a pool"""
        return self._pools.get(pool_name, [])
    
    def get_pool_size(self, pool_name: str) -> int:
        """Get size of a pool"""
        return len(self._pools.get(pool_name, []))
    
    async def shutdown_pool(self, pool_name: str):
        """Shutdown and cleanup a pool"""
        if pool_name in self._pools:
            pool = self._pools[pool_name]
            logger.info(f"Shutting down pool '{pool_name}' ({len(pool)} agents)")
            
            # Cleanup agents (if they have cleanup methods)
            for agent in pool:
                if hasattr(agent, 'cleanup'):
                    await agent.cleanup()
            
            del self._pools[pool_name]
            logger.info(f"✅ Pool '{pool_name}' shutdown complete")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get status of all pools"""
        return {
            "total_pools": len(self._pools),
            "pools": {
                name: {
                    "size": len(agents),
                    "agent_ids": [a.agent_id for a in agents]
                }
                for name, agents in self._pools.items()
            }
        }


# Global pool manager instance
pool_manager = AgentPoolManager()
