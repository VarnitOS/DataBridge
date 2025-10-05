#!/usr/bin/env python3
"""
Quick merge using already-ingested Snowflake tables
"""
import asyncio
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from sf_infrastructure.connector import snowflake_connector


async def main():
    print("🔍 Finding already-ingested tables...")
    
    # Find account tables
    accounts_query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = 'PUBLIC' 
    AND TABLE_NAME LIKE 'RAW_%accounts%'
    ORDER BY CREATED DESC
    LIMIT 5
    """
    
    account_tables = await snowflake_connector.execute_query(accounts_query)
    account_table_names = [row['TABLE_NAME'] for row in account_tables]
    
    print(f"✅ Found {len(account_table_names)} account tables")
    
    # Find transaction tables
    trans_query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = 'PUBLIC' 
    AND TABLE_NAME LIKE 'RAW_%transactions%'
    ORDER BY CREATED DESC
    LIMIT 5
    """
    
    trans_tables = await snowflake_connector.execute_query(trans_query)
    trans_table_names = [row['TABLE_NAME'] for row in trans_tables]
    
    print(f"✅ Found {len(trans_table_names)} transaction tables")
    
    if not account_table_names or not trans_table_names:
        print("\n❌ No tables found! Run ultimate_merge_fast.py first to ingest data.")
        return
    
    print("\n🚀 Merging accounts...")
    
    # Get all unique columns
    all_account_cols = set()
    for table in account_table_names:
        schema = await snowflake_connector.get_table_info(table)
        cols = [col.get('name') or col.get('NAME') for col in schema]
        all_account_cols.update(cols)
    
    # Build UNION ALL
    union_parts = []
    for table in account_table_names:
        schema = await snowflake_connector.get_table_info(table)
        table_cols = [col.get('name') or col.get('NAME') for col in schema]
        
        select_cols = []
        for col in sorted(all_account_cols):
            if col in table_cols:
                select_cols.append(f'"{col}"')
            else:
                select_cols.append(f'NULL AS "{col}"')
        
        select_cols.append(f"'{table}' AS \"_SOURCE\"")
        union_parts.append(f"SELECT {', '.join(select_cols)} FROM {table}")
    
    union_sql = "\nUNION ALL\n".join(union_parts)
    create_sql = f"CREATE OR REPLACE TABLE UNIFIED_ACCOUNTS AS\n{union_sql}"
    
    await snowflake_connector.execute_non_query(create_sql)
    account_count = await snowflake_connector.get_row_count("UNIFIED_ACCOUNTS")
    
    print(f"✅ UNIFIED_ACCOUNTS: {account_count:,} rows, {len(all_account_cols)+1} columns")
    
    # Merge transactions
    print("\n🚀 Merging transactions...")
    
    all_trans_cols = set()
    for table in trans_table_names:
        schema = await snowflake_connector.get_table_info(table)
        cols = [col.get('name') or col.get('NAME') for col in schema]
        all_trans_cols.update(cols)
    
    union_parts = []
    for table in trans_table_names:
        schema = await snowflake_connector.get_table_info(table)
        table_cols = [col.get('name') or col.get('NAME') for col in schema]
        
        select_cols = []
        for col in sorted(all_trans_cols):
            if col in table_cols:
                select_cols.append(f'"{col}"')
            else:
                select_cols.append(f'NULL AS "{col}"')
        
        select_cols.append(f"'{table}' AS \"_SOURCE\"")
        union_parts.append(f"SELECT {', '.join(select_cols)} FROM {table}")
    
    union_sql = "\nUNION ALL\n".join(union_parts)
    create_sql = f"CREATE OR REPLACE TABLE UNIFIED_TRANSACTIONS AS\n{union_sql}"
    
    await snowflake_connector.execute_non_query(create_sql)
    trans_count = await snowflake_connector.get_row_count("UNIFIED_TRANSACTIONS")
    
    print(f"✅ UNIFIED_TRANSACTIONS: {trans_count:,} rows, {len(all_trans_cols)+1} columns")
    
    print("\n" + "="*80)
    print("🎉 QUICK MERGE COMPLETE!")
    print("="*80)
    print(f"\n📊 Results:")
    print(f"   • UNIFIED_ACCOUNTS: {account_count:,} rows")
    print(f"   • UNIFIED_TRANSACTIONS: {trans_count:,} rows")
    print(f"\n💾 Query them:")
    print(f"   SELECT * FROM UNIFIED_ACCOUNTS LIMIT 10;")
    print(f"   SELECT * FROM UNIFIED_TRANSACTIONS LIMIT 10;")


if __name__ == "__main__":
    asyncio.run(main())
