#!/usr/bin/env python3
"""
Quick test: Just run mapping on the already-ingested bank tables
"""
import asyncio
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from agents.gemini.mapping_agent import GeminiMappingAgent
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent

async def main():
    print("="*70)
    print("🏦 BANK CUSTOMER DATA MAPPING - REAL-WORLD TEST")
    print("="*70)
    
    # Initialize agents
    schema_agent = GeminiSchemaReaderAgent(agent_id="bank_schema_001")
    mapping_agent = GeminiMappingAgent(agent_id="bank_mapping_001")
    
    # Use the existing tables
    table1 = "RAW_bank_merge_test_DATASET_1"
    table2 = "RAW_bank_merge_test_DATASET_2"
    
    print(f"\n📊 Analyzing:")
    print(f"  • Bank 1: {table1}")
    print(f"  • Bank 2: {table2}")
    print(f"\n🤖 Gemini Mapping Agent will autonomously:")
    print(f"  1. Fetch schemas via A2A")
    print(f"  2. Understand semantic meaning")
    print(f"  3. Propose intelligent mappings")
    print(f"\nProcessing...\n")
    
    # Run mapping
    result = await mapping_agent.propose_mappings(
        table1=table1,
        table2=table2,
        confidence_threshold=70
    )
    
    print("="*70)
    print("🎯 MAPPING RESULTS")
    print("="*70)
    
    print(f"\n📊 Overall Confidence: {result['overall_confidence']:.1f}%")
    print(f"📊 Status: {result['status'].upper()}")
    print(f"⚠️  Requires Jira: {result['requires_jira']}")
    
    print(f"\n📋 PROPOSED MAPPINGS ({len(result['mappings'])} total):")
    print("="*70)
    
    for i, m in enumerate(result['mappings'], 1):
        emoji = "🟢" if m['confidence'] >= 90 else "🟡" if m['confidence'] >= 70 else "🔴"
        print(f"\n{i}. {m['dataset_a_col']:22s} ↔ {m['dataset_b_col']}")
        print(f"   Unified: {m['unified_name']}")
        print(f"   {emoji} {m['confidence']:.0f}% - {m['reasoning']}")
        if m.get('is_join_key'):
            print(f"   🔑 JOIN KEY")
    
    if result['conflicts']:
        print(f"\n⚠️ CONFLICTS ({len(result['conflicts'])}):")
        print("="*70)
        for c in result['conflicts']:
            print(f"  • {c['dataset_a_col']} ↔ {c['dataset_b_col']}")
            print(f"    Issue: {c.get('issue')}")
    
    print("\n" + "="*70)
    print("🎉 COMPLETE!")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
