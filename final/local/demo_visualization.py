#!/usr/bin/env python3
"""
Demo: Agent Visualization
Runs a merge pipeline while the visualization server shows real-time communication
"""
import asyncio
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
from agents.gemini.mapping_agent import GeminiMappingAgent
from agents.merge.join_agent import JoinAgent
from agents.merge.dedupe_agent import DedupeAgent
from agents.quality.null_checker_agent import NullCheckerAgent
from agents.quality.duplicate_detector_agent import DuplicateDetectorAgent
from agents.quality.stats_agent import StatsAgent


async def run_demo_pipeline():
    """
    Run a complete merge pipeline that demonstrates agent communication
    """
    print("="*80)
    print("🎬 AGENT VISUALIZATION DEMO")
    print("="*80)
    print("\n📺 Open http://localhost:8001 to see the visualization!")
    print("\nInitializing agents...")
    
    # Initialize all agents (they will auto-register)
    ingest_agent = SnowflakeIngestionAgent(agent_id="ingest_001")
    schema_agent = GeminiSchemaReaderAgent(agent_id="schema_001")
    mapping_agent = GeminiMappingAgent(agent_id="mapping_001")
    join_agent = JoinAgent(agent_id="join_001")
    dedupe_agent = DedupeAgent(agent_id="dedupe_001")
    null_checker = NullCheckerAgent(agent_id="null_001")
    duplicate_detector = DuplicateDetectorAgent(agent_id="duplicate_001")
    stats_agent = StatsAgent(agent_id="stats_001")
    
    print("✅ All agents initialized and registered")
    
    await asyncio.sleep(2)  # Give time for UI to update
    
    print("\n🚀 Starting merge pipeline...")
    print("   Watch the visualization to see agents communicating!\n")
    
    # Use pre-ingested bank data
    session_id = "bank_merge_test"
    table1 = f"RAW_{session_id}_DATASET_1"
    table2 = f"RAW_{session_id}_DATASET_2"
    output_table = "MERGED_BANK_CUSTOMERS_DEMO"
    
    # Step 1: Mapping Agent calls Schema Reader (A2A)
    print("📊 Step 1: Mapping Agent analyzing schemas (calls Schema Reader Agent)...")
    mapping_result = await mapping_agent.propose_mappings(
        table1=table1,
        table2=table2,
        confidence_threshold=70
    )
    print(f"✅ Found {len(mapping_result['mappings'])} mappings")
    
    await asyncio.sleep(1)
    
    # Step 2: Join Agent merges data
    print("\n🔗 Step 2: Join Agent merging datasets...")
    merge_result = await join_agent.execute_join(
        table1=table1,
        table2=table2,
        output_table=output_table,
        mappings=mapping_result['mappings'],
        join_type="full_outer"
    )
    print(f"✅ Merged {merge_result['statistics']['output_rows']} rows")
    
    await asyncio.sleep(1)
    
    # Step 3: Quality Agents validate
    print("\n🔍 Step 3: Quality Agents validating data...")
    
    null_check = await null_checker.check_null_values(
        table_name=output_table,
        columns=[],
        null_percentage_threshold=10.0
    )
    print(f"✅ Null Check: {null_check['summary']['total_columns']} columns checked")
    
    await asyncio.sleep(0.5)
    
    duplicate_check = await duplicate_detector.detect_duplicates(
        table_name=output_table,
        unique_keys=["customer_id"]
    )
    print(f"✅ Duplicate Check: {duplicate_check['summary']['duplicate_count']} duplicates found")
    
    await asyncio.sleep(0.5)
    
    stats_check = await stats_agent.profile_table(
        table_name=output_table
    )
    print(f"✅ Stats: {stats_check['basic_stats']['total_rows']} rows profiled")
    
    print("\n" + "="*80)
    print("🎉 DEMO COMPLETE!")
    print("="*80)
    print("\n📺 Check the visualization at http://localhost:8001")
    print("   You should see:")
    print("   • All agents displayed as nodes")
    print("   • Green flowing particles when agents communicate")
    print("   • Event log showing all A2A calls")
    print("   • Real-time statistics")
    print("\n💡 Keep this running and run the demo again to see more flows!")
    print("="*80)


async def main():
    print("\n🎬 Starting demo in 3 seconds...")
    print("   Make sure visualization server is running!")
    print("   Run: python3 visualization_server.py\n")
    
    await asyncio.sleep(3)
    
    try:
        await run_demo_pipeline()
        
        # Keep running to show continuous monitoring
        print("\n⏳ Keeping demo running for continuous monitoring...")
        print("   Press Ctrl+C to exit\n")
        
        while True:
            await asyncio.sleep(10)
            # Optionally run small checks to keep showing activity
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped!")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
