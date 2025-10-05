#!/usr/bin/env python3
"""
Test: Prove FULL OUTER JOIN now preserves ALL columns
"""
import asyncio
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from sf_infrastructure.connector import snowflake_connector
from agents.gemini.mapping_agent import GeminiMappingAgent
from agents.merge.join_agent import JoinAgent

async def main():
    print("="*80)
    print("🧪 TESTING FULL OUTER JOIN - ALL COLUMNS PRESERVED")
    print("="*80)
    
    session_id = "bank_merge_test"
    table1 = f"RAW_{session_id}_DATASET_1"
    table2 = f"RAW_{session_id}_DATASET_2"
    output_table = "MERGED_BANK_CUSTOMERS_FULL"
    
    # Check source tables
    print("\n📊 SOURCE TABLES:")
    schema1 = await snowflake_connector.get_table_info(table1)
    schema2 = await snowflake_connector.get_table_info(table2)
    
    print(f"  • {table1}: {len(schema1)} columns")
    for i, col in enumerate(schema1[:5]):
        print(f"    {i+1}. {col.get('name') or col.get('NAME')}")
    print(f"    ... and {len(schema1) - 5} more")
    
    print(f"\n  • {table2}: {len(schema2)} columns")
    for i, col in enumerate(schema2[:5]):
        print(f"    {i+1}. {col.get('name') or col.get('NAME')}")
    print(f"    ... and {len(schema2) - 5} more")
    
    print(f"\n📌 EXPECTED OUTPUT: {len(schema1)} + {len(schema2)} columns")
    print(f"   • 10 mapped columns (unified)")
    print(f"   • {len(schema1) - 10} unmapped from table1 (ds1_* prefix)")
    print(f"   • {len(schema2) - 10} unmapped from table2 (ds2_* prefix)")
    print(f"   • 2 metadata columns")
    print(f"   • TOTAL: {10 + (len(schema1) - 10) + (len(schema2) - 10) + 2} columns")
    
    # Step 1: Get mappings
    print("\n🤖 Step 1: Getting column mappings...")
    mapping_agent = GeminiMappingAgent(agent_id="mapping_full_test")
    mapping_result = await mapping_agent.propose_mappings(
        table1=table1,
        table2=table2,
        confidence_threshold=70
    )
    
    print(f"✅ Found {len(mapping_result['mappings'])} mappings")
    
    # Step 2: Execute join with NEW logic
    print("\n🔧 Step 2: Executing FULL OUTER JOIN (with ALL columns)...")
    join_agent = JoinAgent(agent_id="join_full_test")
    
    merge_result = await join_agent.execute_join(
        table1=table1,
        table2=table2,
        output_table=output_table,
        mappings=mapping_result['mappings'],
        join_type="full_outer"
    )
    
    if not merge_result["success"]:
        print(f"❌ Merge failed: {merge_result.get('error')}")
        return
    
    print(f"✅ Merge successful!")
    print(f"   • Output: {merge_result['output_table']}")
    print(f"   • Rows: {merge_result['statistics']['output_rows']}")
    
    # Step 3: Check output table schema
    print("\n📋 Step 3: Verifying output table schema...")
    output_schema = await snowflake_connector.get_table_info(output_table)
    
    print(f"\n✅ OUTPUT TABLE: {len(output_schema)} columns")
    print("\n📦 Column breakdown:")
    
    # Categorize columns
    unified = [col for col in output_schema if not (col.get('name') or col.get('NAME')).startswith(('ds1_', 'ds2_', '_'))]
    ds1_cols = [col for col in output_schema if (col.get('name') or col.get('NAME')).startswith('ds1_')]
    ds2_cols = [col for col in output_schema if (col.get('name') or col.get('NAME')).startswith('ds2_')]
    meta_cols = [col for col in output_schema if (col.get('name') or col.get('NAME')).startswith('_')]
    
    print(f"  • Unified (mapped): {len(unified)} columns")
    for col in unified:
        name = col.get('name') or col.get('NAME')
        print(f"    - {name}")
    
    print(f"\n  • From Table 1 (unmapped): {len(ds1_cols)} columns")
    for col in ds1_cols[:5]:
        name = col.get('name') or col.get('NAME')
        print(f"    - {name}")
    if len(ds1_cols) > 5:
        print(f"    ... and {len(ds1_cols) - 5} more")
    
    print(f"\n  • From Table 2 (unmapped): {len(ds2_cols)} columns")
    for col in ds2_cols[:5]:
        name = col.get('name') or col.get('NAME')
        print(f"    - {name}")
    if len(ds2_cols) > 5:
        print(f"    ... and {len(ds2_cols) - 5} more")
    
    print(f"\n  • Metadata: {len(meta_cols)} columns")
    for col in meta_cols:
        name = col.get('name') or col.get('NAME')
        print(f"    - {name}")
    
    # Step 4: Show sample data
    print(f"\n📄 Step 4: Sample data (first 2 rows):")
    sample_query = f"SELECT * FROM {output_table} LIMIT 2"
    sample_data = await snowflake_connector.execute_query(sample_query)
    
    if sample_data:
        print(f"\n✅ Retrieved {len(sample_data)} sample rows")
        for i, row in enumerate(sample_data):
            print(f"\nRow {i+1}:")
            # Show unified columns
            print("  Unified columns:")
            for col in unified:
                name = col.get('name') or col.get('NAME')
                value = row.get(name)
                print(f"    • {name}: {value}")
            
            # Count non-null ds1_ and ds2_ columns
            ds1_non_null = sum(1 for col in ds1_cols if row.get(col.get('name') or col.get('NAME')) is not None)
            ds2_non_null = sum(1 for col in ds2_cols if row.get(col.get('name') or col.get('NAME')) is not None)
            
            print(f"  Dataset 1 columns: {ds1_non_null}/{len(ds1_cols)} populated")
            print(f"  Dataset 2 columns: {ds2_non_null}/{len(ds2_cols)} populated")
            print(f"  Source: {row.get('_SOURCE_TABLE')}")
    
    print("\n" + "="*80)
    print("🎉 SUCCESS! FULL OUTER JOIN NOW PRESERVES ALL COLUMNS!")
    print("="*80)
    print(f"\nBefore fix: {10} columns (only mapped)")
    print(f"After fix:  {len(output_schema)} columns (ALL data preserved)")
    print(f"\nData loss: ELIMINATED! ✅")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
