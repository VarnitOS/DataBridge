"""
Agent Test Harness - Test each agent individually
Run agents one by one to see their outputs
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load .env from parent directory
from dotenv import load_dotenv
env_path = parent_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logging.info(f"Loaded .env from {env_path}")
else:
    logging.warning(f".env file not found at {env_path}")

# Configure logging for clear output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_agents.log')
    ]
)

logger = logging.getLogger(__name__)


def print_header(agent_name: str):
    """Print a nice header for each agent test"""
    print("\n" + "="*80)
    print(f"🤖 TESTING: {agent_name}")
    print("="*80 + "\n")


def print_result(result: dict):
    """Pretty print agent results"""
    import json
    print("\n" + "-"*80)
    print("📊 AGENT OUTPUT:")
    print("-"*80)
    print(json.dumps(result, indent=2, default=str))
    print("-"*80 + "\n")


async def test_agent(agent_class, test_name: str, **kwargs):
    """
    Generic agent tester
    
    Args:
        agent_class: The agent class to test
        test_name: Name of the test
        **kwargs: Arguments to pass to agent.execute()
    """
    print_header(f"{agent_class.__name__} - {test_name}")
    
    try:
        # Create agent instance
        agent = agent_class(agent_id=f"test_{agent_class.__name__.lower()}", config={})
        logger.info(f"✅ Agent created: {agent.agent_id}")
        
        # Execute agent
        logger.info(f"🚀 Executing agent with params: {kwargs}")
        result = await agent.execute(kwargs)
        
        # Show results
        print_result(result)
        
        logger.info(f"✅ {test_name} completed successfully!")
        return result
        
    except Exception as e:
        logger.error(f"❌ {test_name} failed: {e}", exc_info=True)
        return {"error": str(e)}


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║        EY Data Integration - Agent Test Harness              ║
    ║                                                              ║
    ║  Test each agent individually to see what it does            ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("Test harness loaded. Use test_agent() to test individual agents.")
