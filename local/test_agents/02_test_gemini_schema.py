#!/usr/bin/env python3
"""
TEST 2: Gemini Schema Reader Agent
Tests schema reading and analysis using Gemini 2.0 Flash
"""
import asyncio
import sys
import logging
import json
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
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    print_header("GEMINI SCHEMA READER AGENT TEST")

    print("""
📋 What this agent does:
────────────────────────────────────────────────────────────
1. Reads table schema from Snowflake (from Ingestion Agent)
2. Uses Gemini 2.0 Flash to understand column semantics
3. Identifies data types, relationships, and quality issues
4. Proposes potential join keys
5. Suggests transformations and improvements
6. PROPOSES tools to use (does NOT execute them)
────────────────────────────────────────────────────────────
""")

    # This assumes you've already run 01_test_snowflake_ingestion.py
    table_name = "RAW_test_session_001_DATASET_1"
    
    logger.info(f"📊 Analyzing schema for table: {table_name}")
    logger.info("   (This table was created by the Ingestion Agent test)")

    # Test the agent
    result = await test_agent(
        GeminiSchemaReaderAgent,
        "Analyze table schema with Gemini",
        type="read_schema",
        table_name=table_name,
        include_sample=True,
        sample_size=10
    )

    if "error" not in result:
        print(f"""
✅ SUCCESS! Gemini analyzed the schema
────────────────────────────────────────────────────────────
📊 Table: {result.get('table_name')}
📋 Columns: {result.get('metadata', {}).get('column_count', 0)}
🔢 Sample Size: {result.get('metadata', {}).get('sample_size', 0)}

🤖 Gemini's Analysis:
────────────────────────────────────────────────────────────
{result.get('gemini_analysis', 'No analysis available')[:1200]}...

🛠️ Recommended Tools:
────────────────────────────────────────────────────────────
""")
        
        for tool in result.get('recommended_tools', []):
            print(f"  • {tool.get('tool')}: {tool.get('reason')}")
        
        if not result.get('recommended_tools'):
            print("  (No specific tools recommended)")
        
        print(f"""
📈 Confidence Score: {result.get('confidence', 0.0):.2f}

💾 Full Schema:
────────────────────────────────────────────────────────────
""")
        
        for col in result.get('schema', [])[:5]:  # Show first 5 columns
            nullable = "NULL" if col.get("nullable") == "Y" else "NOT NULL"
            print(f"  • {col.get('name')}: {col.get('type')} {nullable}")
        
        if len(result.get('schema', [])) > 5:
            print(f"  ... and {len(result.get('schema', [])) - 5} more columns")
        
        print("""
────────────────────────────────────────────────────────────
💡 Next Steps:
  1. Use the recommended tools to get more details
  2. Run SQL Generator Agent to create merge queries
  3. Run Conflict Detector Agent before merging datasets
────────────────────────────────────────────────────────────
""")
    else:
        print(f"""
❌ FAILED: {result['error']}
────────────────────────────────────────────────────────────
💡 Common Issues:
- Table doesn't exist (run 01_test_snowflake_ingestion.py first)
- Gemini API key not set in .env (GEMINI_API_KEY)
- Network/API issues with Gemini
────────────────────────────────────────────────────────────
""")

if __name__ == "__main__":
    asyncio.run(main())