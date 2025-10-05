#!/usr/bin/env python3
"""
TEST 6: Gemini Mapping Agent with A2A Communication
Tests the Mapping Agent's ability to autonomously fetch schemas and propose mappings
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

# Import agents (they auto-register)
from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
from agents.gemini.mapping_agent import GeminiMappingAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    print_header("GEMINI MAPPING AGENT TEST (WITH A2A)")
    
    print("""
📋 What this test does:
────────────────────────────────────────────────────────────
1. Initializes all required agents (auto-register with registry)
2. Ingests two CSV datasets to Snowflake
3. Mapping Agent AUTONOMOUSLY:
   • Calls Schema Reader Agent via A2A to fetch schemas
   • Uses Gemini to propose intelligent mappings
   • Returns confidence scores + reasoning
   • Identifies conflicts for Jira escalation
4. Demonstrates complete A2A collaboration!
────────────────────────────────────────────────────────────
""")
    
    # --- Initialize Agents ---
    logger.info("Initializing agents...")
    ingest_agent = SnowflakeIngestionAgent(agent_id="ingest_001")
    schema_agent = GeminiSchemaReaderAgent(agent_id="schema_001")
    mapping_agent = GeminiMappingAgent(agent_id="mapping_001")
    logger.info("✅ All agents initialized and registered.")
    
    # --- Display Registry Status ---
    print("\n✅ Agent Registry Status:")
    print("────────────────────────────────────────────────────────────")
    registry_info = agent_registry.get_registry_status()
    print(f"📦 Total Agents: {registry_info['total_agents']}")
    print(f"🛠️  Total Tools: {registry_info['total_tools']}")
    print("\nRegistered Agents:")
    for agent_id in registry_info['agents']:
        print(f"  • {agent_id}")
    print("\nCapabilities:")
    for cap, count in registry_info['capabilities'].items():
        print(f"  • {cap}: {count} tool(s)")
    print("────────────────────────────────────────────────────────────")
    
    # --- Step 1: Create and ingest test datasets ---
    print("\n📂 Step 1: Creating test datasets")
    print("────────────────────────────────────────────────────────────")
    
    uploads_dir = parent_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Dataset 1: Customer data (standard naming)
    dataset1_path = uploads_dir / "mapping_test_customers.csv"
    dataset1_content = """customer_id,customer_name,email_address,signup_date,total_purchases
1001,John Doe,john@example.com,2024-01-15,5000.00
1002,Jane Smith,jane@example.com,2024-02-20,3500.50
1003,Bob Johnson,bob@example.com,2024-03-10,7200.25
1004,Alice Williams,alice@example.com,2024-04-05,1200.00
1005,Charlie Brown,charlie@example.com,2024-05-12,9500.75"""
    
    dataset1_path.write_text(dataset1_content)
    logger.info(f"✅ Created dataset 1: {dataset1_path}")
    
    # Dataset 2: Client data (different naming conventions)
    dataset2_path = uploads_dir / "mapping_test_clients.csv"
    dataset2_content = """client_number,client_full_name,contact_email,registration_dt,purchase_amt,client_tier
C-1001,John Doe,JOHN@EXAMPLE.COM,2024-01-15,5000,Gold
C-1003,Bob Johnson,bob@EXAMPLE.com,2024-03-10,7200,Gold
C-1006,Diana Prince,diana@example.com,2024-06-01,15000,Platinum
C-1007,Ethan Hunt,ethan@example.com,2024-07-15,2500,Silver"""
    
    dataset2_path.write_text(dataset2_content)
    logger.info(f"✅ Created dataset 2: {dataset2_path}")
    
    print("""
📊 Dataset Comparison:
┌─────────────────────┬─────────────────────────┐
│ Dataset 1           │ Dataset 2               │
├─────────────────────┼─────────────────────────┤
│ customer_id         │ client_number           │
│ customer_name       │ client_full_name        │
│ email_address       │ contact_email           │
│ signup_date         │ registration_dt         │
│ total_purchases     │ purchase_amt            │
│                     │ client_tier (NEW)       │
└─────────────────────┴─────────────────────────┘

Expected Mappings:
• customer_id ↔ client_number (join key)
• customer_name ↔ client_full_name
• email_address ↔ contact_email
• signup_date ↔ registration_dt
• total_purchases ↔ purchase_amt
• client_tier: only in dataset 2
────────────────────────────────────────────────────────────
""")
    
    # --- Step 2: Ingest datasets to Snowflake ---
    print("\n📥 Step 2: Ingesting datasets to Snowflake")
    print("────────────────────────────────────────────────────────────")
    
    try:
        session_id = "mapping_test_session"
        
        result1 = await ingest_agent.ingest_file(
            file_path=str(dataset1_path),
            session_id=session_id,
            dataset_num=1
        )
        table1 = result1["table_name"]
        print(f"✅ Dataset 1 ingested to: {table1}")
        print(f"   • Rows: {result1['row_count']}")
        print(f"   • Columns: {result1['column_count']}")
        
        result2 = await ingest_agent.ingest_file(
            file_path=str(dataset2_path),
            session_id=session_id,
            dataset_num=2
        )
        table2 = result2["table_name"]
        print(f"✅ Dataset 2 ingested to: {table2}")
        print(f"   • Rows: {result2['row_count']}")
        print(f"   • Columns: {result2['column_count']}")
        
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        logger.error(f"Ingestion failed: {e}")
        return
    
    # --- Step 3: Mapping Agent proposes mappings (with A2A schema fetching) ---
    print("\n🔗 Step 3: Mapping Agent proposes mappings (A2A mode)")
    print("────────────────────────────────────────────────────────────")
    print("""
Watch how the Mapping Agent:
1. Discovers Schema Reader Agent in the registry
2. Calls it TWICE (once per table) via A2A
3. Gets schemas automatically
4. Uses Gemini to propose intelligent mappings
5. Returns confidence scores + reasoning

This is REAL agent collaboration! 🚀
────────────────────────────────────────────────────────────
""")
    
    try:
        # Call Mapping Agent - it will internally fetch schemas via A2A
        mapping_result = await mapping_agent.propose_mappings(
            table1=table1,
            table2=table2,
            confidence_threshold=70
        )
        
        print("\n✅ Mapping Agent completed!")
        print("────────────────────────────────────────────────────────────")
        print(f"Status: {mapping_result['status']}")
        print(f"Overall Confidence: {mapping_result['overall_confidence']:.1f}%")
        print(f"Requires Jira: {'YES ⚠️' if mapping_result['requires_jira'] else 'NO ✅'}")
        
        print(f"\n📋 Proposed Mappings ({len(mapping_result['mappings'])} total):")
        print("────────────────────────────────────────────────────────────")
        for i, mapping in enumerate(mapping_result['mappings'], 1):
            confidence_emoji = "🟢" if mapping['confidence'] >= 90 else "🟡" if mapping['confidence'] >= 70 else "🔴"
            print(f"\n{i}. {mapping['dataset_a_col']} ↔ {mapping['dataset_b_col']}")
            print(f"   Unified Name: {mapping['unified_name']}")
            print(f"   Confidence: {confidence_emoji} {mapping['confidence']}%")
            print(f"   Reasoning: {mapping['reasoning']}")
            if mapping.get('is_join_key'):
                print(f"   🔑 Potential JOIN KEY")
        
        if mapping_result['conflicts']:
            print(f"\n⚠️  Conflicts Detected ({len(mapping_result['conflicts'])} total):")
            print("────────────────────────────────────────────────────────────")
            for i, conflict in enumerate(mapping_result['conflicts'], 1):
                print(f"\n{i}. {conflict['dataset_a_col']} ↔ {conflict['dataset_b_col']}")
                print(f"   Issue: {conflict.get('issue', 'Low confidence')}")
                print(f"   Confidence: 🔴 {conflict['confidence']}%")
                print(f"   Requires Human Review: {'YES' if conflict.get('requires_human_review') else 'NO'}")
        
        print(f"\n📝 Next Steps:")
        print("────────────────────────────────────────────────────────────")
        for i, step in enumerate(mapping_result['next_steps'], 1):
            print(f"{i}. {step}")
        
        print("\n────────────────────────────────────────────────────────────")
        
    except Exception as e:
        print(f"❌ Mapping proposal failed: {e}")
        logger.error(f"Mapping proposal failed: {e}", exc_info=True)
        return
    
    # --- Summary ---
    print("\n═══════════════════════════════════════════════════════════")
    print("🎯 MAPPING AGENT TEST SUMMARY")
    print("═══════════════════════════════════════════════════════════")
    print("\n✅ Mapping Agent successfully:")
    print("   • Discovered Schema Reader Agent via registry")
    print("   • Fetched schemas autonomously (A2A calls)")
    print("   • Proposed intelligent mappings with confidence")
    print("   • Identified potential conflicts")
    print("   • Generated actionable next steps")
    print("\n✅ A2A Communication Flow:")
    print("   Mapping Agent → Schema Reader Agent (table 1)")
    print("   Mapping Agent → Schema Reader Agent (table 2)")
    print("   Mapping Agent → Gemini API (propose mappings)")
    print("\n🎉 This is how intelligent agents should collaborate!")
    print("═══════════════════════════════════════════════════════════")


if __name__ == "__main__":
    asyncio.run(main())
