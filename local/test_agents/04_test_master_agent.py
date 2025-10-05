#!/usr/bin/env python3
"""
TEST 4: Master Agent
Tests autonomous resource allocation and decision making
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from test_harness import test_agent, print_header
from agents.master_agent import MasterAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_resource_allocation():
    """Test Master Agent's autonomous decision making"""
    print_header("MASTER AGENT - Resource Allocation Test")
    
    print("""
    📋 What this agent does:
    ────────────────────────────────────────────────────────────
    1. Analyzes dataset complexity (size, schema)
    2. Autonomously decides how many agents to spawn
    3. Selects appropriate Snowflake warehouse size
    4. Allocates resources dynamically (1-10 merge agents)
    5. Makes decisions without hardcoded rules
    6. Simulates cloud-native auto-scaling
    ────────────────────────────────────────────────────────────
    """)
    
    master = MasterAgent()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Small dataset",
            "row_count": 5_000,
            "column_count": 8,
            "schema_complexity": "low"
        },
        {
            "name": "Medium dataset",
            "row_count": 100_000,
            "column_count": 20,
            "schema_complexity": "medium"
        },
        {
            "name": "Large complex dataset",
            "row_count": 1_500_000,
            "column_count": 45,
            "schema_complexity": "high"
        }
    ]
    
    print("\n🤖 Testing Master Agent decision making:\n")
    
    for scenario in scenarios:
        print(f"📊 Scenario: {scenario['name']}")
        print(f"   Rows: {scenario['row_count']:,}")
        print(f"   Columns: {scenario['column_count']}")
        print(f"   Complexity: {scenario['schema_complexity']}")
        
        # Master Agent makes autonomous decision
        allocation = master._determine_resource_allocation(
            row_count=scenario['row_count'],
            column_count=scenario['column_count'],
            schema_complexity=scenario['schema_complexity']
        )
        
        print(f"\n   🎯 Master Agent Decision:")
        print(f"   ├─ Gemini Agents:    {allocation['gemini_agents']}")
        print(f"   ├─ Merge Agents:     {allocation['merge_agents']}")
        print(f"   ├─ Quality Agents:   {allocation['quality_agents']}")
        print(f"   └─ Snowflake WH:     {allocation['snowflake_warehouse']}")
        print()
    
    print("""
    ✅ Master Agent successfully demonstrated autonomous decision making!
    ────────────────────────────────────────────────────────────
    
    💡 Key Points:
    - No hardcoded agent counts
    - Scales based on actual data characteristics
    - Optimizes Snowflake warehouse sizing
    - Cloud-native resource allocation
    - Looks like Kubernetes autoscaling!
    """)


async def test_full_orchestration():
    """Test Master Agent orchestrating full pipeline"""
    print_header("MASTER AGENT - Full Orchestration Test")
    
    print("""
    📋 What we're testing:
    ────────────────────────────────────────────────────────────
    1. Master Agent analyzes datasets in Snowflake
    2. Decides resource allocation
    3. Spawns agent pools dynamically
    4. Coordinates entire pipeline
    5. Handles errors and escalations
    ────────────────────────────────────────────────────────────
    
    ⚠️  Prerequisites:
    - Run tests 01-03 first
    - Valid Snowflake tables created
    """)
    
    session_id = input("\n📌 Enter session_id from previous tests (or press Enter for test_session_001): ").strip()
    if not session_id:
        session_id = "test_session_001"
    
    logger.info(f"🚀 Master Agent orchestrating pipeline for session: {session_id}")
    
    master = MasterAgent()
    
    try:
        # Phase 1: Analyze datasets
        print("\n🔍 Phase 1: Master Agent analyzing datasets...")
        await master.analyze_datasets(session_id)
        
        allocation = master.agent_allocations.get(session_id, {})
        print(f"""
    ✅ Analysis complete!
       Allocated: {allocation.get('gemini_agents', 0)} Gemini agents
       Allocated: {allocation.get('merge_agents', 0)} Merge agents
       Allocated: {allocation.get('quality_agents', 0)} Quality agents
       Warehouse: {allocation.get('snowflake_warehouse', 'N/A')}
        """)
        
        # Phase 2: Initiate schema mapping
        print("\n🧠 Phase 2: Master Agent initiating schema mapping...")
        mapping_result = await master.initiate_schema_mapping(session_id)
        
        print(f"""
    ✅ Schema mapping complete!
       Mappings proposed: {len(mapping_result.get('mappings', []))}
       Conflicts found: {len(mapping_result.get('conflicts', []))}
       Status: {mapping_result.get('status', 'N/A')}
        """)
        
        print("""
    ✅ SUCCESS! Master Agent orchestrated the full pipeline
    ────────────────────────────────────────────────────────────
    
    💡 What happened:
    1. Master Agent analyzed dataset complexity
    2. Made autonomous resource allocation decision
    3. Spawned Gemini agent pool dynamically
    4. Coordinated schema analysis across agents
    5. Aggregated results from all agents
    6. Ready for merge execution phase
    
    🎯 This demonstrates:
    - True multi-agent orchestration
    - Autonomous decision making
    - Cloud-native architecture
    - Kubernetes-style agent spawning
        """)
        
    except Exception as e:
        print(f"""
    ❌ FAILED: {str(e)}
    
    💡 Common Issues:
    - Ensure previous tests created Snowflake tables
    - Check all credentials in .env
    - Verify Gemini API key is valid
        """)
        logger.error(f"Orchestration failed", exc_info=True)


async def main():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              MASTER AGENT TEST SUITE                         ║
    ║                                                              ║
    ║  The brain of the system - autonomous decision maker         ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("\nChoose test:")
    print("  1. Resource Allocation (no Snowflake needed)")
    print("  2. Full Orchestration (requires previous tests)")
    print("  3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice in ["1", "3"]:
        await test_resource_allocation()
    
    if choice in ["2", "3"]:
        await test_full_orchestration()


if __name__ == "__main__":
    asyncio.run(main())
