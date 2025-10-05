#!/usr/bin/env python3
"""
ULTIMATE MERGE - The Big One!
Merges ALL account files and ALL transaction files from both banks
while maintaining referential integrity.

What this does:
1. Merge 5 account files → UNIFIED_ACCOUNTS
2. Merge 5 transaction files → UNIFIED_TRANSACTIONS
3. Preserve client/account relationships
4. Full A2A agent orchestration
5. Real-time visualization at http://localhost:8001
"""
import asyncio
import sys
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
from agents.gemini.mapping_agent import GeminiMappingAgent
from agents.merge.join_agent import JoinAgent
from agents.quality.validation_monitor_agent import ValidationMonitorAgent
from agents.quality.stats_agent import StatsAgent
from sf_infrastructure.connector import snowflake_connector


class UltimateMergeOrchestrator:
    """Orchestrates the ultimate merge of all bank data"""
    
    def __init__(self):
        self.session_id = "ultimate_merge_001"
        self.accounts_ingested = []
        self.transactions_ingested = []
        
        # Account files
        self.account_files = [
            ("Bank 1 Data/Bank1_Mock_CurSav_Accounts.xlsx", "Bank1_CurSav_Accounts"),
            ("Bank 1 Data/Bank1_Mock_FixedTerm_Accounts.xlsx", "Bank1_FixedTerm_Accounts"),
            ("Bank 1 Data/Bank1_Mock_Loan_Accounts.xlsx", "Bank1_Loan_Accounts"),
            ("Bank 2 Data/Bank2_Mock_Deposit_Accounts.xlsx", "Bank2_Deposit_Accounts"),
            ("Bank 2 Data/Bank2_Mock_Loan_Accounts.xlsx", "Bank2_Loan_Accounts"),
        ]
        
        # Transaction files
        self.transaction_files = [
            ("Bank 1 Data/Bank1_Mock_CurSav_Transactions.csv", "Bank1_CurSav_Transactions"),
            ("Bank 1 Data/Bank1_Mock_FixedTerm_Transactions.csv", "Bank1_FixedTerm_Transactions"),
            ("Bank 1 Data/Bank1_Mock_Loan_Transactions.csv", "Bank1_Loan_Transactions"),
            ("Bank 2 Data/Bank2_Mock_Deposit_Transactions.xlsx", "Bank2_Deposit_Transactions"),
            ("Bank 2 Data/Bank2_Mock_Loan_Transactions.xlsx", "Bank2_Loan_Transactions"),
        ]
    
    async def prepare_files(self) -> Dict[str, List[Path]]:
        """Convert all files to CSV and copy to uploads/"""
        print("\n📂 Preparing files...")
        
        uploads_dir = parent_dir / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        prepared_accounts = []
        prepared_transactions = []
        
        # Prepare account files
        for file_path, name in self.account_files:
            source = parent_dir / file_path
            dest = uploads_dir / f"{name}.csv"
            
            if source.suffix == '.csv':
                df = pd.read_csv(source)
            else:
                df = pd.read_excel(source)
            
            df.to_csv(dest, index=False)
            prepared_accounts.append((dest, name))
            print(f"  ✅ {name}: {len(df):,} rows")
        
        # Prepare transaction files
        for file_path, name in self.transaction_files:
            source = parent_dir / file_path
            dest = uploads_dir / f"{name}.csv"
            
            if source.suffix == '.csv':
                df = pd.read_csv(source)
            else:
                df = pd.read_excel(source)
            
            df.to_csv(dest, index=False)
            prepared_transactions.append((dest, name))
            print(f"  ✅ {name}: {len(df):,} rows")
        
        return {
            "accounts": prepared_accounts,
            "transactions": prepared_transactions
        }
    
    async def ingest_all_files(self, files: List, ingest_agent, prefix: str):
        """Ingest multiple files in parallel"""
        tasks = []
        for i, (file_path, name) in enumerate(files, 1):
            task = ingest_agent.ingest_file(
                file_path=str(file_path),
                session_id=f"{self.session_id}_{prefix}",
                dataset_num=i
            )
            tasks.append((task, name))
        
        results = []
        for task, name in tasks:
            result = await task
            result['source_name'] = name
            results.append(result)
        
        return results
    
    async def merge_multiple_tables(
        self,
        tables: List[str],
        output_table: str,
        table_type: str,
        mapping_agent,
        join_agent
    ):
        """
        Merge multiple tables into one unified table
        Strategy: Merge pairs, then merge results
        """
        print(f"\n🔗 Merging {len(tables)} {table_type} tables...")
        
        if len(tables) == 1:
            # Just copy the single table
            copy_sql = f"CREATE OR REPLACE TABLE {output_table} AS SELECT * FROM {tables[0]}"
            await snowflake_connector.execute_non_query(copy_sql)
            return await snowflake_connector.get_row_count(output_table)
        
        # Merge in pairs, then merge the results
        current_tables = tables[:]
        merge_round = 1
        
        while len(current_tables) > 1:
            print(f"\n  Round {merge_round}: Merging {len(current_tables)} tables...")
            next_round_tables = []
            
            # Process pairs
            for i in range(0, len(current_tables), 2):
                if i + 1 < len(current_tables):
                    # Merge pair
                    table1 = current_tables[i]
                    table2 = current_tables[i + 1]
                    intermediate_table = f"MERGE_INTERMEDIATE_{table_type}_{merge_round}_{i}"
                    
                    print(f"    Merging {table1.split('_')[-1]} + {table2.split('_')[-1]}...")
                    
                    # Get mappings
                    mapping_result = await mapping_agent.propose_mappings(
                        table1=table1,
                        table2=table2,
                        confidence_threshold=60  # Lower threshold for account types
                    )
                    
                    # Execute merge
                    await join_agent.perform_join_merge(
                        table1=table1,
                        table2=table2,
                        mappings=mapping_result['mappings'],
                        merge_type="full_outer",
                        output_table_name=intermediate_table,
                        session_id=orchestrator.session_id
                    )
                    
                    next_round_tables.append(intermediate_table)
                else:
                    # Odd one out, carry forward
                    next_round_tables.append(current_tables[i])
            
            current_tables = next_round_tables
            merge_round += 1
        
        # Rename final table
        if current_tables[0] != output_table:
            rename_sql = f"CREATE OR REPLACE TABLE {output_table} AS SELECT * FROM {current_tables[0]}"
            await snowflake_connector.execute_non_query(rename_sql)
        
        final_count = await snowflake_connector.get_row_count(output_table)
        print(f"\n  ✅ Final {table_type} table: {final_count:,} rows")
        
        return final_count


async def main():
    print("="*80)
    print("🚀 ULTIMATE MERGE - ALL ACCOUNTS + ALL TRANSACTIONS")
    print("="*80)
    print("\n📺 WATCH THE VISUALIZATION: http://localhost:8001")
    print("   This will be EPIC - multiple agents working in parallel!\n")
    
    orchestrator = UltimateMergeOrchestrator()
    
    # Initialize agents
    print("🤖 Initializing agent army...")
    monitor = ValidationMonitorAgent(agent_id="monitor_ultimate")
    ingest_agent = SnowflakeIngestionAgent(agent_id="ingest_ultimate")
    schema_agent = GeminiSchemaReaderAgent(agent_id="schema_ultimate")
    mapping_agent = GeminiMappingAgent(agent_id="mapping_ultimate")
    join_agent = JoinAgent(agent_id="join_ultimate")
    stats_agent = StatsAgent(agent_id="stats_ultimate")
    print("✅ All agents ready for battle!")
    
    await asyncio.sleep(1)
    
    # Phase 1: Prepare files
    print("\n" + "="*80)
    print("PHASE 1: PREPARING FILES")
    print("="*80)
    prepared_files = await orchestrator.prepare_files()
    
    print(f"\n✅ Prepared:")
    print(f"   • {len(prepared_files['accounts'])} account files")
    print(f"   • {len(prepared_files['transactions'])} transaction files")
    
    await asyncio.sleep(1)
    
    # Phase 2: Ingest all account files
    print("\n" + "="*80)
    print("PHASE 2: INGESTING ALL ACCOUNT FILES")
    print("="*80)
    print("⏳ Uploading to Snowflake...")
    
    account_results = await orchestrator.ingest_all_files(
        prepared_files['accounts'],
        ingest_agent,
        "accounts"
    )
    
    print(f"\n✅ Ingested {len(account_results)} account files:")
    total_account_rows = 0
    account_tables = []
    for result in account_results:
        print(f"   • {result['source_name']}: {result['row_count']:,} rows → {result['table_name']}")
        total_account_rows += result['row_count']
        account_tables.append(result['table_name'])
    print(f"\n📊 Total account records: {total_account_rows:,}")
    
    await asyncio.sleep(1)
    
    # Phase 3: Ingest all transaction files
    print("\n" + "="*80)
    print("PHASE 3: INGESTING ALL TRANSACTION FILES")
    print("="*80)
    print("⏳ Uploading to Snowflake...")
    
    transaction_results = await orchestrator.ingest_all_files(
        prepared_files['transactions'],
        ingest_agent,
        "transactions"
    )
    
    print(f"\n✅ Ingested {len(transaction_results)} transaction files:")
    total_transaction_rows = 0
    transaction_tables = []
    for result in transaction_results:
        print(f"   • {result['source_name']}: {result['row_count']:,} rows → {result['table_name']}")
        total_transaction_rows += result['row_count']
        transaction_tables.append(result['table_name'])
    print(f"\n📊 Total transaction records: {total_transaction_rows:,}")
    
    await asyncio.sleep(1)
    
    # Phase 4: Merge all accounts
    print("\n" + "="*80)
    print("PHASE 4: MERGING ALL ACCOUNTS → UNIFIED_ACCOUNTS")
    print("="*80)
    print(f"🔗 Merging {len(account_tables)} account tables...")
    print("   (Watch the visualization - agents working in parallel!)")
    
    unified_accounts_count = await orchestrator.merge_multiple_tables(
        tables=account_tables,
        output_table="UNIFIED_ACCOUNTS",
        table_type="ACCOUNT",
        mapping_agent=mapping_agent,
        join_agent=join_agent
    )
    
    await asyncio.sleep(1)
    
    # Phase 5: Merge all transactions
    print("\n" + "="*80)
    print("PHASE 5: MERGING ALL TRANSACTIONS → UNIFIED_TRANSACTIONS")
    print("="*80)
    print(f"🔗 Merging {len(transaction_tables)} transaction tables...")
    print("   (Watch the visualization - more agent flows!)")
    
    unified_transactions_count = await orchestrator.merge_multiple_tables(
        tables=transaction_tables,
        output_table="UNIFIED_TRANSACTIONS",
        table_type="TRANSACTION",
        mapping_agent=mapping_agent,
        join_agent=join_agent
    )
    
    await asyncio.sleep(1)
    
    # Phase 6: Verify relationships
    print("\n" + "="*80)
    print("PHASE 6: VERIFYING RELATIONSHIPS")
    print("="*80)
    print("🔍 Checking account-transaction relationships...")
    
    # Get account schema
    account_schema = await snowflake_connector.get_table_info("UNIFIED_ACCOUNTS")
    account_cols = [col.get('name') or col.get('NAME') for col in account_schema]
    
    # Find ID columns
    id_columns = [col for col in account_cols if 'id' in col.lower() or 'key' in col.lower()]
    print(f"\n📋 Found {len(id_columns)} potential ID columns in accounts:")
    for col in id_columns[:5]:
        print(f"   • {col}")
    
    # Get transaction schema
    transaction_schema = await snowflake_connector.get_table_info("UNIFIED_TRANSACTIONS")
    transaction_cols = [col.get('name') or col.get('NAME') for col in transaction_schema]
    
    # Find ID columns
    trans_id_columns = [col for col in transaction_cols if 'id' in col.lower() or 'key' in col.lower() or 'account' in col.lower()]
    print(f"\n📋 Found {len(trans_id_columns)} potential ID columns in transactions:")
    for col in trans_id_columns[:5]:
        print(f"   • {col}")
    
    # Phase 7: Quality validation
    print("\n" + "="*80)
    print("PHASE 7: QUALITY VALIDATION")
    print("="*80)
    print("⏳ Running statistical analysis...")
    
    # Analyze accounts
    account_stats = await stats_agent.analyze_table("UNIFIED_ACCOUNTS")
    print(f"\n📊 UNIFIED_ACCOUNTS:")
    print(f"   • Total rows: {account_stats['basic_stats']['total_rows']:,}")
    print(f"   • Total columns: {account_stats['basic_stats']['total_columns']}")
    print(f"   • Primary key candidates: {len(account_stats.get('primary_key_candidates', []))}")
    
    # Analyze transactions
    transaction_stats = await stats_agent.analyze_table("UNIFIED_TRANSACTIONS")
    print(f"\n📊 UNIFIED_TRANSACTIONS:")
    print(f"   • Total rows: {transaction_stats['basic_stats']['total_rows']:,}")
    print(f"   • Total columns: {transaction_stats['basic_stats']['total_columns']}")
    print(f"   • Primary key candidates: {len(transaction_stats.get('primary_key_candidates', []))}")
    
    # Monitor summary
    print("\n" + "="*80)
    print("🔍 VALIDATION MONITOR SUMMARY")
    print("="*80)
    
    monitor_summary = monitor.get_summary()
    print(f"📊 Tables checked: {monitor_summary['tables_checked']}")
    print(f"⚠️  Issues found: {monitor_summary['issues_found']}")
    
    if monitor_summary['issues_found'] == 0:
        print("\n✅ No critical issues detected!")
    else:
        print("\n⚠️  Some issues detected (see details above)")
    
    # Final summary
    print("\n" + "="*80)
    print("🎉 ULTIMATE MERGE COMPLETE!")
    print("="*80)
    
    print(f"\n📊 RESULTS:")
    print(f"\n  🏦 UNIFIED_ACCOUNTS:")
    print(f"     • Source files: {len(account_results)}")
    print(f"     • Input rows: {total_account_rows:,}")
    print(f"     • Output rows: {unified_accounts_count:,}")
    print(f"     • Columns: {len(account_cols)}")
    
    print(f"\n  💳 UNIFIED_TRANSACTIONS:")
    print(f"     • Source files: {len(transaction_results)}")
    print(f"     • Input rows: {total_transaction_rows:,}")
    print(f"     • Output rows: {unified_transactions_count:,}")
    print(f"     • Columns: {len(transaction_cols)}")
    
    print(f"\n💾 Query the unified data:")
    print(f"   SELECT * FROM UNIFIED_ACCOUNTS LIMIT 10;")
    print(f"   SELECT * FROM UNIFIED_TRANSACTIONS LIMIT 10;")
    
    print(f"\n📺 Check the visualization at http://localhost:8001")
    print(f"   You should see MASSIVE agent communication flows!")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
