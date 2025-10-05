#!/usr/bin/env python3
"""
Test: Full Bank Data Merge using Join Agent
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
from sf_infrastructure.connector import snowflake_connector

async def main():
    print("="*70)
    print("🏦 BANK DATA MERGE TEST - FULL PIPELINE")
    print("="*70)
    
    # Initialize agents
    print("\n📦 Initializing agents...")
    schema_agent = GeminiSchemaReaderAgent(agent_id="schema_001")
    mapping_agent = GeminiMappingAgent(agent_id="mapping_001")
    join_agent = JoinAgent(agent_id="join_001")
    print("✅ All agents ready")
    
    # Use existing tables
    table1 = "RAW_bank_merge_test_DATASET_1"
    table2 = "RAW_bank_merge_test_DATASET_2"
    output_table = "MERGED_BANK_CUSTOMERS"
    
    print(f"\n📊 Source Tables:")
    print(f"  • Bank 1: {table1}")
    print(f"  • Bank 2: {table2}")
    
    # Get row counts
    count1 = await snowflake_connector.get_row_count(table1)
    count2 = await snowflake_connector.get_row_count(table2)
    print(f"\n📈 Input Data:")
    print(f"  • Bank 1: {count1:,} customers")
    print(f"  • Bank 2: {count2:,} customers")
    
    # Step 1: Get mappings
    print(f"\n🤖 Step 1: Mapping Agent analyzing schemas...")
    mapping_result = await mapping_agent.propose_mappings(
        table1=table1,
        table2=table2,
        confidence_threshold=70
    )
    
    print(f"✅ Found {len(mapping_result['mappings'])} mappings")
    print(f"   Overall confidence: {mapping_result['overall_confidence']:.1f}%")
    
    # Display mappings
    print(f"\n📋 Column Mappings:")
    for i, m in enumerate(mapping_result['mappings'][:5], 1):
        emoji = "🟢" if m['confidence'] >= 90 else "🟡"
        print(f"  {i}. {m['dataset_a_col']:18s} ↔ {m['dataset_b_col']:18s} {emoji} {m['confidence']:.0f}%")
    if len(mapping_result['mappings']) > 5:
        print(f"  ... and {len(mapping_result['mappings']) - 5} more")
    
    # Step 2: Execute merge
    print(f"\n🔧 Step 2: Join Agent executing merge...")
    merge_result = await join_agent.execute_join(
        table1=table1,
        table2=table2,
        output_table=output_table,
        mappings=mapping_result['mappings'],
        join_type="full_outer"
    )
    
    if merge_result["success"]:
        print(f"✅ MERGE SUCCESSFUL!")
        print(f"\n📊 Results:")
        print(f"  • Output Table: {output_table}")
        print(f"  • Total Rows: {merge_result['statistics']['output_rows']:,}")
        print(f"  • From Bank 1: {merge_result['statistics']['table1_rows']:,}")
        print(f"  • From Bank 2: {merge_result['statistics']['table2_rows']:,}")
        print(f"  • Mappings Applied: {merge_result['statistics']['mappings_applied']}")
        
        # Sample the merged data
        print(f"\n📝 Sample merged data (first 3 rows):")
        sample_query = f"SELECT * FROM {output_table} LIMIT 3"
        sample_data = await snowflake_connector.execute_query(sample_query)
        
        if sample_data:
            # Get column names
            cols = list(sample_data[0].keys())
            print(f"\n  Columns in merged table: {', '.join(cols[:5])}...")
            
            for i, row in enumerate(sample_data, 1):
                print(f"\n  Row {i}:")
                for col in cols[:8]:  # Show first 8 columns
                    value = str(row.get(col, 'NULL'))[:30]
                    print(f"    • {col}: {value}")
        
        print(f"\n🎉 BANK MERGE COMPLETE!")
        print(f"\nYou can now query the merged data:")
        print(f"  SELECT * FROM {output_table};")
        
    else:
        print(f"❌ MERGE FAILED: {merge_result.get('error')}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(main())
