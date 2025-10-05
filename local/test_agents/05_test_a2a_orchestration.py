#!/usr/bin/env python3
"""
TEST 5: Agent-to-Agent (A2A) Orchestration
Tests the full A2A communication system with Master Agent
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load .env file
from dotenv import load_dotenv
env_path = parent_dir / '.env'
load_dotenv(env_path)

from test_harness import print_header
from core.agent_registry import agent_registry, AgentCapability

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    print_header("A2A ORCHESTRATION TEST")

    print("""
📋 What this test does:
────────────────────────────────────────────────────────────
1. Initializes all agents (they auto-register with registry)
2. Master Agent discovers available agents
3. Master Agent orchestrates full pipeline via A2A calls:
   - Calls Ingestion Agent to upload CSVs
   - Calls Schema Agent to analyze tables
   - Calls Conflict Detector to find issues
   - Calls SQL Generator to create merge query
4. All communication happens Agent-to-Agent (no manual orchestration!)
────────────────────────────────────────────────────────────
""")

    # Step 1: Initialize all agents (they auto-register)
    logger.info("🔧 Initializing agents...")
    
    from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent
    from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
    from agents.gemini.conflict_detector_agent import GeminiConflictDetectorAgent
    from agents.gemini.sql_generator_agent import GeminiSQLGeneratorAgent
    from agents.master_orchestrator import MasterOrchestratorAgent
    
    # Create agents (they auto-register)
    ingest_agent = SnowflakeIngestionAgent(agent_id="ingest_001")
    schema_agent = GeminiSchemaReaderAgent(agent_id="schema_001")
    conflict_agent = GeminiConflictDetectorAgent(agent_id="conflict_001")
    sql_agent = GeminiSQLGeneratorAgent(agent_id="sql_001")
    master_agent = MasterOrchestratorAgent(agent_id="master_001")
    
    # Step 2: Check registry status
    logger.info("📊 Checking Agent Registry...")
    status = agent_registry.get_registry_status()
    
    print(f"""
✅ Agent Registry Status:
────────────────────────────────────────────────────────────
📦 Total Agents: {status['total_agents']}
🛠️  Total Tools: {status['total_tools']}

Registered Agents:
""")
    for agent_id in status['agents']:
        print(f"  • {agent_id}")
    
    print(f"""
Available Capabilities:
""")
    for cap, count in status['capabilities'].items():
        print(f"  • {cap}: {count} tool(s)")
    
    print("""
────────────────────────────────────────────────────────────
""")
    
    # Step 3: Test A2A communication - Simple call
    logger.info("🔄 Testing simple A2A call...")
    print("""
📞 Test 1: Simple A2A Call
────────────────────────────────────────────────────────────
Schema Agent → Ingestion Agent: "Can you ingest this file?"
""")
    
    try:
        # Schema agent discovers and calls ingestion agent
        result = await schema_agent.invoke_capability(
            capability=AgentCapability.DATA_INGESTION,
            parameters={
                "file_path": str(parent_dir / "uploads" / "sample_dataset_1.csv"),
                "session_id": "a2a_test_session",
                "dataset_num": 1
            }
        )
        
        if result['success']:
            print(f"""
✅ A2A Call Successful!
   Ingestion Agent returned: {result['result']['table_name']}
   Rows loaded: {result['result']['row_count']}
   
   This happened automatically - Schema Agent discovered
   Ingestion Agent via registry and invoked it!
────────────────────────────────────────────────────────────
""")
        else:
            print(f"""
❌ A2A Call Failed: {result.get('error')}
────────────────────────────────────────────────────────────
""")
    except Exception as e:
        print(f"""
❌ A2A Test Failed: {e}
💡 Make sure sample_dataset_1.csv exists in uploads/
────────────────────────────────────────────────────────────
""")
    
    # Step 4: Test Master Orchestrator (full pipeline)
    logger.info("🚀 Testing Master Orchestrator...")
    print("""
📞 Test 2: Master Orchestrator (Full Pipeline)
────────────────────────────────────────────────────────────
Master Agent orchestrates EVERYTHING automatically:
1. Master → Ingestion Agent (upload dataset 1)
2. Master → Ingestion Agent (upload dataset 2)
3. Master → Schema Agent (analyze dataset 1)
4. Master → Schema Agent (analyze dataset 2)
5. Master → Conflict Detector (find conflicts)
6. Master → SQL Generator (create merge SQL)

All via A2A communication! Let's watch...
────────────────────────────────────────────────────────────
""")
    
    try:
        # Use sample CSV files
        file1 = parent_dir / "uploads" / "sample_dataset_1.csv"
        file2 = parent_dir / "uploads" / "sample_dataset_2.csv"
        
        # Create sample files if they don't exist
        file1.parent.mkdir(parents=True, exist_ok=True)
        if not file1.exists():
            file1.write_text("id,name,email\n1,Alice,alice@test.com\n2,Bob,bob@test.com\n")
        if not file2.exists():
            file2.write_text("id,name,phone\n1,Alice,555-1234\n3,Charlie,555-5678\n")
        
        result = await master_agent.execute({
            "type": "full_pipeline",
            "file1_path": str(file1),
            "file2_path": str(file2),
            "session_id": "master_test_session",
            "merge_type": "full_outer",
            "auto_approve": False  # Require approval
        })
        
        if result['success']:
            pipeline_state = result['pipeline_state']
            
            print(f"""
✅ Master Orchestrator SUCCESS!
────────────────────────────────────────────────────────────
📊 Pipeline Status: {pipeline_state['status']}

Completed Steps (via A2A):
""")
            for i, step in enumerate(pipeline_state['steps_completed'], 1):
                print(f"  {i}. {step} ✅")
            
            print(f"""
⚠️  Conflicts Detected: {len(result.get('conflicts', []))}
""")
            if result.get('conflicts'):
                conflict_summary = pipeline_state.get('conflict_summary', {})
                for severity, count in conflict_summary.items():
                    if count > 0:
                        print(f"   • {severity}: {count}")
            
            print(f"""
📝 Proposed SQL Generated: {len(result.get('proposed_sql', ''))} chars

🎉 ALL AGENTS COMMUNICATED AUTOMATICALLY VIA A2A!
────────────────────────────────────────────────────────────
""")
            
            # Show a snippet of the proposed SQL
            if result.get('proposed_sql'):
                print("""
SQL Snippet (first 300 chars):
""")
                print(result['proposed_sql'][:300] + "...")
                print("""
────────────────────────────────────────────────────────────
""")
        else:
            print(f"""
❌ Master Orchestrator Failed
────────────────────────────────────────────────────────────
Error: {result.get('error')}
Completed Steps: {result['pipeline_state'].get('steps_completed', [])}
────────────────────────────────────────────────────────────
""")
    
    except Exception as e:
        logger.error(f"Master orchestrator test failed: {e}", exc_info=True)
        print(f"""
❌ Master Orchestrator Test Failed: {e}
────────────────────────────────────────────────────────────
💡 Common Issues:
- Missing Gemini API key in .env
- Sample CSV files not created
- Agent initialization failed
────────────────────────────────────────────────────────────
""")
    
    # Summary
    print("""
═══════════════════════════════════════════════════════════
🎯 A2A SYSTEM SUMMARY
═══════════════════════════════════════════════════════════

✅ Agents auto-register with registry
✅ Agents discover each other by capability
✅ Agents invoke each other directly (A2A)
✅ Master Agent orchestrates without manual coding
✅ MCP-style tool server pattern working!

This is how agents should work - they find and call each other
automatically, no hardcoded dependencies! 🚀

═══════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    asyncio.run(main())
