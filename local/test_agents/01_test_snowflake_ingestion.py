#!/usr/bin/env python3
"""
TEST 1: Snowflake Ingestion Agent
Tests uploading CSV to Snowflake and creating table
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load .env file
from dotenv import load_dotenv
env_path = parent_dir / '.env'
load_dotenv(env_path)

from test_harness import test_agent, print_header
from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    print_header("SNOWFLAKE INGESTION AGENT TEST")
    
    print("""
    📋 What this agent does:
    ────────────────────────────────────────────────────────────
    1. Takes a local CSV file
    2. Creates a Snowflake stage (temporary storage area)
    3. Uploads the file to the stage
    4. Uses Snowflake's INFER_SCHEMA to auto-detect column types
    5. Creates a table with the detected schema
    6. Loads data using COPY INTO
    7. Returns table name, row count, column count
    ────────────────────────────────────────────────────────────
    """)
    
    # Check if sample file exists
    sample_file = Path(__file__).parent.parent / "sample_dataset_1.csv"
    if not sample_file.exists():
        logger.error(f"❌ Sample file not found: {sample_file}")
        logger.info("Creating sample file...")
        
        sample_file.parent.mkdir(exist_ok=True)
        sample_file.write_text("""cust_id,first_name,last_name,email_addr,phone,signup_dt,account_status,total_orders
C001,John,Smith,john.smith@email.com,555-0101,2023-01-15,active,12
C002,Sarah,Johnson,sarah.j@email.com,555-0102,2023-02-20,active,8
C003,Michael,Brown,mbrown@email.com,555-0103,2023-03-10,inactive,3
C004,Emily,Davis,emily.davis@email.com,555-0104,2023-04-05,active,15
C005,David,Wilson,d.wilson@email.com,555-0105,2023-05-12,active,22""")
        
        logger.info(f"✅ Created sample file: {sample_file}")
    
    logger.info(f"📂 Using sample file: {sample_file}")
    logger.info(f"   File size: {sample_file.stat().st_size} bytes")
    
    # Test the agent
    result = await test_agent(
        SnowflakeIngestionAgent,
        "Ingest sample_dataset_1.csv to Snowflake",
        type="ingest_file",
        file_path=str(sample_file),
        session_id="test_session_001",
        dataset_num=1
    )
    
    if "error" not in result:
        print(f"""
    ✅ SUCCESS! Data ingested to Snowflake
    ────────────────────────────────────────────────────────────
    📊 Table Name:     {result.get('table_name')}
    📈 Rows Loaded:    {result.get('row_count')}
    📋 Column Count:   {result.get('column_count')}
    📦 Stage Name:     {result.get('stage_name')}
    ────────────────────────────────────────────────────────────
    
    💡 Next Steps:
    - This table is now in Snowflake
    - Ready for schema analysis by Gemini Agent
    - Can be queried, joined, merged
        """)
    else:
        print(f"""
    ❌ FAILED: {result.get('error')}
    
    💡 Common Issues:
    - Check .env file has correct Snowflake credentials
    - Ensure Snowflake warehouse is running
    - Verify user has CREATE TABLE privileges
        """)


if __name__ == "__main__":
    asyncio.run(main())
