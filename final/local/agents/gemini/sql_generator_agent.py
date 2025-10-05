"""
Gemini SQL Generator Agent
Generates optimized SQL queries for merging, transforming, and analyzing data
"""
from typing import Dict, Any, List
import logging
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool
from agents.gemini.base_gemini_agent import BaseGeminiAgent

logger = logging.getLogger(__name__)


class GeminiSQLGeneratorAgent(BaseAgent, BaseGeminiAgent):
    """
    Generates SQL queries based on user requirements
    - Merge/Join queries
    - Data transformation queries
    - Quality check queries
    - Aggregation queries
    
    IMPORTANT: This agent PROPOSES SQL, it does NOT execute it
    User must approve before execution
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        # Initialize BaseAgent
        BaseAgent.__init__(
            self,
            agent_id=agent_id,
            agent_type="gemini_sql_generator",
            capabilities=[AgentCapability.SQL_GENERATION],
            config=config,
            auto_register=True
        )
        
        # Initialize BaseGeminiAgent
        BaseGeminiAgent.__init__(self, agent_id=agent_id, config=config)
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="generate_merge_sql",
                description="Generate SQL to merge two Snowflake tables with Gemini AI",
                capability=AgentCapability.SQL_GENERATION,
                parameters={
                    "type": "object",
                    "properties": {
                        "table1": {"type": "string"},
                        "table2": {"type": "string"},
                        "schema1": {"type": "array"},
                        "schema2": {"type": "array"},
                        "merge_type": {"type": "string", "enum": ["full_outer", "inner", "left", "right"]},
                        "join_columns": {"type": "array"}
                    },
                    "required": ["table1", "table2", "schema1", "schema2"]
                },
                handler=self._handle_merge_sql,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_merge_sql(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for merge SQL generation (called via A2A)"""
        return await self.generate_merge_sql(
            table1=params["table1"],
            table2=params["table2"],
            schema1=params["schema1"],
            schema2=params["schema2"],
            merge_type=params.get("merge_type", "full_outer"),
            join_columns=params.get("join_columns", [])
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SQL generation task
        
        Expected task format:
        {
            "type": "generate_merge_sql",
            "table1": "RAW_session_001_DATASET_1",
            "table2": "RAW_session_001_DATASET_2",
            "schema1": [...],
            "schema2": [...],
            "merge_type": "full_outer",
            "join_columns": [{"left": "customer_id", "right": "client_id"}]
        }
        """
        task_type = task.get("type")
        
        if task_type == "generate_merge_sql":
            return await self.generate_merge_sql(
                table1=task["table1"],
                table2=task["table2"],
                schema1=task.get("schema1", []),
                schema2=task.get("schema2", []),
                merge_type=task.get("merge_type", "full_outer"),
                join_columns=task.get("join_columns", [])
            )
        elif task_type == "generate_transform_sql":
            return await self.generate_transform_sql(
                table_name=task["table_name"],
                transformations=task.get("transformations", [])
            )
        elif task_type == "generate_quality_sql":
            return await self.generate_quality_check_sql(
                table_name=task["table_name"],
                quality_checks=task.get("quality_checks", [])
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def generate_merge_sql(
        self,
        table1: str,
        table2: str,
        schema1: List[Dict[str, Any]],
        schema2: List[Dict[str, Any]],
        merge_type: str = "full_outer",
        join_columns: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL to merge two tables
        """
        logger.info(f"[{self.agent_id}] Generating {merge_type} merge SQL for {table1} + {table2}")
        
        prompt = f"""
Generate an optimized SQL query to merge these two Snowflake tables:

**Table 1:** {table1}
Schema:
{self._format_schema(schema1)}

**Table 2:** {table2}
Schema:
{self._format_schema(schema2)}

**Merge Type:** {merge_type} join
**Join Columns:** {join_columns or "Auto-detect best join keys"}

Requirements:
1. Generate a complete, executable SQL query
2. Handle column name conflicts (use table prefixes)
3. Handle null values appropriately
4. Include comments explaining each section
5. Optimize for Snowflake performance
6. Create a unified schema with all relevant columns
7. Add metadata columns (source table, merge timestamp)

Provide:
- Complete SQL query
- Explanation of the merge logic
- Estimated complexity
- Potential issues to watch for
- Recommended indexes (if creating a materialized table)

Format as:
```sql
-- Your SQL here
```

Then provide explanations.
"""
        
        analysis_result = await self.analyze_with_tools(prompt, {
            "table1": table1,
            "table2": table2,
            "merge_type": merge_type
        })
        
        # Extract SQL from the response
        sql_query = self._extract_sql_from_response(analysis_result['analysis'])
        
        result = {
            "agent_id": self.agent_id,
            "task": "merge_sql_generation",
            "proposed_sql": sql_query,
            "explanation": analysis_result['analysis'],
            "merge_type": merge_type,
            "join_columns": join_columns,
            "confidence": analysis_result['confidence'],
            "warning": "⚠️ SQL NOT EXECUTED - User must approve and provide final schema",
            "next_steps": [
                "Review the proposed SQL",
                "Verify join keys are correct",
                "Approve for execution",
                "Provide target table name"
            ]
        }
        
        logger.info(f"[{self.agent_id}] Merge SQL generated ({len(sql_query)} chars)")
        return result
    
    async def generate_transform_sql(
        self,
        table_name: str,
        transformations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate SQL for data transformations
        """
        logger.info(f"[{self.agent_id}] Generating transformation SQL for {table_name}")
        
        transformations_desc = "\n".join([
            f"- {t.get('column')}: {t.get('operation')} ({t.get('description', 'No description')})"
            for t in transformations
        ])
        
        prompt = f"""
Generate SQL to transform data in table: {table_name}

Requested Transformations:
{transformations_desc}

Provide:
1. Complete SQL (CREATE TABLE AS SELECT or UPDATE)
2. Explanation of each transformation
3. Data type conversions if needed
4. Error handling for edge cases

Format as executable Snowflake SQL.
"""
        
        analysis_result = await self.analyze_with_tools(prompt, {
            "table_name": table_name,
            "transformations": transformations
        })
        
        sql_query = self._extract_sql_from_response(analysis_result['analysis'])
        
        return {
            "agent_id": self.agent_id,
            "task": "transformation_sql_generation",
            "proposed_sql": sql_query,
            "explanation": analysis_result['analysis'],
            "transformations": transformations,
            "confidence": analysis_result['confidence'],
            "warning": "⚠️ SQL NOT EXECUTED - User must approve"
        }
    
    async def generate_quality_check_sql(
        self,
        table_name: str,
        quality_checks: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL for data quality checks
        """
        logger.info(f"[{self.agent_id}] Generating quality check SQL for {table_name}")
        
        default_checks = [
            "null_counts",
            "duplicate_detection",
            "type_validation",
            "referential_integrity",
            "statistical_summary"
        ]
        
        checks = quality_checks or default_checks
        
        prompt = f"""
Generate SQL queries to perform data quality checks on table: {table_name}

Required Checks:
{', '.join(checks)}

Provide separate SQL queries for each check with:
1. Query description
2. Executable SQL
3. How to interpret results
4. Threshold recommendations

Format each as:
```sql
-- Check: <name>
-- Purpose: <description>
<SQL>
```
"""
        
        analysis_result = await self.analyze_with_tools(prompt, {
            "table_name": table_name,
            "quality_checks": checks
        })
        
        sql_queries = self._extract_all_sql_blocks(analysis_result['analysis'])
        
        return {
            "agent_id": self.agent_id,
            "task": "quality_check_sql_generation",
            "proposed_queries": sql_queries,
            "explanation": analysis_result['analysis'],
            "checks": checks,
            "confidence": analysis_result['confidence'],
            "warning": "⚠️ SQL NOT EXECUTED - User must approve and execute each check"
        }
    
    def _format_schema(self, schema: List[Dict[str, Any]]) -> str:
        """Format schema for prompt"""
        if not schema:
            return "Schema not provided"
        return "\n".join([
            f"  - {col.get('name', 'unknown')}: {col.get('type', 'unknown')}"
            for col in schema
        ])
    
    def _extract_sql_from_response(self, response_text: str) -> str:
        """Extract first SQL block from Gemini response"""
        import re
        sql_pattern = r"```sql\n(.*?)\n```"
        match = re.search(sql_pattern, response_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response_text  # Return full response if no SQL block found
    
    def _extract_all_sql_blocks(self, response_text: str) -> List[Dict[str, str]]:
        """Extract all SQL blocks from response"""
        import re
        sql_pattern = r"```sql\n(.*?)\n```"
        matches = re.findall(sql_pattern, response_text, re.DOTALL)
        return [{"query": match.strip()} for match in matches]