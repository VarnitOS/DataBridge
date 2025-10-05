#!/usr/bin/env python3
"""
Fix: Manually create tables with proper column names from CSV headers
"""
import asyncio
import sys
from pathlib import Path
import pandas as pd

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from sf_infrastructure.connector import snowflake_connector

async def main():
    # Read the CSVs to get column names
    bank1_csv = parent_dir / "uploads" / "bank1_customer.csv"
    bank2_csv = parent_dir / "uploads" / "bank2_customer.csv"
    
    bank1_df = pd.read_csv(bank1_csv, nrows=1)
    bank2_df = pd.read_csv(bank2_csv, nrows=1)
    
    bank1_cols = list(bank1_df.columns)
    bank2_cols = list(bank2_df.columns)
    
    print(f"Bank 1 columns ({len(bank1_cols)}): {bank1_cols[:5]}...")
    print(f"Bank 2 columns ({len(bank2_cols)}): {bank2_cols[:5]}...")
    
    # Drop and recreate tables with correct schema
    table1 = "RAW_bank_merge_test_DATASET_1"
    table2 = "RAW_bank_merge_test_DATASET_2"
    
    # Create Bank 1 table
    bank1_schema = ", ".join([f'"{col}" VARCHAR' for col in bank1_cols])
    create1_sql = f"""
    CREATE OR REPLACE TABLE {table1} (
        {bank1_schema}
    )
    """
    
    print(f"\nCreating {table1}...")
    await snowflake_connector.execute_non_query(create1_sql)
    
    # Load data into Bank 1 table
    stage1 = "@EY_STAGE_bank_merge_test_1"
    copy1_sql = f"""
    COPY INTO {table1}
    FROM {stage1}
    FILE_FORMAT = (
        TYPE = 'CSV' 
        PARSE_HEADER = TRUE 
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    )
    ON_ERROR = 'CONTINUE'
    MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
    """
    
    print(f"Loading data into {table1}...")
    await snowflake_connector.execute_non_query(copy1_sql)
    
    # Create Bank 2 table
    bank2_schema = ", ".join([f'"{col}" VARCHAR' for col in bank2_cols])
    create2_sql = f"""
    CREATE OR REPLACE TABLE {table2} (
        {bank2_schema}
    )
    """
    
    print(f"\nCreating {table2}...")
    await snowflake_connector.execute_non_query(create2_sql)
    
    # Load data into Bank 2 table
    stage2 = "@EY_STAGE_bank_merge_test_2"
    copy2_sql = f"""
    COPY INTO {table2}
    FROM {stage2}
    FILE_FORMAT = (
        TYPE = 'CSV' 
        PARSE_HEADER = TRUE 
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    )
    ON_ERROR = 'CONTINUE'
    MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
    """
    
    print(f"Loading data into {table2}...")
    await snowflake_connector.execute_non_query(copy2_sql)
    
    # Verify
    schema1 = await snowflake_connector.get_table_info(table1)
    schema2 = await snowflake_connector.get_table_info(table2)
    
    print(f"\n✅ {table1} columns:")
    for col in schema1[:5]:
        print(f"  - {col.get('name') or col.get('NAME')}")
    print(f"  ... ({len(schema1)} total)")
    
    print(f"\n✅ {table2} columns:")
    for col in schema2[:5]:
        print(f"  - {col.get('name') or col.get('NAME')}")
    print(f"  ... ({len(schema2)} total)")
    
    print("\n🎉 Tables fixed! Now run the mapping test again.")

if __name__ == "__main__":
    asyncio.run(main())
