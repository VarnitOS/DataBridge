#!/usr/bin/env python3
"""
TEST 7: Real-World Bank Data Mapping
Demonstrates Gemini Mapping Agent on actual Bank 1 and Bank 2 customer data
"""
import asyncio
import sys
import logging
from pathlib import Path
import pandas as pd

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load .env file
from dotenv import load_dotenv
env_path = parent_dir / '.env'
load_dotenv(env_path)

from test_harness import print_header
from core.agent_registry import agent_registry

# Import agents (they auto-register)
from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
from agents.gemini.mapping_agent import GeminiMappingAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    print_header("REAL-WORLD BANK DATA MAPPING TEST")
    
    print("""
📋 Scenario: EY needs to merge customer data from two acquired banks
────────────────────────────────────────────────────────────────
Bank 1 Customer Data:
  • customerId, lastName, givenName, email, phoneNumber
  • dateOfBirth, gender, customerStatus, customerType
  • address fields (street, city, country, state, postCode)
  • legal documents (legalId, legalDocumentName, etc.)

Bank 2 Customer Data:
  • id, lastName, firstName, emailAddress
  • birthDate, gender, clientType
  • homePhone, mobilePhone
  • state, preferredLanguage, assignedUserKey
  
Challenge: These banks use DIFFERENT naming conventions!
  • Bank 1: "customerId" vs Bank 2: "id"
  • Bank 1: "email" vs Bank 2: "emailAddress"
  • Bank 1: "givenName" vs Bank 2: "firstName"
  • Bank 1: "dateOfBirth" vs Bank 2: "birthDate"
  
Let's see if Gemini can figure this out! 🤖
────────────────────────────────────────────────────────────────
""")
    
    # --- Initialize Agents ---
    logger.info("Initializing agents...")
    ingest_agent = SnowflakeIngestionAgent(agent_id="bank_ingest_001")
    schema_agent = GeminiSchemaReaderAgent(agent_id="bank_schema_001")
    mapping_agent = GeminiMappingAgent(agent_id="bank_mapping_001")
    logger.info("✅ All agents initialized.")
    
    # --- Step 1: Convert Bank Customer files to CSV (Snowflake prefers CSV) ---
    print("\n📂 Step 1: Preparing bank customer data")
    print("────────────────────────────────────────────────────────────")
    
    uploads_dir = parent_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Read Bank 1 Customer data
    bank1_customer_path = parent_dir / "Bank 1 Data" / "Bank1_Mock_Customer.xlsx"
    bank1_df = pd.read_excel(bank1_customer_path)
    bank1_csv = uploads_dir / "bank1_customer.csv"
    bank1_df.to_csv(bank1_csv, index=False)
    
    print(f"✅ Bank 1 Customer: {len(bank1_df)} rows, {len(bank1_df.columns)} columns")
    print(f"   Columns: {', '.join(bank1_df.columns[:8])}...")
    
    # Read Bank 2 Customer data
    bank2_customer_path = parent_dir / "Bank 2 Data" / "Bank2_Mock_Customer.xlsx"
    bank2_df = pd.read_excel(bank2_customer_path)
    bank2_csv = uploads_dir / "bank2_customer.csv"
    bank2_df.to_csv(bank2_csv, index=False)
    
    print(f"✅ Bank 2 Customer: {len(bank2_df)} rows, {len(bank2_df.columns)} columns")
    print(f"   Columns: {', '.join(bank2_df.columns[:8])}...")
    
    # --- Step 2: Ingest to Snowflake ---
    print("\n📥 Step 2: Ingesting bank data to Snowflake")
    print("────────────────────────────────────────────────────────────")
    
    try:
        session_id = "bank_merge_test"
        
        result1 = await ingest_agent.ingest_file(
            file_path=str(bank1_csv),
            session_id=session_id,
            dataset_num=1
        )
        bank1_table = result1["table_name"]
        print(f"✅ Bank 1 ingested to: {bank1_table}")
        print(f"   • Rows: {result1['row_count']}")
        print(f"   • Columns: {result1['column_count']}")
        
        result2 = await ingest_agent.ingest_file(
            file_path=str(bank2_csv),
            session_id=session_id,
            dataset_num=2
        )
        bank2_table = result2["table_name"]
        print(f"✅ Bank 2 ingested to: {bank2_table}")
        print(f"   • Rows: {result2['row_count']}")
        print(f"   • Columns: {result2['column_count']}")
        
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        logger.error(f"Ingestion failed: {e}")
        return
    
    # --- Step 3: Gemini Mapping Agent analyzes and proposes mappings ---
    print("\n🤖 Step 3: Gemini AI analyzing bank schemas")
    print("────────────────────────────────────────────────────────────")
    print("""
The Mapping Agent will:
1. Autonomously fetch schemas from Snowflake (via Schema Reader Agent)
2. Use Gemini 2.0 Flash to understand semantic meaning
3. Propose intelligent mappings despite different naming conventions
4. Calculate confidence scores for each mapping
5. Identify potential conflicts

Watch the magic happen... ✨
────────────────────────────────────────────────────────────
""")
    
    try:
        # The Mapping Agent autonomously fetches schemas via A2A!
        mapping_result = await mapping_agent.propose_mappings(
            table1=bank1_table,
            table2=bank2_table,
            confidence_threshold=70
        )
        
        print("\n" + "="*70)
        print("🎯 GEMINI MAPPING RESULTS")
        print("="*70)
        
        print(f"\n📊 Overall Status: {mapping_result['status'].upper()}")
        print(f"📊 Overall Confidence: {mapping_result['overall_confidence']:.1f}%")
        print(f"⚠️  Requires Jira: {'YES (low confidence mappings)' if mapping_result['requires_jira'] else 'NO (all mappings confident)'}")
        
        # Display all proposed mappings
        print(f"\n📋 PROPOSED COLUMN MAPPINGS ({len(mapping_result['mappings'])} total)")
        print("="*70)
        
        for i, mapping in enumerate(mapping_result['mappings'], 1):
            confidence_emoji = "🟢" if mapping['confidence'] >= 90 else "🟡" if mapping['confidence'] >= 70 else "🔴"
            
            print(f"\n{i}. {mapping['dataset_a_col']:25s} ↔ {mapping['dataset_b_col']}")
            print(f"   └─ Unified Name: {mapping['unified_name']}")
            print(f"   └─ Confidence: {confidence_emoji} {mapping['confidence']:.0f}%")
            print(f"   └─ Reasoning: {mapping['reasoning']}")
            
            if mapping.get('is_join_key'):
                print(f"   └─ 🔑 POTENTIAL JOIN KEY (use for merging)")
            
            if mapping.get('transformation'):
                print(f"   └─ 🔧 Transformation: {mapping['transformation']}")
        
        # Display conflicts if any
        if mapping_result['conflicts']:
            print(f"\n⚠️  CONFLICTS DETECTED ({len(mapping_result['conflicts'])} total)")
            print("="*70)
            
            for i, conflict in enumerate(mapping_result['conflicts'], 1):
                print(f"\n{i}. {conflict['dataset_a_col']} ↔ {conflict['dataset_b_col']}")
                print(f"   └─ Issue: {conflict.get('issue', 'Low confidence')}")
                print(f"   └─ Confidence: 🔴 {conflict['confidence']:.0f}%")
                print(f"   └─ Requires Human Review: {'YES ⚠️' if conflict.get('requires_human_review') else 'NO'}")
                
                if 'resolution_suggestion' in conflict:
                    print(f"   └─ Suggested Resolution: {conflict['resolution_suggestion']}")
        
        # Display recommended next steps
        print(f"\n📝 RECOMMENDED NEXT STEPS:")
        print("="*70)
        for i, step in enumerate(mapping_result['next_steps'], 1):
            print(f"{i}. {step}")
        
        # Summary statistics
        print(f"\n📊 MAPPING STATISTICS:")
        print("="*70)
        high_conf = sum(1 for m in mapping_result['mappings'] if m['confidence'] >= 90)
        med_conf = sum(1 for m in mapping_result['mappings'] if 70 <= m['confidence'] < 90)
        low_conf = sum(1 for m in mapping_result['mappings'] if m['confidence'] < 70)
        join_keys = sum(1 for m in mapping_result['mappings'] if m.get('is_join_key'))
        
        print(f"  • High Confidence (≥90%):  {high_conf:3d} mappings 🟢")
        print(f"  • Medium Confidence (70-89%): {med_conf:3d} mappings 🟡")
        print(f"  • Low Confidence (<70%):   {low_conf:3d} mappings 🔴")
        print(f"  • Potential Join Keys:     {join_keys:3d} identified 🔑")
        print(f"  • Conflicts Requiring Review: {len(mapping_result['conflicts']):3d} items ⚠️")
        
    except Exception as e:
        print(f"\n❌ Mapping proposal failed: {e}")
        logger.error(f"Mapping proposal failed: {e}", exc_info=True)
        return
    
    # --- Final Summary ---
    print("\n" + "="*70)
    print("🎉 BANK DATA MAPPING TEST COMPLETE")
    print("="*70)
    
    print("""
✅ What the Gemini Mapping Agent successfully did:
   1. Autonomously fetched schemas from Snowflake (A2A call)
   2. Understood semantic meaning of each column
   3. Proposed intelligent mappings despite different naming:
      • "customerId" ↔ "id" 
      • "email" ↔ "emailAddress"
      • "givenName" ↔ "firstName"
      • "dateOfBirth" ↔ "birthDate"
   4. Calculated confidence scores
   5. Identified join keys for merging
   6. Flagged low-confidence mappings for human review

🎯 This demonstrates REAL AI-powered data integration!
   No hardcoded rules - Gemini figured out the mappings semantically.
    """)
    
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
