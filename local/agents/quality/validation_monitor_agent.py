"""
Validation Monitor Agent - Real-time sanity checks
Watches agent communications and catches obvious data quality issues
"""
from typing import Dict, Any, List
import logging
import asyncio
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool
from core.event_bus import event_bus
from sf_infrastructure.connector import snowflake_connector

logger = logging.getLogger(__name__)


class ValidationMonitorAgent(BaseAgent):
    """
    Validation Monitor Agent - Watches for obvious data quality issues
    
    Monitors:
    - Entire NULL datasets
    - Generic column names (c1, c2, c3...)
    - INFER_SCHEMA failures
    - Empty tables
    - Suspiciously low row counts
    
    Does NOT block the pipeline - just raises warnings!
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type="validation_monitor",
            capabilities=[AgentCapability.DATA_QUALITY],
            config=config,
            auto_register=True
        )
        
        self.issues_found = []
        self.tables_checked = set()
        
        # Subscribe to event bus to monitor agent communications
        event_bus.subscribe(self._on_agent_event)
        
        logger.info(f"[{self.agent_id}] 🔍 Validation Monitor started - watching for issues")
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="quick_sanity_check",
                description="Run quick sanity checks on a Snowflake table",
                capability=AgentCapability.DATA_QUALITY,
                parameters={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Table to check"}
                    },
                    "required": ["table_name"]
                },
                handler=self._handle_sanity_check,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_sanity_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for sanity check tool"""
        return await self.quick_sanity_check(params["table_name"])
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation task"""
        task_type = task.get("type")
        
        if task_type == "sanity_check":
            return await self.quick_sanity_check(task["table_name"])
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _on_agent_event(self, event: dict):
        """
        Called whenever agents communicate
        Runs quick checks to catch obvious issues
        """
        try:
            event_type = event.get("type")
            data = event.get("data", {})
            
            # Monitor for completed ingestion operations
            if event_type == "agent_response":
                tool_name = data.get("tool_name", "")
                
                # Check tables after ingestion
                if "ingest" in tool_name.lower():
                    # Give it a moment to finish
                    await asyncio.sleep(0.5)
                    await self._check_recent_ingestion()
            
            # Monitor for schema analysis
            elif event_type == "agent_call":
                tool_name = data.get("tool_name", "")
                params = data.get("parameters", {})
                
                # Check tables being analyzed
                if "schema" in tool_name.lower() and "table_name" in params:
                    table_name = params["table_name"]
                    if table_name and table_name not in self.tables_checked:
                        await self._check_table_async(table_name)
        
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Error in event handler: {e}")
    
    async def _check_recent_ingestion(self):
        """Check the most recently created tables"""
        try:
            # Get recent tables
            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'PUBLIC' 
            AND TABLE_NAME LIKE 'RAW_%'
            ORDER BY CREATED DESC
            LIMIT 2
            """
            
            recent_tables = await snowflake_connector.execute_query(query)
            
            for row in recent_tables:
                table_name = row.get('TABLE_NAME')
                if table_name and table_name not in self.tables_checked:
                    await self._check_table_async(table_name)
        
        except Exception as e:
            logger.debug(f"[{self.agent_id}] Could not check recent ingestion: {e}")
    
    async def _check_table_async(self, table_name: str):
        """Run async sanity check on a table"""
        try:
            result = await self.quick_sanity_check(table_name)
            
            if not result.get("passed", True):
                # Emit warning event
                await event_bus.emit("validation_warning", {
                    "agent_id": self.agent_id,
                    "table_name": table_name,
                    "issues": result.get("issues", [])
                })
        
        except Exception as e:
            logger.debug(f"[{self.agent_id}] Error checking {table_name}: {e}")
    
    async def quick_sanity_check(self, table_name: str) -> Dict[str, Any]:
        """
        Quick sanity checks - just scratching the surface!
        
        Checks:
        1. Table exists
        2. Has rows
        3. Columns are not all NULL
        4. Column names are not generic (c1, c2, c3...)
        5. At least some data is populated
        """
        if table_name in self.tables_checked:
            return {"skipped": True, "reason": "Already checked"}
        
        self.tables_checked.add(table_name)
        
        logger.info(f"[{self.agent_id}] 🔍 Running sanity check on {table_name}")
        
        issues = []
        warnings = []
        
        try:
            # Check 1: Table exists and has rows
            row_count = await snowflake_connector.get_row_count(table_name)
            
            if row_count == 0:
                issues.append({
                    "severity": "ERROR",
                    "issue": "Empty table",
                    "details": f"Table {table_name} has 0 rows"
                })
                logger.error(f"[{self.agent_id}] ❌ {table_name}: Empty table!")
            
            # Check 2: Get schema
            schema = await snowflake_connector.get_table_info(table_name)
            
            if not schema:
                issues.append({
                    "severity": "ERROR",
                    "issue": "No schema",
                    "details": f"Could not retrieve schema for {table_name}"
                })
                logger.error(f"[{self.agent_id}] ❌ {table_name}: No schema!")
                return {
                    "table_name": table_name,
                    "passed": False,
                    "issues": issues,
                    "warnings": warnings
                }
            
            # Check 3: Generic column names (c1, c2, c3...)
            column_names = [col.get('name') or col.get('NAME') for col in schema]
            generic_columns = [col for col in column_names if col and col.lower().startswith('c') and col[1:].isdigit()]
            
            if len(generic_columns) > 5:  # More than 5 generic columns is suspicious
                issues.append({
                    "severity": "CRITICAL",
                    "issue": "Generic column names detected",
                    "details": f"Found {len(generic_columns)} columns like c1, c2, c3... This suggests INFER_SCHEMA failed!"
                })
                logger.error(f"[{self.agent_id}] ❌ {table_name}: Generic column names (c1, c2...) - INFER_SCHEMA likely failed!")
            
            # Check 4: Sample data for NULLs (only if we have rows)
            if row_count > 0:
                sample_query = f"SELECT * FROM {table_name} LIMIT 3"
                sample_data = await snowflake_connector.execute_query(sample_query)
                
                if sample_data:
                    # Count NULL values across all columns in sample
                    total_values = 0
                    null_values = 0
                    
                    for row in sample_data:
                        for col_name in column_names:
                            total_values += 1
                            if row.get(col_name) is None:
                                null_values += 1
                    
                    if total_values > 0:
                        null_percentage = (null_values / total_values) * 100
                        
                        if null_percentage > 90:
                            issues.append({
                                "severity": "CRITICAL",
                                "issue": "Data is almost entirely NULL",
                                "details": f"{null_percentage:.1f}% of sample data is NULL"
                            })
                            logger.error(f"[{self.agent_id}] ❌ {table_name}: {null_percentage:.1f}% NULL data!")
                        
                        elif null_percentage > 50:
                            warnings.append({
                                "severity": "WARNING",
                                "issue": "High NULL percentage",
                                "details": f"{null_percentage:.1f}% of sample data is NULL"
                            })
                            logger.warning(f"[{self.agent_id}] ⚠️  {table_name}: {null_percentage:.1f}% NULL data")
            
            # Check 5: Suspiciously low row count for large files
            if row_count < 10 and row_count > 0:
                warnings.append({
                    "severity": "WARNING",
                    "issue": "Low row count",
                    "details": f"Only {row_count} rows - verify file loaded completely"
                })
                logger.warning(f"[{self.agent_id}] ⚠️  {table_name}: Only {row_count} rows")
            
            # Summary
            passed = len(issues) == 0
            
            if passed and len(warnings) == 0:
                logger.info(f"[{self.agent_id}] ✅ {table_name}: Sanity checks passed ({row_count:,} rows, {len(column_names)} columns)")
            
            result = {
                "table_name": table_name,
                "passed": passed,
                "row_count": row_count,
                "column_count": len(column_names),
                "issues": issues,
                "warnings": warnings,
                "column_names": column_names[:10]  # First 10 columns
            }
            
            # Store issues for reporting
            if issues or warnings:
                self.issues_found.append(result)
            
            return result
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{self.agent_id}] ❌ Failed to check {table_name}: {error_msg}")
            
            return {
                "table_name": table_name,
                "passed": False,
                "error": error_msg,
                "issues": [{
                    "severity": "ERROR",
                    "issue": "Sanity check failed",
                    "details": error_msg
                }]
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all issues found"""
        return {
            "agent_id": self.agent_id,
            "tables_checked": len(self.tables_checked),
            "issues_found": len(self.issues_found),
            "details": self.issues_found
        }
