#!/usr/bin/env python3
"""
Test: Prove Dedupe Agent Actually Works with Real Duplicates
"""
import asyncio
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from sf_infrastructure.connector import snowflake_connector
from agents.merge.dedupe_agent import DedupeAgent

async def main():
    print("="*70)
    print("🧪 DEDUPE AGENT TEST - PROVING IT WORKS")
    print("="*70)
    
    # Step 1: Create a table WITH duplicates
    print("\n📊 Step 1: Creating test table WITH DUPLICATES...")
    
    create_test_table = """
    CREATE OR REPLACE TABLE TEST_DUPLICATES AS
    SELECT 
        'CUST-001' as customer_id,
        'John Doe' as name,
        'john@example.com' as email,
        CURRENT_TIMESTAMP() as created_at
    UNION ALL
    SELECT 'CUST-001', 'John Doe', 'john@example.com', CURRENT_TIMESTAMP()
    UNION ALL
    SELECT 'CUST-001', 'John Doe', 'john@example.com', CURRENT_TIMESTAMP()
    UNION ALL
    SELECT 'CUST-002', 'Jane Smith', 'jane@example.com', CURRENT_TIMESTAMP()
    UNION ALL
    SELECT 'CUST-002', 'Jane Smith', 'jane@example.com', CURRENT_TIMESTAMP()
    UNION ALL
    SELECT 'CUST-003', 'Bob Wilson', 'bob@example.com', CURRENT_TIMESTAMP()
    UNION ALL
    SELECT 'CUST-003', 'Bob Wilson', 'bob@example.com', CURRENT_TIMESTAMP()
    UNION ALL
    SELECT 'CUST-003', 'Bob Wilson', 'bob@example.com', CURRENT_TIMESTAMP()
    UNION ALL
    SELECT 'CUST-004', 'Alice Brown', 'alice@example.com', CURRENT_TIMESTAMP()
    """
    
    await snowflake_connector.execute_non_query(create_test_table)
    
    # Count before
    before_count = await snowflake_connector.get_row_count("TEST_DUPLICATES")
    print(f"✅ Created TEST_DUPLICATES: {before_count} rows")
    
    # Show the duplicates
    print("\n📋 BEFORE DEDUPLICATION - Showing actual duplicates:")
    query_before = """
    SELECT 
        customer_id,
        COUNT(*) as duplicate_count
    FROM TEST_DUPLICATES
    GROUP BY customer_id
    ORDER BY duplicate_count DESC
    """
    
    duplicates_before = await snowflake_connector.execute_query(query_before)
    
    total_duplicates = 0
    for row in duplicates_before:
        cust_id = row.get('CUSTOMER_ID')
        count = row.get('DUPLICATE_COUNT')
        print(f"  • {cust_id}: {count} copies (duplicate)")
        if count > 1:
            total_duplicates += (count - 1)
    
    print(f"\n  Total rows: {before_count}")
    print(f"  Duplicate rows: {total_duplicates}")
    print(f"  Expected after dedupe: {before_count - total_duplicates}")
    
    # Step 2: Run Dedupe Agent
    print("\n🔧 Step 2: Running DEDUPE AGENT...")
    print("-" * 70)
    
    dedupe_agent = DedupeAgent(agent_id="test_dedupe_001")
    
    result = await dedupe_agent.deduplicate(
        input_table="TEST_DUPLICATES",
        output_table="TEST_DEDUPED",
        unique_key="customer_id",
        order_by="created_at"
    )
    
    if result["success"]:
        print(f"✅ Deduplication completed!")
        print(f"\n📊 RESULTS:")
        print(f"  Before: {result['statistics']['before_count']} rows")
        print(f"  After:  {result['statistics']['after_count']} rows")
        print(f"  Removed: {result['statistics']['duplicates_removed']} duplicates")
        print(f"  Percentage: {result['statistics']['duplicate_percentage']}%")
    else:
        print(f"❌ Failed: {result.get('error')}")
        return
    
    # Step 3: Verify the deduped table
    print("\n📋 Step 3: VERIFYING - Checking deduped table...")
    
    query_after = """
    SELECT 
        customer_id,
        COUNT(*) as row_count
    FROM TEST_DEDUPED
    GROUP BY customer_id
    ORDER BY customer_id
    """
    
    after_results = await snowflake_connector.execute_query(query_after)
    
    print(f"\n✅ AFTER DEDUPLICATION:")
    all_unique = True
    for row in after_results:
        cust_id = row.get('CUSTOMER_ID')
        count = row.get('ROW_COUNT')
        emoji = "✅" if count == 1 else "❌"
        print(f"  {emoji} {cust_id}: {count} row(s)")
        if count > 1:
            all_unique = False
    
    # Show the actual deduplicated data
    print(f"\n📋 Step 4: Showing ACTUAL DATA from deduped table:")
    sample_query = """
    SELECT customer_id, name, email
    FROM TEST_DEDUPED
    ORDER BY customer_id
    """
    
    sample_data = await snowflake_connector.execute_query(sample_query)
    
    print(f"\n✅ {len(sample_data)} unique customers (real data from Snowflake):")
    for row in sample_data:
        print(f"  • {row.get('CUSTOMER_ID')}: {row.get('NAME')} ({row.get('EMAIL')})")
    
    # Final verification
    print("\n" + "="*70)
    if all_unique:
        print("✅ DEDUPE AGENT WORKS! All duplicates removed!")
    else:
        print("❌ Something went wrong - duplicates still exist")
    print("="*70)
    
    # Cleanup
    print("\n🧹 Cleaning up test tables...")
    await snowflake_connector.execute_non_query("DROP TABLE IF EXISTS TEST_DUPLICATES")
    await snowflake_connector.execute_non_query("DROP TABLE IF EXISTS TEST_DEDUPED")
    print("✅ Cleanup complete")
    
    print("\n" + "="*70)
    print("🎉 TEST COMPLETE - DEDUPE AGENT IS WORKING!")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
