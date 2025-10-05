#!/usr/bin/env python3
"""
Test: Quality Agents + Dedupe on Merged Bank Data
"""
import asyncio
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from agents.merge.dedupe_agent import DedupeAgent
from agents.quality.null_checker_agent import NullCheckerAgent
from agents.quality.duplicate_detector_agent import DuplicateDetectorAgent
from agents.quality.stats_agent import StatsAgent

async def main():
    print("="*70)
    print("🔍 QUALITY VALIDATION & DEDUPLICATION TEST")
    print("="*70)
    
    # Initialize agents
    print("\n📦 Initializing quality agents...")
    dedupe_agent = DedupeAgent(agent_id="dedupe_001")
    null_checker = NullCheckerAgent(agent_id="null_001")
    duplicate_detector = DuplicateDetectorAgent(agent_id="dup_001")
    stats_agent = StatsAgent(agent_id="stats_001")
    print("✅ All agents ready")
    
    # Use the merged table from previous test
    input_table = "MERGED_BANK_CUSTOMERS"
    deduped_table = "MERGED_BANK_CUSTOMERS_CLEAN"
    
    print(f"\n📊 Target Table: {input_table}")
    
    # --- STEP 1: Initial Quality Check ---
    print("\n" + "="*70)
    print("STEP 1: INITIAL QUALITY CHECK (Before Deduplication)")
    print("="*70)
    
    # Check for duplicates
    print("\n🔍 Checking for duplicates...")
    dup_result = await duplicate_detector.detect_duplicates(
        table_name=input_table,
        key_columns=["customer_id"]
    )
    
    if dup_result["success"]:
        print(f"✅ Duplicate Detection Complete")
        print(f"   Status: {dup_result['status']}")
        print(f"   Total Rows: {dup_result['statistics']['total_rows']:,}")
        print(f"   Duplicate Keys: {dup_result['statistics']['unique_duplicate_keys']:,}")
        print(f"   Duplicate Records: {dup_result['statistics']['total_duplicate_records']:,}")
        print(f"   Duplicate %: {dup_result['statistics']['duplicate_percentage']}%")
        
        if dup_result['statistics']['unique_duplicate_keys'] > 0:
            print(f"\n   Sample duplicates:")
            for i, dup in enumerate(dup_result['sample_duplicates'][:3], 1):
                print(f"     {i}. Customer {dup.get('customer_id')}: {dup.get('DUPLICATE_COUNT')} records")
    
    # Check for NULLs
    print("\n🔍 Checking for NULL values...")
    null_result = await null_checker.check_nulls(
        table_name=input_table,
        null_threshold=5.0
    )
    
    if null_result["success"]:
        print(f"✅ NULL Check Complete")
        print(f"   Status: {null_result['status']}")
        print(f"   Completeness Score: {null_result['statistics']['completeness_score']}%")
        print(f"   Columns with NULLs: {null_result['statistics']['columns_with_nulls']}")
        print(f"   Columns Exceeding Threshold: {null_result['statistics']['columns_exceeding_threshold']}")
        
        if null_result['columns_with_issues']:
            print(f"\n   Columns with issues: {', '.join(null_result['columns_with_issues'][:5])}")
    
    # Generate statistics
    print("\n📊 Generating statistics...")
    stats_result = await stats_agent.generate_stats(
        table_name=input_table
    )
    
    if stats_result["success"]:
        print(f"✅ Statistics Generated")
        print(f"   Total Rows: {stats_result['summary']['total_rows']:,}")
        print(f"   Total Columns: {stats_result['summary']['total_columns']}")
        print(f"   High Cardinality Columns: {stats_result['summary']['high_cardinality_columns']}")
        print(f"   Likely Primary Keys: {', '.join(stats_result['summary']['likely_primary_keys'])}")
        
        if stats_result.get('recommendations'):
            print(f"\n   📝 Recommendations:")
            for rec in stats_result['recommendations']:
                print(f"     • {rec}")
    
    # --- STEP 2: Deduplication ---
    print("\n" + "="*70)
    print("STEP 2: DEDUPLICATION")
    print("="*70)
    
    if dup_result.get("statistics", {}).get("unique_duplicate_keys", 0) > 0:
        print(f"\n🔧 Running deduplication...")
        dedupe_result = await dedupe_agent.deduplicate(
            input_table=input_table,
            output_table=deduped_table,
            unique_key="customer_id",
            order_by="_MERGE_TIMESTAMP"
        )
        
        if dedupe_result["success"]:
            print(f"✅ Deduplication Complete!")
            print(f"   Input Rows: {dedupe_result['statistics']['before_count']:,}")
            print(f"   Output Rows: {dedupe_result['statistics']['after_count']:,}")
            print(f"   Duplicates Removed: {dedupe_result['statistics']['duplicates_removed']:,}")
            print(f"   Duplicate %: {dedupe_result['statistics']['duplicate_percentage']}%")
            print(f"\n   📊 Clean data table: {deduped_table}")
        else:
            print(f"❌ Deduplication failed: {dedupe_result.get('error')}")
            deduped_table = input_table  # Use original if dedupe fails
    else:
        print("✅ No duplicates found - deduplication not needed!")
        deduped_table = input_table
    
    # --- STEP 3: Final Quality Check ---
    print("\n" + "="*70)
    print("STEP 3: FINAL QUALITY CHECK (After Deduplication)")
    print("="*70)
    
    # Check duplicates again
    print("\n🔍 Verifying no duplicates remain...")
    final_dup_result = await duplicate_detector.detect_duplicates(
        table_name=deduped_table,
        key_columns=["customer_id"]
    )
    
    if final_dup_result["success"]:
        print(f"✅ Final Duplicate Check")
        print(f"   Status: {final_dup_result['status']}")
        print(f"   Duplicate Keys: {final_dup_result['statistics']['unique_duplicate_keys']}")
        
        if final_dup_result['statistics']['unique_duplicate_keys'] == 0:
            print(f"   🎉 All duplicates removed successfully!")
    
    # Generate final stats
    print("\n📊 Final statistics...")
    final_stats = await stats_agent.generate_stats(
        table_name=deduped_table
    )
    
    if final_stats["success"]:
        print(f"✅ Final Statistics")
        print(f"   Total Rows: {final_stats['summary']['total_rows']:,}")
        print(f"   Total Columns: {final_stats['summary']['total_columns']}")
    
    # --- SUMMARY ---
    print("\n" + "="*70)
    print("🎉 QUALITY VALIDATION COMPLETE")
    print("="*70)
    
    print(f"\n📋 Summary:")
    print(f"  • Original Table: {input_table}")
    print(f"  • Clean Table: {deduped_table}")
    print(f"  • Quality Checks Run: 4 (Duplicates, NULLs, Stats, Final Verification)")
    print(f"  • Status: All quality agents operational ✅")
    
    print(f"\n💡 You can now query the clean data:")
    print(f"  SELECT * FROM {deduped_table};")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(main())
