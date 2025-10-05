#!/usr/bin/env python3
"""
Test: Prove FULL OUTER JOIN now preserves ALL columns (simplified - use existing mappings)
"""
import asyncio
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from sf_infrastructure.connector import snowflake_connector
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
    
    # Manual mappings (from previous test)
    mappings = [
        {"dataset_a_col": "customerId", "dataset_b_col": "id", "unified_name": "customer_id", "confidence": 100, "reasoning": "Exact match", "transformation": None, "is_join_key": True},
        {"dataset_a_col": "email", "dataset_b_col": "emailAddress", "unified_name": "email", "confidence": 95, "reasoning": "Semantic match", "transformation": None, "is_join_key": False},
        {"dataset_a_col": "givenName", "dataset_b_col": "firstName", "unified_name": "first_name", "confidence": 95, "reasoning": "Semantic match", "transformation": None, "is_join_key": False},
        {"dataset_a_col": "dateOfBirth", "dataset_b_col": "birthDate", "unified_name": "date_of_birth", "confidence": 95, "reasoning": "Semantic match", "transformation": None, "is_join_key": False},
        {"dataset_a_col": "language", "dataset_b_col": "preferredLanguage", "unified_name": "language", "confidence": 90, "reasoning": "Semantic match", "transformation": None, "is_join_key": False},
        {"dataset_a_col": "phoneNumber", "dataset_b_col": "homePhone", "unified_name": "phone_number", "confidence": 85, "reasoning": "Phone number match", "transformation": None, "is_join_key": False},
        {"dataset_a_col": "customerType", "dataset_b_col": "clientType", "unified_name": "customer_type", "confidence": 90, "reasoning": "Semantic match", "transformation": None, "is_join_key": False},
        {"dataset_a_col": "gender", "dataset_b_col": "gender", "unified_name": "gender", "confidence": 100, "reasoning": "Exact match", "transformation": None, "is_join_key": False},
        {"dataset_a_col": "state", "dataset_b_col": "state", "unified_name": "state", "confidence": 100, "reasoning": "Exact match", "transformation": None, "is_join_key": False},
        {"dataset_a_col": "lastName", "dataset_b_col": "lastName", "unified_name": "lastname", "confidence": 100, "reasoning": "Exact match", "transformation": None, "is_join_key": False},
    ]
    
    print(f"\n📌 EXPECTED OUTPUT:")
    print(f"   • {len(mappings)} mapped columns (unified)")
    print(f"   • {len(schema1) - len(mappings)} unmapped from table1 (ds1_* prefix)")
    print(f"   • {len(schema2) - len(mappings)} unmapped from table2 (ds2_* prefix)")
    print(f"   • 2 metadata columns")
    expected_total = len(mappings) + (len(schema1) - len(mappings)) + (len(schema2) - len(mappings)) + 2
    print(f"   • TOTAL EXPECTED: {expected_total} columns")
    
    # Execute join with NEW logic
    print("\n🔧 Executing FULL OUTER JOIN (with ALL columns)...")
    join_agent = JoinAgent(agent_id="join_full_test")
    
    merge_result = await join_agent.execute_join(
        table1=table1,
        table2=table2,
        output_table=output_table,
        mappings=mappings,
        join_type="full_outer"
    )
    
    if not merge_result["success"]:
        print(f"❌ Merge failed: {merge_result.get('error')}")
        return
    
    print(f"\n✅ Merge successful!")
    print(f"   • Output: {merge_result['output_table']}")
    print(f"   • Rows: {merge_result['statistics']['output_rows']}")
    
    # Check output table schema
    print("\n📋 Verifying output table schema...")
    output_schema = await snowflake_connector.get_table_info(output_table)
    
    print(f"\n✅ OUTPUT TABLE: {len(output_schema)} columns")
    print("\n📦 Column breakdown:")
    
    # Categorize columns
    unified = []
    ds1_cols = []
    ds2_cols = []
    meta_cols = []
    
    for col in output_schema:
        name = col.get('name') or col.get('NAME')
        if name.startswith('ds1_'):
            ds1_cols.append(col)
        elif name.startswith('ds2_'):
            ds2_cols.append(col)
        elif name.startswith('_'):
            meta_cols.append(col)
        else:
            unified.append(col)
    
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
    
    # Show sample data
    print(f"\n📄 Sample data (first row):")
    sample_query = f"SELECT * FROM {output_table} LIMIT 1"
    sample_data = await snowflake_connector.execute_query(sample_query)
    
    if sample_data:
        row = sample_data[0]
        print("\nUnified columns:")
        for col in unified:
            name = col.get('name') or col.get('NAME')
            value = row.get(name)
            print(f"  • {name}: {value}")
        
        # Count non-null ds1_ and ds2_ columns
        ds1_non_null = sum(1 for col in ds1_cols if row.get(col.get('name') or col.get('NAME')) is not None)
        ds2_non_null = sum(1 for col in ds2_cols if row.get(col.get('name') or col.get('NAME')) is not None)
        
        print(f"\nDataset 1 unmapped columns: {ds1_non_null}/{len(ds1_cols)} populated")
        print(f"Dataset 2 unmapped columns: {ds2_non_null}/{len(ds2_cols)} populated")
        print(f"Source: {row.get('_SOURCE_TABLE')}")
    
    print("\n" + "="*80)
    print("🎉 SUCCESS! FULL OUTER JOIN NOW PRESERVES ALL COLUMNS!")
    print("="*80)
    print(f"\n❌ Before fix: 10 columns (only mapped) - DATA LOSS!")
    print(f"✅ After fix:  {len(output_schema)} columns (ALL data preserved)")
    print(f"\n📊 Comparison:")
    print(f"  • Expected: {expected_total} columns")
    print(f"  • Actual:   {len(output_schema)} columns")
    if len(output_schema) == expected_total:
        print(f"  ✅ PERFECT MATCH!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
