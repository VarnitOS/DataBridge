"""
Gemini Schema Agent - Semantic schema understanding using Gemini 2.5 Pro
"""
from typing import Dict, Any, List
import logging
import google.generativeai as genai
from core.config import settings
from sf_infrastructure.connector import snowflake_connector

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiSchemaAgent:
    """
    Gemini Schema Agent - Uses Gemini 2.5 Pro for semantic schema analysis
    
    Responsibilities:
    - Analyze table schemas from Snowflake
    - Understand semantic meaning of columns
    - Identify potential join keys
    - Detect data quality issues
    """
    
    def __init__(self, agent_id: str, config: Dict = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info(f"Initialized Gemini Schema Agent: {agent_id}")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute schema analysis task"""
        task_type = task.get("type")
        
        if task_type == "analyze_schema":
            return await self.analyze_schema(
                task["table_name"],
                task.get("session_id")
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def analyze_schema(
        self,
        table_name: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze table schema using Gemini 2.5 Pro
        
        Args:
            table_name: Snowflake table name
            session_id: Optional session identifier
        
        Returns:
            Comprehensive schema analysis
        """
        logger.info(f"[{self.agent_id}] Analyzing schema for {table_name}")
        
        try:
            # Get schema from Snowflake
            schema_info = await snowflake_connector.get_table_info(table_name)
            
            # Get sample data
            sample_query = f"SELECT * FROM {table_name} LIMIT 100"
            sample_data = await snowflake_connector.execute_query(sample_query)
            
            # Get row count
            row_count = await snowflake_connector.get_row_count(table_name)
            
            # Build prompt for Gemini
            prompt = self._build_analysis_prompt(
                table_name,
                schema_info,
                sample_data[:10],  # First 10 rows
                row_count
            )
            
            # Call Gemini 2.5 Pro
            response = self.model.generate_content(prompt)
            semantic_analysis = response.text
            
            logger.info(f"[{self.agent_id}] Schema analysis complete for {table_name}")
            
            return {
                "table_name": table_name,
                "row_count": row_count,
                "columns": self._parse_schema_info(schema_info),
                "sample_data": sample_data[:10],
                "semantic_understanding": semantic_analysis,
                "potential_join_keys": self._extract_join_keys(semantic_analysis),
                "data_quality_observations": self._extract_quality_notes(semantic_analysis)
            }
        
        except Exception as e:
            logger.error(f"[{self.agent_id}] Schema analysis failed: {e}")
            raise
    
    def _build_analysis_prompt(
        self,
        table_name: str,
        schema_info: List[Dict],
        sample_data: List[Dict],
        row_count: int
    ) -> str:
        """Build Gemini prompt for schema analysis"""
        
        # Format schema
        schema_str = "\n".join([
            f"- {col['name']} ({col['type']}){' [nullable]' if col.get('null') == 'Y' else ''}"
            for col in schema_info
        ])
        
        # Format sample data
        sample_str = ""
        if sample_data:
            keys = list(sample_data[0].keys())[:5]  # First 5 columns
            sample_str = "\n".join([
                str({k: row.get(k) for k in keys})
                for row in sample_data[:5]
            ])
        
        prompt = f"""
You are a data integration expert analyzing database schemas. Analyze this table and provide semantic understanding.

Table: {table_name}
Row Count: {row_count:,}

Schema:
{schema_str}

Sample Data (first 5 rows, first 5 columns):
{sample_str}

Provide a comprehensive analysis including:

1. **Semantic Meaning**: What does this table represent? (e.g., customers, transactions, products)

2. **Column Semantics**: For each column, explain its business meaning

3. **Potential Join Keys**: Which columns could be used to join with other tables? 
   Identify:
   - Primary key candidates (unique identifiers)
   - Foreign key candidates (references to other entities)
   - Natural keys (business identifiers like email, customer_id, etc.)

4. **Data Quality Observations**: 
   - Any obvious data quality issues?
   - Missing patterns?
   - Type inconsistencies?
   - Recommended validations?

5. **Business Domain**: What business domain does this table belong to? (CRM, Finance, HR, etc.)

Format your response clearly with section headers.
"""
        return prompt
    
    def _parse_schema_info(self, schema_info: List[Dict]) -> List[Dict[str, Any]]:
        """Parse Snowflake schema info into structured format"""
        return [
            {
                "name": col.get("name"),
                "type": col.get("type"),
                "nullable": col.get("null") == "Y",
                "default": col.get("default")
            }
            for col in schema_info
        ]
    
    def _extract_join_keys(self, semantic_analysis: str) -> List[str]:
        """Extract potential join keys from Gemini's analysis"""
        # Simple keyword extraction (can be improved)
        join_keywords = ["primary key", "foreign key", "join key", "identifier", "_id", "_key"]
        
        potential_keys = []
        lines = semantic_analysis.lower().split("\n")
        
        for line in lines:
            for keyword in join_keywords:
                if keyword in line:
                    # Extract column names (simplified)
                    words = line.split()
                    for word in words:
                        if word.endswith("_id") or word.endswith("_key") or word.endswith("id"):
                            potential_keys.append(word.strip(",:;."))
        
        return list(set(potential_keys))
    
    def _extract_quality_notes(self, semantic_analysis: str) -> List[str]:
        """Extract data quality observations from analysis"""
        notes = []
        
        if "data quality" in semantic_analysis.lower():
            # Extract the data quality section
            lines = semantic_analysis.split("\n")
            in_quality_section = False
            
            for line in lines:
                if "data quality" in line.lower():
                    in_quality_section = True
                    continue
                
                if in_quality_section:
                    if line.strip().startswith("-") or line.strip().startswith("*"):
                        notes.append(line.strip().lstrip("-*").strip())
                    elif line.strip() and not line[0].isalpha():
                        break
        
        return notes

