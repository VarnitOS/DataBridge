#!/usr/bin/env python3
"""
Fix Loan Transaction Ingestion
Properly ingest loan transactions with correct column names
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
from sf_infrastructure.stage_manager import StageManager


async def ingest_with_proper_headers(csv_path: Path, table_name: str, stage_name: str):
    """Ingest CSV with proper column names"""
    
    # Read CSV to get column names
    df = pd.read_csv(csv_path, nrows=0)  # Just get headers
    columns = df.columns.tolist()
    
    print(f"📋 Detected {len(columns)} columns:")
    for i, col in enumerate(columns[:8]):
        print(f"   {i+1}. {col}")
    if len(columns) > 8:
        print(f"   ... and {len(columns) - 8} more")
    
    # Create table with explicit schema (all VARCHAR for simplicity)
    col_definitions = ", ".join([f'"{col}" VARCHAR' for col in columns])
    create_sql = f"""
    CREATE OR REPLACE TABLE {table_name} (
        {col_definitions}
    )
    """
    
    print(f"\n📦 Creating table: {table_name}")
    await snowflake_connector.execute_non_query(create_sql)
    print("✅ Table created")
    
    # Upload file to stage
    stage_manager = StageManager(snowflake_connector)
    print(f"\n📤 Uploading {csv_path.name} to Snowflake...")
    await stage_manager.upload_file_to_stage(str(csv_path), stage_name)
    print("✅ File uploaded")
    
    # Load data with SKIP_HEADER = 1 (skip the header row in CSV)
    copy_sql = f"""
    COPY INTO {table_name}
    FROM {stage_name}
    FILE_FORMAT = (
        TYPE = 'CSV'
        SKIP_HEADER = 1
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        NULL_IF = ('NULL', 'null', '')
    )
    ON_ERROR = 'CONTINUE'
    """
    
    print(f"\n📥 Loading data into {table_name}...")
    await snowflake_connector.execute_non_query(copy_sql)
    
    # Get row count
    row_count = await snowflake_connector.get_row_count(table_name)
    print(f"✅ Loaded {row_count:,} rows")
    
    return {
        "table_name": table_name,
        "row_count": row_count,
        "columns": columns
    }


async def main():
    print("="*80)
    print("🔧 FIXING LOAN TRANSACTION INGESTION")
    print("="*80)
    
    session_id = "loan_merge_001"
    
    # Bank 1
    bank1_csv = parent_dir / "uploads" / "bank1_loan_transactions.csv"
    table1 = f"RAW_{session_id}_DATASET_1"
    stage1 = f"@EY_STAGE_{session_id}_1"
    
    # Bank 2
    bank2_csv = parent_dir / "uploads" / "bank2_loan_transactions.csv"
    table2 = f"RAW_{session_id}_DATASET_2"
    stage2 = f"@EY_STAGE_{session_id}_2"
    
    # Create stages
    stage_manager = StageManager(snowflake_connector)
    await stage_manager.create_session_stage(session_id, 1)
    await stage_manager.create_session_stage(session_id, 2)
    
    print("\n" + "="*80)
    print("📥 BANK 1 - Loan Transactions")
    print("="*80)
    result1 = await ingest_with_proper_headers(bank1_csv, table1, stage1)
    
    print("\n" + "="*80)
    print("📥 BANK 2 - Loan Transactions")
    print("="*80)
    result2 = await ingest_with_proper_headers(bank2_csv, table2, stage2)
    
    # Verify data
    print("\n" + "="*80)
    print("✅ VERIFICATION")
    print("="*80)
    
    print(f"\n📊 {table1}:")
    sample1 = await snowflake_connector.execute_query(f"SELECT * FROM {table1} LIMIT 3")
    for i, row in enumerate(sample1, 1):
        print(f"\n  Row {i}:")
        for key, value in list(row.items())[:5]:
            print(f"    • {key}: {value}")
    
    print(f"\n📊 {table2}:")
    sample2 = await snowflake_connector.execute_query(f"SELECT * FROM {table2} LIMIT 3")
    for i, row in enumerate(sample2, 1):
        print(f"\n  Row {i}:")
        for key, value in list(row.items())[:5]:
            print(f"    • {key}: {value}")
    
    print("\n" + "="*80)
    print("🎉 INGESTION FIXED!")
    print("="*80)
    print(f"\n✅ {table1}: {result1['row_count']:,} rows with proper column names")
    print(f"✅ {table2}: {result2['row_count']:,} rows with proper column names")
    print("\nNow run: python3 merge_loan_transactions.py")
    print("(It will use the existing tables with correct data!)")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
