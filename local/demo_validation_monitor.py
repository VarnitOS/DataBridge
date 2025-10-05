#!/usr/bin/env python3
"""
Demo: Validation Monitor Catching Issues
Shows the monitor detecting problems in real-time
"""
import asyncio
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from agents.quality.validation_monitor_agent import ValidationMonitorAgent
from sf_infrastructure.connector import snowflake_connector


async def create_bad_tables():
    """Create tables with issues for the monitor to catch"""
    
    print("="*80)
    print("🧪 CREATING TABLES WITH ISSUES")
    print("="*80)
    
    # Bad Table 1: Generic column names (c1, c2, c3...)
    print("\n📦 Creating table with generic column names...")
    bad_table1 = """
    CREATE OR REPLACE TABLE TEST_BAD_COLUMNS (
        c1 VARCHAR,
        c2 VARCHAR,
        c3 VARCHAR,
        c4 VARCHAR,
        c5 VARCHAR,
        c6 VARCHAR
    )
    """
    await snowflake_connector.execute_non_query(bad_table1)
    
    # Insert some data
    insert1 = """
    INSERT INTO TEST_BAD_COLUMNS VALUES 
    ('value1', 'value2', 'value3', 'value4', 'value5', 'value6')
    """
    await snowflake_connector.execute_non_query(insert1)
    print("✅ Created TEST_BAD_COLUMNS (generic c1, c2, c3...)")
    
    # Bad Table 2: Almost all NULL data
    print("\n📦 Creating table with NULL data...")
    bad_table2 = """
    CREATE OR REPLACE TABLE TEST_NULL_DATA (
        customer_id VARCHAR,
        name VARCHAR,
        email VARCHAR,
        phone VARCHAR,
        address VARCHAR
    )
    """
    await snowflake_connector.execute_non_query(bad_table2)
    
    # Insert mostly NULL data
    insert2 = """
    INSERT INTO TEST_NULL_DATA VALUES 
    (NULL, NULL, NULL, NULL, NULL),
    (NULL, NULL, NULL, NULL, NULL),
    (NULL, NULL, NULL, NULL, NULL),
    ('ID001', NULL, NULL, NULL, NULL)
    """
    await snowflake_connector.execute_non_query(insert2)
    print("✅ Created TEST_NULL_DATA (mostly NULL)")
    
    # Bad Table 3: Empty table
    print("\n📦 Creating empty table...")
    bad_table3 = """
    CREATE OR REPLACE TABLE TEST_EMPTY_TABLE (
        transaction_id VARCHAR,
        amount VARCHAR,
        date VARCHAR
    )
    """
    await snowflake_connector.execute_non_query(bad_table3)
    print("✅ Created TEST_EMPTY_TABLE (0 rows)")
    
    # Good Table: For comparison
    print("\n📦 Creating good table...")
    good_table = """
    CREATE OR REPLACE TABLE TEST_GOOD_TABLE (
        customer_id VARCHAR,
        customer_name VARCHAR,
        email_address VARCHAR
    )
    """
    await snowflake_connector.execute_non_query(good_table)
    
    insert_good = """
    INSERT INTO TEST_GOOD_TABLE VALUES 
    ('CUST001', 'John Doe', 'john@example.com'),
    ('CUST002', 'Jane Smith', 'jane@example.com'),
    ('CUST003', 'Bob Wilson', 'bob@example.com')
    """
    await snowflake_connector.execute_non_query(insert_good)
    print("✅ Created TEST_GOOD_TABLE (proper data)")


async def main():
    print("="*80)
    print("🔍 VALIDATION MONITOR DEMO")
    print("="*80)
    print("\nThis demo shows the Validation Monitor catching issues in real-time")
    print("Watch how it detects:")
    print("  • Generic column names (c1, c2, c3...)")
    print("  • NULL data")
    print("  • Empty tables")
    print("  • And approves good tables")
    print("="*80)
    
    # Create test tables
    await create_bad_tables()
    
    await asyncio.sleep(1)
    
    # Initialize Validation Monitor
    print("\n" + "="*80)
    print("🤖 STARTING VALIDATION MONITOR")
    print("="*80)
    monitor = ValidationMonitorAgent(agent_id="demo_monitor")
    print("✅ Monitor initialized and watching...\n")
    
    await asyncio.sleep(0.5)
    
    # Check each table
    tables_to_check = [
        "TEST_BAD_COLUMNS",
        "TEST_NULL_DATA",
        "TEST_EMPTY_TABLE",
        "TEST_GOOD_TABLE"
    ]
    
    print("="*80)
    print("🔍 RUNNING SANITY CHECKS")
    print("="*80)
    
    for table in tables_to_check:
        print(f"\n📊 Checking {table}...")
        result = await monitor.quick_sanity_check(table)
        
        if result.get("passed"):
            print(f"   ✅ PASSED")
        else:
            print(f"   ❌ FAILED")
        
        await asyncio.sleep(0.3)
    
    # Show summary
    print("\n" + "="*80)
    print("📊 VALIDATION MONITOR SUMMARY")
    print("="*80)
    
    summary = monitor.get_summary()
    print(f"\n📊 Tables checked: {summary['tables_checked']}")
    print(f"⚠️  Issues found: {summary['issues_found']}")
    
    if summary['issues_found'] > 0:
        print("\n" + "="*80)
        print("📋 DETAILED ISSUES REPORT")
        print("="*80)
        
        for item in summary['details']:
            print(f"\n🔴 Table: {item['table_name']}")
            print(f"   Rows: {item.get('row_count', 'N/A')}, Columns: {item.get('column_count', 'N/A')}")
            
            if item.get('issues'):
                print(f"\n   ❌ CRITICAL ISSUES:")
                for issue in item['issues']:
                    severity_emoji = "🔴" if issue['severity'] == "CRITICAL" else "❌"
                    print(f"      {severity_emoji} {issue['issue']}")
                    print(f"         {issue['details']}")
            
            if item.get('warnings'):
                print(f"\n   ⚠️  WARNINGS:")
                for warning in item['warnings']:
                    print(f"      ⚠️  {warning['issue']}")
                    print(f"         {warning['details']}")
    
    print("\n" + "="*80)
    print("🎉 DEMO COMPLETE")
    print("="*80)
    
    print("\n✅ What the Validation Monitor does:")
    print("   • Runs automatically in the background")
    print("   • Listens to agent communications via event bus")
    print("   • Catches obvious issues before they cause problems:")
    print("     - Generic column names (c1, c2...) → INFER_SCHEMA failure")
    print("     - NULL data → File loading issue")
    print("     - Empty tables → Upload failure")
    print("   • Doesn't block the pipeline, just raises warnings")
    print("   • Visible in the visualization at http://localhost:8001")
    
    print("\n💡 In production:")
    print("   The monitor runs silently alongside your pipeline")
    print("   When it detects issues, it can:")
    print("     • Send alerts")
    print("     • Create Jira tickets")
    print("     • Trigger rollback")
    print("     • Log to monitoring systems")
    
    print("\n🧹 Cleaning up test tables...")
    for table in tables_to_check:
        await snowflake_connector.execute_non_query(f"DROP TABLE IF EXISTS {table}")
    print("✅ Cleanup complete")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
