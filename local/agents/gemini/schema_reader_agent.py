"""
Gemini Schema Reader Agent
Reads and understands database schemas, proposes data types, identifies relationships
"""
from typing import Dict, Any, List
import logging
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool
from agents.gemini.base_gemini_agent import BaseGeminiAgent
from sf_infrastructure.connector import snowflake_connector

logger = logging.getLogger(__name__)


class GeminiSchemaReaderAgent(BaseAgent, BaseGeminiAgent):
    """
    Reads table schemas from Snowflake and provides intelligent analysis
    - Column types and semantics
    - Data quality observations
    - Potential join keys
    - Recommended transformations
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        # Initialize BaseAgent first (for registry)
        BaseAgent.__init__(
            self,
            agent_id=agent_id,
            agent_type="gemini_schema_reader",
            capabilities=[AgentCapability.SCHEMA_ANALYSIS],
            config=config,
            auto_register=True
        )
        
        # Initialize BaseGeminiAgent (for Gemini integration)
        BaseGeminiAgent.__init__(self, agent_id=agent_id, config=config)
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="read_and_analyze_schema",
                description="Read Snowflake table schema and analyze with Gemini AI for semantic understanding",
                capability=AgentCapability.SCHEMA_ANALYSIS,
                parameters={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Snowflake table name to analyze"
                        },
                        "include_sample": {
                            "type": "boolean",
                            "description": "Include sample data in analysis (default: true)"
                        },
                        "sample_size": {
                            "type": "integer",
                            "description": "Number of sample rows (default: 10)"
                        }
                    },
                    "required": ["table_name"]
                },
                handler=self._handle_schema_analysis,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_schema_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for schema analysis tool (called via A2A)
        
        Note: The AgentRegistry's invoke_tool already wraps results with success/error,
        so we just return the raw result here
        """
        # Validate required parameters
        if "table_name" not in params:
            raise ValueError(f"Missing required parameter 'table_name'. Received params: {list(params.keys())}")
        
        return await self.read_and_analyze_schema(
            table_name=params["table_name"],
            include_sample=params.get("include_sample", True),
            sample_size=params.get("sample_size", 10)
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute schema reading task
        
        Expected task format:
        {
            "type": "read_schema",
            "table_name": "RAW_session_001_DATASET_1",
            "include_sample": true,
            "sample_size": 10
        }
        """
        task_type = task.get("type")
        
        if task_type == "read_schema":
            return await self.read_and_analyze_schema(
                table_name=task["table_name"],
                include_sample=task.get("include_sample", True),
                sample_size=task.get("sample_size", 10)
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def read_and_analyze_schema(
        self,
        table_name: str,
        include_sample: bool = True,
        sample_size: int = 10
    ) -> Dict[str, Any]:
        """
        Read schema from Snowflake and analyze it with Gemini
        """
        logger.info(f"[{self.agent_id}] Reading schema for table: {table_name}")
        
        try:
            # Step 1: Get raw schema from Snowflake
            schema_info = await snowflake_connector.get_table_info(table_name)
            
            # Step 2: Get sample data if requested
            sample_data = None
            if include_sample:
                query = f"SELECT * FROM {table_name} LIMIT {sample_size}"
                sample_data = await snowflake_connector.execute_query(query)
                
                # Convert datetime objects to strings for JSON serialization
                if sample_data:
                    from datetime import datetime, date
                    cleaned_sample = []
                    for row in sample_data:
                        cleaned_row = {}
                        for key, value in row.items():
                            if isinstance(value, (datetime, date)):
                                cleaned_row[key] = value.isoformat()
                            else:
                                cleaned_row[key] = value
                        cleaned_sample.append(cleaned_row)
                    sample_data = cleaned_sample
            
            # Step 3: Build context for Gemini
            context = {
                "table_name": table_name,
                "schema": [
                    {
                        "name": col.get("name") or col.get("NAME"),
                        "type": col.get("type") or col.get("TYPE"),
                        "nullable": col.get("null?") or col.get("NULL?"),
                    }
                    for col in schema_info
                ],
                "sample_data": sample_data[:5] if sample_data else None,  # Show first 5 rows
                "row_count": len(sample_data) if sample_data else 0
            }
            
            # Step 4: Ask Gemini to analyze the schema
            prompt = f"""
Analyze this database table schema and provide insights:

Table: {table_name}
Columns: {len(context['schema'])}

Schema:
{self._format_schema_for_prompt(context['schema'])}

Sample Data (first 5 rows):
{self._format_sample_data(sample_data[:5] if sample_data else [])}

Provide:
1. **Semantic Understanding**: What does each column represent? (e.g., "customer_id" is a unique identifier)
2. **Data Types Analysis**: Are the current types appropriate? Suggest improvements if needed
3. **Potential Issues**: Missing values, inconsistent formats, potential duplicates
4. **Join Key Candidates**: Which columns could be used to join with other tables?
5. **Data Quality Score**: Rate the quality (0.0-1.0) based on completeness, consistency, validity
6. **Recommended Transformations**: Any normalization, cleaning, or type changes needed

Be concise and actionable.
"""
            
            # Step 5: Get Gemini's analysis
            analysis_result = await self.analyze_with_tools(prompt, context)
            
            # Step 6: Structure the response
            result = {
                "agent_id": self.agent_id,
                "table_name": table_name,
                "schema": context['schema'],
                "sample_data": sample_data[:5] if sample_data else [],
                "gemini_analysis": analysis_result['analysis'],
                "recommended_tools": analysis_result['recommended_tools'],
                "confidence": analysis_result['confidence'],
                "metadata": {
                    "column_count": len(context['schema']),
                    "sample_size": len(sample_data) if sample_data else 0,
                    "has_nulls": self._check_for_nulls(context['schema'])
                }
            }
            
            logger.info(f"[{self.agent_id}] Schema analysis complete for {table_name}")
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Schema analysis failed: {e}")
            raise
    
    def _format_schema_for_prompt(self, schema: List[Dict[str, Any]]) -> str:
        """Format schema for Gemini prompt"""
        lines = []
        for col in schema:
            nullable = "NULL" if col.get("nullable") == "Y" else "NOT NULL"
            lines.append(f"  - {col['name']}: {col['type']} {nullable}")
        return "\n".join(lines)
    
    def _format_sample_data(self, sample_data: List[Dict[str, Any]]) -> str:
        """Format sample data for Gemini prompt"""
        if not sample_data:
            return "No sample data available"
        
        # Take first row to get column names
        if sample_data:
            headers = list(sample_data[0].keys())
            lines = [f"  {', '.join(headers)}"]
            for row in sample_data:
                values = [str(row.get(h, 'NULL'))[:50] for h in headers]  # Truncate long values
                lines.append(f"  {', '.join(values)}")
            return "\n".join(lines)
        return "No sample data"
    
    def _check_for_nulls(self, schema: List[Dict[str, Any]]) -> bool:
        """Check if any columns allow nulls"""
        return any(col.get("nullable") == "Y" for col in schema)
