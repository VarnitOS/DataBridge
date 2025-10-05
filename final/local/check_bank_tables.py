#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from sf_infrastructure.connector import snowflake_connector

async def main():
    # Check what columns are actually in the tables
    schema1 = await snowflake_connector.get_table_info("RAW_bank_merge_test_DATASET_1")
    schema2 = await snowflake_connector.get_table_info("RAW_bank_merge_test_DATASET_2")
    
    print("Bank 1 Table Columns:")
    for col in schema1[:10]:
        print(f"  - {col.get('name') or col.get('NAME')}")
    
    print(f"\n... ({len(schema1)} total columns)\n")
    
    print("Bank 2 Table Columns:")
    for col in schema2[:10]:
        print(f"  - {col.get('name') or col.get('NAME')}")
    
    print(f"\n... ({len(schema2)} total columns)")

if __name__ == "__main__":
    asyncio.run(main())
