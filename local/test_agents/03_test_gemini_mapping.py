#!/usr/bin/env python3
"""
TEST 3: Gemini Mapping Agent
Tests column mapping between two datasets using Gemini 2.5 Pro
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from test_harness import test_agent, print_header
from agents.gemini.mapping_agent import GeminiMappingAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    print_header("GEMINI MAPPING AGENT TEST")
    
    print("""
    📋 What this agent does:
    ────────────────────────────────────────────────────────────
    1. Receives schema analysis from 2 datasets
    2. Uses Gemini 2.5 Pro to propose column mappings
    3. Provides confidence scores (0-100) for each mapping
    4. Explains semantic reasoning
    5. Flags ambiguous mappings (confidence < 70%)
    6. Suggests unified column names
    7. Identifies required transformations
    ────────────────────────────────────────────────────────────
    
    ⚠️  Prerequisites:
    - Run tests 01 and 02 first for both datasets
    - Need schema analysis from both tables
    """)
    
    # Mock schema analyses (in real flow, these come from Schema Agent)
    schema_a = {
        "table_name": "RAW_test_session_001_DATASET_1",
        "domain": "CRM",
        "columns": [
            {"name": "cust_id", "type": "VARCHAR", "semantic_meaning": "Customer identifier"},
            {"name": "first_name", "type": "VARCHAR", "semantic_meaning": "Customer first name"},
            {"name": "last_name", "type": "VARCHAR", "semantic_meaning": "Customer last name"},
            {"name": "email_addr", "type": "VARCHAR", "semantic_meaning": "Customer email address"},
            {"name": "signup_dt", "type": "DATE", "semantic_meaning": "Customer registration date"}
        ],
        "primary_key": "cust_id",
        "potential_join_keys": ["cust_id", "email_addr"]
    }
    
    schema_b = {
        "table_name": "RAW_test_session_001_DATASET_2",
        "domain": "Client Management",
        "columns": [
            {"name": "customer_number", "type": "VARCHAR", "semantic_meaning": "Client identifier"},
            {"name": "contact_email", "type": "VARCHAR", "semantic_meaning": "Client email"},
            {"name": "full_name", "type": "VARCHAR", "semantic_meaning": "Client full name"},
            {"name": "registration_date", "type": "DATE", "semantic_meaning": "Client signup date"},
            {"name": "member_tier", "type": "VARCHAR", "semantic_meaning": "Client membership level"}
        ],
        "primary_key": "customer_number",
        "potential_join_keys": ["customer_number", "contact_email"]
    }
    
    logger.info(f"📊 Mapping schemas:")
    logger.info(f"   Dataset A: {len(schema_a['columns'])} columns")
    logger.info(f"   Dataset B: {len(schema_b['columns'])} columns")
    
    # Test the agent
    result = await test_agent(
        GeminiMappingAgent,
        "Propose mappings between Dataset A and Dataset B",
        type="propose_mappings",
        schema_a=schema_a,
        schema_b=schema_b,
        session_id="test_session_001"
    )
    
    if "error" not in result:
        mappings = result.get('mappings', [])
        conflicts = result.get('conflicts', [])
        
        print(f"""
    ✅ SUCCESS! Gemini proposed column mappings
    ────────────────────────────────────────────────────────────
    ✅ High Confidence Mappings: {len([m for m in mappings if m.get('confidence', 0) >= 90])}
    ⚠️  Medium Confidence:        {len([m for m in mappings if 70 <= m.get('confidence', 0) < 90])}
    ❌ Low Confidence (Conflicts): {len([m for m in mappings if m.get('confidence', 0) < 70])}
    🎫 Jira Escalations Needed:  {len(conflicts)}
    ────────────────────────────────────────────────────────────
    
    📝 Proposed Mappings:
        """)
        
        for mapping in mappings:
            conf = mapping.get('confidence', 0)
            icon = "✅" if conf >= 90 else "⚠️ " if conf >= 70 else "❌"
            
            print(f"""
    {icon} {mapping.get('dataset_a_col')} ↔ {mapping.get('dataset_b_col')}
       → Unified Name: {mapping.get('unified_name')}
       → Confidence: {conf}%
       → Reasoning: {mapping.get('reasoning', 'N/A')}
       → Transform: {mapping.get('transformation') or 'None'}
            """)
        
        if conflicts:
            print("\n    🎫 Conflicts requiring Jira escalation:")
            for conflict in conflicts:
                print(f"""
       • {conflict.get('dataset_a_col')} vs {conflict.get('dataset_b_col')}
         Issue: {conflict.get('issue')}
         Confidence: {conflict.get('confidence')}%
                """)
        
        print(f"""
    💡 Next Steps:
    - High confidence mappings can be auto-approved
    - Low confidence mappings trigger Jira ticket creation
    - User reviews and approves/modifies mappings
    - SQL Generator Agent uses approved mappings for merge
        """)
    else:
        print(f"""
    ❌ FAILED: {result.get('error')}
    
    💡 Common Issues:
    - Check GEMINI_API_KEY in .env
    - Verify Gemini 2.5 Pro model specified
    - Check API quota not exceeded
        """)


if __name__ == "__main__":
    asyncio.run(main())
