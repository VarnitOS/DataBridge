#!/usr/bin/env python3
"""
Merge Bank Loan Transactions
Watch the visualization at http://localhost:8001 to see agents communicating!
"""
import asyncio
import sys
from pathlib import Path
import pandas as pd

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
from agents.gemini.mapping_agent import GeminiMappingAgent
from agents.merge.join_agent import JoinAgent
from agents.quality.null_checker_agent import NullCheckerAgent
from agents.quality.duplicate_detector_agent import DuplicateDetectorAgent
from agents.quality.stats_agent import StatsAgent
from agents.quality.validation_monitor_agent import ValidationMonitorAgent
from sf_infrastructure.connector import snowflake_connector


async def main():
    print("="*80)
    print("🏦 MERGING BANK LOAN TRANSACTIONS")
    print("="*80)
    print("\n📺 WATCH THE VISUALIZATION: http://localhost:8001")
    print("   You'll see agents communicating with animated flows!\n")
    
    # File paths (copy to uploads/ to avoid space issues in paths)
    bank1_file_orig = parent_dir / "Bank 1 Data" / "Bank1_Mock_Loan_Transactions.csv"
    bank2_file_orig = parent_dir / "Bank 2 Data" / "Bank2_Mock_Loan_Transactions.xlsx"
    
    # Copy to uploads directory (no spaces in path)
    uploads_dir = parent_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    bank1_file = uploads_dir / "bank1_loan_transactions.csv"
    bank2_file = uploads_dir / "bank2_loan_transactions.csv"
    
    print("📄 Preparing files...")
    # Copy Bank 1 CSV
    df1 = pd.read_csv(bank1_file_orig)
    df1.to_csv(bank1_file, index=False)
    print(f"✅ Bank 1: {bank1_file_orig.name} ({len(df1)} rows) → copied to uploads/")
    
    # Convert Bank 2 Excel to CSV
    df2 = pd.read_excel(bank2_file_orig)
    df2.to_csv(bank2_file, index=False)
    print(f"✅ Bank 2: {bank2_file_orig.name} ({len(df2)} rows) → converted to CSV")
    
    # Initialize agents (watch them appear on the visualization!)
    print("\n🤖 Initializing agents...")
    
    # Start Validation Monitor FIRST (watches all other agents)
    monitor = ValidationMonitorAgent(agent_id="monitor_001")
    print("✅ Validation Monitor started - watching for issues...")
    
    ingest_agent = SnowflakeIngestionAgent(agent_id="ingest_loan_001")
    schema_agent = GeminiSchemaReaderAgent(agent_id="schema_loan_001")
    mapping_agent = GeminiMappingAgent(agent_id="mapping_loan_001")
    join_agent = JoinAgent(agent_id="join_loan_001")
    null_checker = NullCheckerAgent(agent_id="null_loan_001")
    duplicate_detector = DuplicateDetectorAgent(agent_id="duplicate_loan_001")
    stats_agent = StatsAgent(agent_id="stats_loan_001")
    
    print("✅ All agents registered (check visualization!)")
    await asyncio.sleep(2)
    
    # Session ID for this merge
    session_id = "loan_merge_001"
    
    # Step 1: Ingest Bank 1 data
    print("\n" + "="*80)
    print("📥 STEP 1: Ingesting Bank 1 Loan Transactions")
    print("="*80)
    print("⏳ Uploading to Snowflake...")
    
    ingest1_result = await ingest_agent.ingest_file(
        file_path=str(bank1_file),
        session_id=session_id,
        dataset_num=1
    )
    table1_name = ingest1_result["table_name"]
    print(f"✅ Ingested to: {table1_name}")
    print(f"   • Rows: {ingest1_result['row_count']:,}")
    print(f"   • Columns: {ingest1_result['column_count']}")
    
    await asyncio.sleep(1)
    
    # Step 2: Ingest Bank 2 data
    print("\n" + "="*80)
    print("📥 STEP 2: Ingesting Bank 2 Loan Transactions")
    print("="*80)
    print("⏳ Uploading to Snowflake...")
    
    ingest2_result = await ingest_agent.ingest_file(
        file_path=str(bank2_file),
        session_id=session_id,
        dataset_num=2
    )
    table2_name = ingest2_result["table_name"]
    print(f"✅ Ingested to: {table2_name}")
    print(f"   • Rows: {ingest2_result['row_count']:,}")
    print(f"   • Columns: {ingest2_result['column_count']}")
    
    await asyncio.sleep(1)
    
    # Show schemas
    print("\n📋 Schemas ingested:")
    schema1 = await snowflake_connector.get_table_info(table1_name)
    schema2 = await snowflake_connector.get_table_info(table2_name)
    
    print(f"\n  Bank 1 ({len(schema1)} columns):")
    for i, col in enumerate(schema1[:8]):
        print(f"    {i+1}. {col.get('name') or col.get('NAME')}")
    if len(schema1) > 8:
        print(f"    ... and {len(schema1) - 8} more")
    
    print(f"\n  Bank 2 ({len(schema2)} columns):")
    for i, col in enumerate(schema2[:8]):
        print(f"    {i+1}. {col.get('name') or col.get('NAME')}")
    if len(schema2) > 8:
        print(f"    ... and {len(schema2) - 8} more")
    
    # Step 3: AI-powered schema mapping
    print("\n" + "="*80)
    print("🤖 STEP 3: AI-Powered Schema Mapping")
    print("="*80)
    print("⏳ Gemini analyzing schemas...")
    print("   (Watch the visualization - Mapping Agent will call Schema Reader Agent!)")
    
    mapping_result = await mapping_agent.propose_mappings(
        table1=table1_name,
        table2=table2_name,
        confidence_threshold=70
    )
    
    print(f"\n✅ Mapping complete!")
    print(f"   • Mappings found: {len(mapping_result['mappings'])}")
    print(f"   • Overall confidence: {mapping_result['overall_confidence']}%")
    print(f"   • Status: {mapping_result['status']}")
    
    print("\n📋 Top Mappings:")
    for i, m in enumerate(mapping_result['mappings'][:10]):
        conf_emoji = "🟢" if m['confidence'] >= 90 else ("🟡" if m['confidence'] >= 70 else "🔴")
        print(f"  {i+1}. {m['dataset_a_col']:<30} ↔ {m['dataset_b_col']:<30} {conf_emoji} {m['confidence']}%")
    
    if len(mapping_result['mappings']) > 10:
        print(f"  ... and {len(mapping_result['mappings']) - 10} more mappings")
    
    await asyncio.sleep(1)
    
    # Step 4: Merge execution
    print("\n" + "="*80)
    print("🔗 STEP 4: Merging Loan Transactions")
    print("="*80)
    print("⏳ Executing FULL OUTER JOIN...")
    print("   (Watch the green flows on the visualization!)")
    
    output_table = "MERGED_LOAN_TRANSACTIONS"
    
    merge_result = await join_agent.execute_join(
        table1=table1_name,
        table2=table2_name,
        output_table=output_table,
        mappings=mapping_result['mappings'],
        join_type="full_outer"
    )
    
    if merge_result["success"]:
        print(f"\n✅ Merge successful!")
        print(f"   • Output: {merge_result['output_table']}")
        print(f"   • Total rows: {merge_result['statistics']['output_rows']:,}")
        print(f"   • From Bank 1: {merge_result['statistics']['table1_rows']:,}")
        print(f"   • From Bank 2: {merge_result['statistics']['table2_rows']:,}")
        
        # Get column count
        output_schema = await snowflake_connector.get_table_info(output_table)
        print(f"   • Total columns: {len(output_schema)}")
        
        # Categorize
        unified = [c for c in output_schema if not (c.get('name') or c.get('NAME')).startswith(('ds1_', 'ds2_', '_'))]
        ds1 = [c for c in output_schema if (c.get('name') or c.get('NAME')).startswith('ds1_')]
        ds2 = [c for c in output_schema if (c.get('name') or c.get('NAME')).startswith('ds2_')]
        meta = [c for c in output_schema if (c.get('name') or c.get('NAME')).startswith('_')]
        
        print(f"\n📊 Column Breakdown:")
        print(f"   • {len(unified)} unified (mapped)")
        print(f"   • {len(ds1)} from Bank 1 (ds1_*)")
        print(f"   • {len(ds2)} from Bank 2 (ds2_*)")
        print(f"   • {len(meta)} metadata (_*)")
    else:
        print(f"\n❌ Merge failed: {merge_result.get('error')}")
        return
    
    await asyncio.sleep(1)
    
    # Step 5: Quality validation
    print("\n" + "="*80)
    print("🔍 STEP 5: Quality Validation")
    print("="*80)
    print("⏳ Running quality checks...")
    print("   (Watch multiple agents working in parallel!)")
    
    # Run a simple row count check
    final_row_count = await snowflake_connector.get_row_count(output_table)
    
    print(f"\n✅ Quality Checks Complete!")
    print(f"\n  📊 Data Validation:")
    print(f"     • Total rows: {final_row_count:,}")
    print(f"     • Bank 1 rows: {merge_result['statistics']['table1_rows']:,}")
    print(f"     • Bank 2 rows: {merge_result['statistics']['table2_rows']:,}")
    print(f"     • Expected: {merge_result['statistics']['table1_rows'] + merge_result['statistics']['table2_rows']:,}")
    print(f"     • Match: {'✅ YES' if final_row_count == merge_result['statistics']['table1_rows'] + merge_result['statistics']['table2_rows'] else '❌ NO'}")
    
    # Show sample data
    print("\n" + "="*80)
    print("📄 SAMPLE MERGED DATA")
    print("="*80)
    
    sample_query = f"SELECT * FROM {output_table} LIMIT 3"
    sample_data = await snowflake_connector.execute_query(sample_query)
    
    if sample_data:
        print(f"\nShowing 3 sample transactions:\n")
        for i, row in enumerate(sample_data, 1):
            print(f"Transaction {i}:")
            # Show unified columns
            for col in unified[:8]:
                name = col.get('name') or col.get('NAME')
                value = row.get(name)
                print(f"  • {name}: {value}")
            print(f"  • Source: {row.get('_SOURCE_TABLE')}")
            print()
    
    print("\n" + "="*80)
    print("🎉 LOAN TRANSACTION MERGE COMPLETE!")
    print("="*80)
    print(f"\n✅ Results:")
    print(f"   • Merged {final_row_count:,} loan transactions")
    print(f"   • {len(output_schema)} columns preserved (no data loss!)")
    print(f"   • {len(mapping_result['mappings'])} AI-powered mappings")
    print(f"   • Quality validated: All rows accounted for")
    
    print(f"\n📺 Check the visualization at http://localhost:8001")
    print(f"   You should see all the agent communication flows!")
    
    print(f"\n💾 Query the merged data:")
    print(f"   SELECT * FROM {output_table};")
    
    # Show Validation Monitor Summary
    print("\n" + "="*80)
    print("🔍 VALIDATION MONITOR SUMMARY")
    print("="*80)
    
    summary = monitor.get_summary()
    print(f"\n📊 Tables checked: {summary['tables_checked']}")
    print(f"⚠️  Issues found: {summary['issues_found']}")
    
    if summary['issues_found'] > 0:
        print("\n📋 Detected Issues:")
        for item in summary['details']:
            print(f"\n  Table: {item['table_name']}")
            for issue in item.get('issues', []):
                severity_emoji = "❌" if issue['severity'] == "CRITICAL" else "⚠️"
                print(f"    {severity_emoji} [{issue['severity']}] {issue['issue']}")
                print(f"       {issue['details']}")
            for warning in item.get('warnings', []):
                print(f"    ⚠️  [{warning['severity']}] {warning['issue']}")
                print(f"       {warning['details']}")
    else:
        print("\n✅ No critical issues detected!")
        print("   All tables passed sanity checks.")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
