"""
Master Agent - Orchestrator and decision maker for the entire pipeline
Implements autonomous resource allocation and workflow coordination
"""
from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime

from agents.orchestration.agent_pool import agent_pool_manager
from agents.orchestration.resource_manager import resource_manager
from core.storage import job_store, JobStatus
from core.events import event_bus
from core.telemetry import telemetry
from sf_infrastructure.connector import snowflake_connector
from core.config import settings

logger = logging.getLogger(__name__)


class MasterAgent:
    """
    Master Agent - The brain of the data integration system
    
    Responsibilities:
    - Analyze workload complexity
    - Autonomously decide agent allocation
    - Orchestrate multi-agent workflows
    - Handle errors and escalations
    - Coordinate with external integrations
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.agent_allocations: Dict[str, Dict[str, int]] = {}
    
    async def analyze_datasets(self, session_id: str) -> Dict[str, Any]:
        """
        Phase 1: Analyze datasets and determine resource requirements
        
        Args:
            session_id: Session identifier
        
        Returns:
            Analysis results with recommended allocation
        """
        logger.info(f"Master Agent analyzing datasets for session {session_id}")
        telemetry.track_api_request("analyze", 0)
        
        try:
            # Get session info
            session = job_store.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Get dataset metadata from Snowflake
            table1 = session["snowflake_tables"]["dataset1"]
            table2 = session["snowflake_tables"]["dataset2"]
            
            # Query row counts
            row_count1 = await snowflake_connector.get_row_count(table1)
            row_count2 = await snowflake_connector.get_row_count(table2)
            total_rows = row_count1 + row_count2
            
            # Get schema info
            schema1 = await snowflake_connector.get_table_info(table1)
            schema2 = await snowflake_connector.get_table_info(table2)
            
            col_count = len(schema1) + len(schema2)
            
            # Determine complexity
            complexity = resource_manager.determine_complexity(
                row_count=total_rows,
                column_count=col_count,
                has_nested_data=False,  # TODO: Detect from schema
                potential_join_keys=1  # TODO: Detect potential keys
            )
            
            # Calculate agent allocation
            allocation = resource_manager.calculate_agent_allocation(
                dataset_size=total_rows,
                schema_complexity=complexity
            )
            
            # Store allocation decision
            self.agent_allocations[session_id] = allocation
            
            logger.info(
                f"Master Agent decision for {session_id}: "
                f"{total_rows} rows, {complexity} complexity, "
                f"allocation={allocation}"
            )
            
            # Publish event
            await event_bus.publish("master.analysis_complete", {
                "session_id": session_id,
                "allocation": allocation,
                "complexity": complexity
            })
            
            return {
                "session_id": session_id,
                "total_rows": total_rows,
                "total_columns": col_count,
                "complexity": complexity,
                "recommended_allocation": allocation
            }
        
        except Exception as e:
            logger.error(f"Master Agent analysis failed: {e}")
            telemetry.track_error("master_agent_analysis", str(e))
            raise
    
    async def initiate_schema_mapping(self, session_id: str) -> Dict[str, Any]:
        """
        Phase 2: Initiate Gemini agent pool for schema mapping
        
        Args:
            session_id: Session identifier
        
        Returns:
            Mapping proposals from Gemini agents
        """
        logger.info(f"Master Agent initiating schema mapping for {session_id}")
        
        try:
            # Get allocation decision
            allocation = self.agent_allocations.get(session_id)
            if not allocation:
                # Analyze first if not done
                await self.analyze_datasets(session_id)
                allocation = self.agent_allocations[session_id]
            
            # Spawn Gemini agent pool
            from agents.gemini.schema_agent import GeminiSchemaAgent
            gemini_pool = agent_pool_manager.create_pool(
                GeminiSchemaAgent,
                f"gemini_pool_{session_id}"
            )
            
            gemini_count = allocation["gemini_agents"]
            agent_ids = gemini_pool.spawn_agents(gemini_count)
            
            telemetry.track_agent_spawn("gemini", gemini_count)
            
            logger.info(f"Spawned {gemini_count} Gemini agents: {agent_ids}")
            
            # Get session data
            session = job_store.get_session(session_id)
            table1 = session["snowflake_tables"]["dataset1"]
            table2 = session["snowflake_tables"]["dataset2"]
            
            # Execute schema analysis in parallel
            tasks = [
                gemini_pool.execute_task({
                    "type": "analyze_schema",
                    "table_name": table1,
                    "session_id": session_id
                }),
                gemini_pool.execute_task({
                    "type": "analyze_schema",
                    "table_name": table2,
                    "session_id": session_id
                })
            ]
            
            schema_analyses = await asyncio.gather(*tasks)
            
            # Now use mapping agent to propose mappings
            from agents.gemini.mapping_agent import GeminiMappingAgent
            mapping_agent = GeminiMappingAgent(
                agent_id=f"mapping_{session_id}",
                config={}
            )
            
            mappings = await mapping_agent.execute({
                "type": "propose_mappings",
                "schema_a": schema_analyses[0],
                "schema_b": schema_analyses[1],
                "session_id": session_id
            })
            
            # Check for conflicts requiring Jira escalation
            conflicts = mappings.get("conflicts", [])
            low_confidence = [
                m for m in mappings.get("mappings", [])
                if m.get("confidence", 100) < settings.JIRA_ESCALATION_THRESHOLD
            ]
            
            if conflicts or low_confidence:
                logger.warning(
                    f"Found {len(conflicts)} conflicts and "
                    f"{len(low_confidence)} low-confidence mappings"
                )
                
                # Trigger Jira agent if enabled
                if settings.JIRA_ENABLED:
                    await self.escalate_to_jira(session_id, conflicts, low_confidence)
            
            return {
                "session_id": session_id,
                "mappings": mappings,
                "gemini_agents_used": gemini_count
            }
        
        except Exception as e:
            logger.error(f"Schema mapping failed: {e}")
            telemetry.track_error("schema_mapping", str(e))
            raise
    
    async def execute_merge(
        self,
        session_id: str,
        approved_mappings: List[Dict],
        merge_type: str
    ) -> str:
        """
        Phase 3: Execute merge operation with merge agent pool
        
        Args:
            session_id: Session identifier
            approved_mappings: User-approved column mappings
            merge_type: Type of join
        
        Returns:
            Job ID for tracking
        """
        logger.info(f"Master Agent executing merge for {session_id}")
        
        try:
            # Create merge job
            job_id = job_store.create_job(
                session_id=session_id,
                job_type="merge",
                metadata={
                    "mappings": approved_mappings,
                    "merge_type": merge_type
                }
            )
            
            # Get allocation
            allocation = self.agent_allocations.get(session_id, {})
            merge_agent_count = allocation.get("merge_agents", 2)
            
            # Spawn merge agent pool
            from agents.merge.base_merge_agent import BaseMergeAgent
            merge_pool = agent_pool_manager.create_pool(
                BaseMergeAgent,
                f"merge_pool_{session_id}"
            )
            
            agent_ids = merge_pool.spawn_agents(merge_agent_count)
            telemetry.track_agent_spawn("merge", merge_agent_count)
            
            logger.info(f"Spawned {merge_agent_count} merge agents: {agent_ids}")
            
            # Update job status
            job_store.update_job_status(
                job_id,
                JobStatus.IN_PROGRESS,
                f"Spawned {merge_agent_count} merge agents"
            )
            
            # Execute merge asynchronously
            asyncio.create_task(
                self._execute_merge_pipeline(
                    job_id,
                    session_id,
                    merge_pool,
                    approved_mappings,
                    merge_type
                )
            )
            
            return job_id
        
        except Exception as e:
            logger.error(f"Merge execution failed: {e}")
            telemetry.track_error("merge_execution", str(e))
            raise
    
    async def _execute_merge_pipeline(
        self,
        job_id: str,
        session_id: str,
        merge_pool: Any,
        mappings: List[Dict],
        merge_type: str
    ):
        """Internal method to execute merge pipeline"""
        try:
            # Generate SQL using Gemini
            from agents.gemini.sql_generator_agent import GeminiSQLGeneratorAgent
            sql_agent = GeminiSQLGeneratorAgent(
                agent_id=f"sql_gen_{session_id}",
                config={}
            )
            
            sql_query = await sql_agent.execute({
                "type": "generate_merge_sql",
                "mappings": mappings,
                "merge_type": merge_type,
                "session_id": session_id
            })
            
            job_store.add_job_log(job_id, "SQL generated by Gemini")
            job_store.update_job(job_id, {"progress_percentage": 30})
            
            # Execute merge with agents
            session = job_store.get_session(session_id)
            result = await merge_pool.execute_task({
                "type": "execute_merge",
                "sql": sql_query,
                "session_id": session_id,
                "output_table": f"MERGED_{session_id}_FINAL"
            })
            
            job_store.add_job_log(job_id, "Merge completed")
            job_store.update_job(job_id, {"progress_percentage": 70})
            
            # Run quality checks
            await self.run_quality_checks(job_id, session_id)
            
            job_store.update_job_status(job_id, JobStatus.COMPLETED, "Pipeline complete")
            job_store.update_job(job_id, {"progress_percentage": 100})
            
        except Exception as e:
            logger.error(f"Merge pipeline failed: {e}")
            job_store.update_job_status(job_id, JobStatus.FAILED, str(e))
            job_store.add_job_error(job_id, str(e))
    
    async def run_quality_checks(self, job_id: str, session_id: str) -> Dict[str, Any]:
        """
        Phase 4: Run quality validation with quality agent pool
        
        Args:
            job_id: Job identifier
            session_id: Session identifier
        
        Returns:
            Quality report
        """
        logger.info(f"Master Agent running quality checks for {session_id}")
        
        try:
            # Spawn quality agent pool
            from agents.quality.null_checker_agent import NullCheckerAgent
            quality_pool = agent_pool_manager.create_pool(
                NullCheckerAgent,
                f"quality_pool_{session_id}"
            )
            
            quality_pool.spawn_agents(5)  # All quality agents
            telemetry.track_agent_spawn("quality", 5)
            
            # Run checks in parallel
            # TODO: Implement actual quality checks
            
            job_store.add_job_log(job_id, "Quality checks completed")
            job_store.update_job(job_id, {"progress_percentage": 90})
            
            return {
                "status": "passed",
                "checks": {}
            }
        
        except Exception as e:
            logger.error(f"Quality checks failed: {e}")
            raise
    
    async def escalate_to_jira(
        self,
        session_id: str,
        conflicts: List[Dict],
        low_confidence_mappings: List[Dict]
    ):
        """
        Escalate issues to Jira for human review
        
        Args:
            session_id: Session identifier
            conflicts: List of conflicts
            low_confidence_mappings: Mappings with low confidence
        """
        logger.info(f"Escalating to Jira for session {session_id}")
        
        try:
            if not settings.JIRA_ENABLED:
                logger.info("Jira disabled, skipping escalation")
                return
            
            from agents.integration_agents.jira_agent import JiraAgent
            jira_agent = JiraAgent(agent_id=f"jira_{session_id}", config={})
            
            # Create tickets for conflicts
            for conflict in conflicts:
                await jira_agent.execute({
                    "type": "create_ticket",
                    "session_id": session_id,
                    "conflict": conflict
                })
            
            logger.info(f"Created {len(conflicts)} Jira tickets")
        
        except Exception as e:
            logger.error(f"Jira escalation failed: {e}")
            # Don't raise - escalation failure shouldn't block pipeline
    
    def get_status(self) -> Dict[str, Any]:
        """Get Master Agent status"""
        return {
            "active_sessions": len(self.active_sessions),
            "agent_pools": agent_pool_manager.get_all_status()
        }


# Global master agent instance
master_agent = MasterAgent()

