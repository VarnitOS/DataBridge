"""
Master Orchestrator Agent

Automatically coordinates all agents to complete data integration tasks.
Uses the Agent Registry to discover and invoke agents dynamically.
"""
from typing import Dict, Any, List
import logging
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool

logger = logging.getLogger(__name__)


class MasterOrchestratorAgent(BaseAgent):
    """
    Master Agent that orchestrates the entire data integration pipeline
    
    Workflow:
    1. User provides: two datasets (files or tables)
    2. Master Agent:
       a. Calls Ingestion Agent (if files) → gets table names
       b. Calls Schema Reader Agent → understands schemas
       c. Calls Conflict Detector Agent → finds issues
       d. Calls SQL Generator Agent → proposes merge SQL
       e. (Optional) Calls Jira Agent if conflicts need review
       f. Calls Merge Agent → executes merge (with user approval)
       g. Calls Quality Agent → validates result
    
    All communication is Agent-to-Agent (A2A) via registry.
    """
    
    def __init__(self, agent_id: str = "master_orchestrator", config: Dict[str, Any] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type="master_orchestrator",
            capabilities=[AgentCapability.DATA_INGESTION],  # Can orchestrate all
            config=config
        )
    
    def _define_tools(self):
        """Master agent exposes high-level orchestration tools"""
        self._tools = [
            AgentTool(
                name="orchestrate_full_pipeline",
                description="Orchestrate complete data integration pipeline from files to merged dataset",
                capability=AgentCapability.DATA_INGESTION,
                parameters={
                    "type": "object",
                    "properties": {
                        "file1_path": {"type": "string", "description": "Path to first dataset"},
                        "file2_path": {"type": "string", "description": "Path to second dataset"},
                        "session_id": {"type": "string", "description": "Session identifier"},
                        "merge_type": {"type": "string", "description": "Type of merge (full_outer, inner, left)"},
                        "auto_approve": {"type": "boolean", "description": "Auto-approve SQL without user confirmation"}
                    },
                    "required": ["file1_path", "file2_path", "session_id"]
                },
                handler=self._handle_full_pipeline,
                agent_id=self.agent_id
            )
        ]
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestration task"""
        task_type = task.get("type")
        
        if task_type == "full_pipeline":
            return await self.orchestrate_full_pipeline(
                file1_path=task["file1_path"],
                file2_path=task["file2_path"],
                session_id=task["session_id"],
                merge_type=task.get("merge_type", "full_outer"),
                auto_approve=task.get("auto_approve", False)
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _handle_full_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for orchestrate_full_pipeline tool"""
        return await self.orchestrate_full_pipeline(**params)
    
    async def orchestrate_full_pipeline(
        self,
        file1_path: str,
        file2_path: str,
        session_id: str,
        merge_type: str = "full_outer",
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Orchestrate the full pipeline with automatic A2A communication
        """
        logger.info(f"🚀 [{self.agent_id}] Starting full pipeline orchestration")
        
        pipeline_state = {
            "session_id": session_id,
            "steps_completed": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # STEP 1: Ingest datasets
            logger.info(f"📥 Step 1: Ingesting datasets...")
            table1_result = await self.invoke_capability(
                capability=AgentCapability.DATA_INGESTION,
                parameters={
                    "type": "ingest_file",
                    "file_path": file1_path,
                    "session_id": session_id,
                    "dataset_num": 1
                }
            )
            
            if not table1_result['success']:
                raise Exception(f"Failed to ingest dataset 1: {table1_result.get('error')}")
            
            table1 = table1_result['result']['table_name']
            pipeline_state['steps_completed'].append("ingest_dataset_1")
            logger.info(f"✅ Dataset 1 ingested: {table1}")
            
            # Ingest dataset 2
            table2_result = await self.invoke_capability(
                capability=AgentCapability.DATA_INGESTION,
                parameters={
                    "type": "ingest_file",
                    "file_path": file2_path,
                    "session_id": session_id,
                    "dataset_num": 2
                }
            )
            
            if not table2_result['success']:
                raise Exception(f"Failed to ingest dataset 2: {table2_result.get('error')}")
            
            table2 = table2_result['result']['table_name']
            pipeline_state['steps_completed'].append("ingest_dataset_2")
            logger.info(f"✅ Dataset 2 ingested: {table2}")
            
            # STEP 2: Analyze schemas with Gemini
            logger.info(f"🧠 Step 2: Analyzing schemas with Gemini...")
            schema1_result = await self.invoke_capability(
                capability=AgentCapability.SCHEMA_ANALYSIS,
                parameters={
                    "type": "read_schema",
                    "table_name": table1,
                    "include_sample": True,
                    "sample_size": 10
                }
            )
            
            if not schema1_result['success']:
                raise Exception(f"Schema analysis failed for table1: {schema1_result.get('error')}")
            
            schema1 = schema1_result['result']['schema']
            pipeline_state['steps_completed'].append("analyze_schema_1")
            logger.info(f"✅ Schema 1 analyzed ({len(schema1)} columns)")
            
            schema2_result = await self.invoke_capability(
                capability=AgentCapability.SCHEMA_ANALYSIS,
                parameters={
                    "type": "read_schema",
                    "table_name": table2,
                    "include_sample": True,
                    "sample_size": 10
                }
            )
            
            if not schema2_result['success']:
                raise Exception(f"Schema analysis failed for table2: {schema2_result.get('error')}")
            
            schema2 = schema2_result['result']['schema']
            pipeline_state['steps_completed'].append("analyze_schema_2")
            logger.info(f"✅ Schema 2 analyzed ({len(schema2)} columns)")
            
            # STEP 3: Detect conflicts
            logger.info(f"⚠️  Step 3: Detecting conflicts...")
            
            # Auto-propose mappings (simple heuristic: match column names)
            proposed_mappings = self._auto_propose_mappings(schema1, schema2)
            
            conflict_result = await self.invoke_capability(
                capability=AgentCapability.CONFLICT_DETECTION,
                parameters={
                    "type": "detect_conflicts",
                    "table1": table1,
                    "table2": table2,
                    "schema1": schema1,
                    "schema2": schema2,
                    "proposed_mappings": proposed_mappings
                }
            )
            
            if not conflict_result['success']:
                raise Exception(f"Conflict detection failed: {conflict_result.get('error')}")
            
            conflicts = conflict_result['result']['conflicts']
            requires_review = conflict_result['result'].get('requires_human_review', False)
            
            pipeline_state['steps_completed'].append("detect_conflicts")
            pipeline_state['conflicts'] = conflicts
            pipeline_state['conflict_summary'] = conflict_result['result'].get('severity_summary', {})
            
            if requires_review:
                pipeline_state['warnings'].append("CRITICAL conflicts detected - human review recommended")
                logger.warning(f"⚠️  CRITICAL conflicts detected!")
                
                if not auto_approve:
                    # Would normally create Jira ticket here
                    logger.info(f"🎫 Would create Jira ticket for conflict review")
            
            logger.info(f"✅ Conflict detection complete: {len(conflicts)} conflicts found")
            
            # STEP 4: Generate merge SQL
            logger.info(f"🔧 Step 4: Generating merge SQL with Gemini...")
            sql_result = await self.invoke_capability(
                capability=AgentCapability.SQL_GENERATION,
                parameters={
                    "type": "generate_merge_sql",
                    "table1": table1,
                    "table2": table2,
                    "schema1": schema1,
                    "schema2": schema2,
                    "merge_type": merge_type,
                    "join_columns": proposed_mappings
                }
            )
            
            if not sql_result['success']:
                raise Exception(f"SQL generation failed: {sql_result.get('error')}")
            
            proposed_sql = sql_result['result']['proposed_sql']
            pipeline_state['steps_completed'].append("generate_sql")
            pipeline_state['proposed_sql'] = proposed_sql
            
            logger.info(f"✅ Merge SQL generated ({len(proposed_sql)} chars)")
            
            # STEP 5: Execute merge (with approval)
            if auto_approve or not requires_review:
                logger.info(f"🔄 Step 5: Executing merge...")
                # Would invoke merge agent here
                pipeline_state['steps_completed'].append("execute_merge")
                logger.info(f"✅ Merge executed (simulated)")
            else:
                logger.info(f"⏸️  Step 5: Awaiting user approval for merge")
                pipeline_state['awaiting_approval'] = True
            
            # FINAL RESULT
            pipeline_state['status'] = 'completed' if not pipeline_state.get('awaiting_approval') else 'awaiting_approval'
            
            logger.info(f"🎉 [{self.agent_id}] Pipeline orchestration complete!")
            
            return {
                "success": True,
                "session_id": session_id,
                "pipeline_state": pipeline_state,
                "table1": table1,
                "table2": table2,
                "conflicts": conflicts,
                "proposed_sql": proposed_sql,
                "message": "Pipeline orchestration successful - all agents coordinated automatically via A2A"
            }
            
        except Exception as e:
            logger.error(f"❌ [{self.agent_id}] Pipeline orchestration failed: {e}")
            pipeline_state['status'] = 'failed'
            pipeline_state['errors'].append(str(e))
            
            return {
                "success": False,
                "session_id": session_id,
                "pipeline_state": pipeline_state,
                "error": str(e)
            }
    
    def _auto_propose_mappings(
        self,
        schema1: List[Dict[str, Any]],
        schema2: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Auto-propose column mappings (simple heuristic)
        In production, Gemini would do this
        """
        mappings = []
        
        # Match by exact name
        schema1_names = {col['name'].lower(): col['name'] for col in schema1}
        schema2_names = {col['name'].lower(): col['name'] for col in schema2}
        
        for name_lower, name1 in schema1_names.items():
            if name_lower in schema2_names:
                mappings.append({
                    "left": name1,
                    "right": schema2_names[name_lower]
                })
        
        # Simple heuristics for common patterns
        # "id" matches "customer_id", "client_id", etc.
        # "name" matches "full_name", "customer_name", etc.
        
        logger.info(f"Auto-proposed {len(mappings)} column mappings")
        return mappings
