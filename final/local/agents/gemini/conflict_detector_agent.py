"""
Gemini Conflict Detection Agent
Detects data conflicts, type mismatches, and integration issues between datasets
"""
from typing import Dict, Any, List
import logging
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool
from agents.gemini.base_gemini_agent import BaseGeminiAgent
from sf_infrastructure.connector import snowflake_connector

logger = logging.getLogger(__name__)


class GeminiConflictDetectorAgent(BaseAgent, BaseGeminiAgent):
    """
    Detects conflicts between datasets before merging
    - Schema conflicts (type mismatches)
    - Data conflicts (duplicates, inconsistent values)
    - Referential integrity issues
    - Semantic conflicts (same column, different meaning)
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        # Initialize BaseAgent
        BaseAgent.__init__(
            self,
            agent_id=agent_id,
            agent_type="gemini_conflict_detector",
            capabilities=[AgentCapability.CONFLICT_DETECTION],
            config=config,
            auto_register=True
        )
        
        # Initialize BaseGeminiAgent
        BaseGeminiAgent.__init__(self, agent_id=agent_id, config=config)
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="detect_data_conflicts",
                description="Detect conflicts between two datasets using Gemini AI (type mismatches, duplicates, semantic conflicts)",
                capability=AgentCapability.CONFLICT_DETECTION,
                parameters={
                    "type": "object",
                    "properties": {
                        "table1": {"type": "string"},
                        "table2": {"type": "string"},
                        "schema1": {"type": "array"},
                        "schema2": {"type": "array"},
                        "proposed_mappings": {"type": "array"}
                    },
                    "required": ["table1", "table2", "schema1", "schema2"]
                },
                handler=self._handle_conflict_detection,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_conflict_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for conflict detection (called via A2A)"""
        return await self.detect_all_conflicts(
            table1=params["table1"],
            table2=params["table2"],
            schema1=params["schema1"],
            schema2=params["schema2"],
            proposed_mappings=params.get("proposed_mappings", [])
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute conflict detection task
        
        Expected task format:
        {
            "type": "detect_conflicts",
            "table1": "RAW_session_001_DATASET_1",
            "table2": "RAW_session_001_DATASET_2",
            "schema1": [...],
            "schema2": [...],
            "proposed_mappings": [{"left": "customer_id", "right": "client_id"}]
        }
        """
        task_type = task.get("type")
        
        if task_type == "detect_conflicts":
            return await self.detect_all_conflicts(
                table1=task["table1"],
                table2=task["table2"],
                schema1=task.get("schema1", []),
                schema2=task.get("schema2", []),
                proposed_mappings=task.get("proposed_mappings", [])
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def detect_all_conflicts(
        self,
        table1: str,
        table2: str,
        schema1: List[Dict[str, Any]],
        schema2: List[Dict[str, Any]],
        proposed_mappings: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Comprehensive conflict detection between two tables
        """
        logger.info(f"[{self.agent_id}] Detecting conflicts between {table1} and {table2}")
        
        try:
            # Step 1: Schema-level conflict detection
            schema_conflicts = self._detect_schema_conflicts(schema1, schema2, proposed_mappings)
            
            # Step 2: Sample data for value-level checks
            sample1 = await self._get_sample_data(table1, 20)
            sample2 = await self._get_sample_data(table2, 20)
            
            # Step 3: Ask Gemini to analyze conflicts
            prompt = f"""
Analyze potential conflicts between these two datasets:

**Dataset 1:** {table1}
Schema: {self._format_schema(schema1)}
Sample (first 3 rows): {self._format_sample(sample1[:3])}

**Dataset 2:** {table2}
Schema: {self._format_schema(schema2)}
Sample (first 3 rows): {self._format_sample(sample2[:3])}

**Proposed Column Mappings:**
{self._format_mappings(proposed_mappings)}

**Detected Schema Conflicts:**
{self._format_conflicts(schema_conflicts)}

Analyze and identify:
1. **Type Conflicts**: Where mapped columns have incompatible types
2. **Value Conflicts**: Where data ranges don't overlap or have different formats
3. **Semantic Conflicts**: Where column names suggest different meanings
4. **Duplicate Risks**: Potential for duplicate records after merge
5. **Data Quality Issues**: Missing values, outliers, inconsistent formats
6. **Resolution Strategies**: How to resolve each conflict

Rate each conflict by severity: CRITICAL, HIGH, MEDIUM, LOW

Provide actionable recommendations with SQL snippets for resolution.
"""
            
            analysis_result = await self.analyze_with_tools(prompt, {
                "table1": table1,
                "table2": table2,
                "schema_conflicts": schema_conflicts
            })
            
            # Step 4: Structure results
            conflicts = self._parse_conflicts_from_response(
                analysis_result['analysis'],
                schema_conflicts
            )
            
            result = {
                "agent_id": self.agent_id,
                "task": "conflict_detection",
                "table1": table1,
                "table2": table2,
                "conflicts": conflicts,
                "gemini_analysis": analysis_result['analysis'],
                "severity_summary": self._summarize_severity(conflicts),
                "recommended_actions": self._extract_recommendations(analysis_result['analysis']),
                "confidence": analysis_result['confidence'],
                "requires_human_review": self._needs_human_review(conflicts)
            }
            
            logger.info(f"[{self.agent_id}] Detected {len(conflicts)} conflicts")
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Conflict detection failed: {e}")
            raise
    
    def _detect_schema_conflicts(
        self,
        schema1: List[Dict[str, Any]],
        schema2: List[Dict[str, Any]],
        mappings: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Detect schema-level conflicts (type mismatches, etc.)
        """
        conflicts = []
        
        for mapping in mappings:
            left_col = mapping.get("left")
            right_col = mapping.get("right")
            
            # Find column definitions
            left_def = next((c for c in schema1 if c.get("name") == left_col), None)
            right_def = next((c for c in schema2 if c.get("name") == right_col), None)
            
            if not left_def or not right_def:
                conflicts.append({
                    "type": "MISSING_COLUMN",
                    "severity": "CRITICAL",
                    "left_column": left_col,
                    "right_column": right_col,
                    "description": f"Column not found in schema"
                })
                continue
            
            # Type mismatch detection
            left_type = left_def.get("type", "").upper()
            right_type = right_def.get("type", "").upper()
            
            if not self._types_compatible(left_type, right_type):
                conflicts.append({
                    "type": "TYPE_MISMATCH",
                    "severity": "HIGH",
                    "left_column": left_col,
                    "right_column": right_col,
                    "left_type": left_type,
                    "right_type": right_type,
                    "description": f"Type mismatch: {left_type} vs {right_type}"
                })
        
        return conflicts
    
    def _types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two SQL types are compatible"""
        # Simplify types (remove precision)
        type1 = type1.split("(")[0]
        type2 = type2.split("(")[0]
        
        # Numeric types are compatible with each other
        numeric_types = ["NUMBER", "INT", "INTEGER", "BIGINT", "FLOAT", "DECIMAL", "NUMERIC"]
        if type1 in numeric_types and type2 in numeric_types:
            return True
        
        # String types are compatible
        string_types = ["VARCHAR", "CHAR", "TEXT", "STRING"]
        if type1 in string_types and type2 in string_types:
            return True
        
        # Date/timestamp types
        date_types = ["DATE", "TIMESTAMP", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ"]
        if type1 in date_types and type2 in date_types:
            return True
        
        # Exact match
        return type1 == type2
    
    async def _get_sample_data(self, table_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get sample data from table"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return await snowflake_connector.execute_query(query)
        except Exception as e:
            logger.warning(f"Could not fetch sample data: {e}")
            return []
    
    def _format_schema(self, schema: List[Dict[str, Any]]) -> str:
        """Format schema for prompt"""
        return "\n".join([
            f"  - {col.get('name')}: {col.get('type')}"
            for col in schema
        ])
    
    def _format_sample(self, sample: List[Dict[str, Any]]) -> str:
        """Format sample data"""
        if not sample:
            return "No sample data"
        return str(sample)[:500]  # Truncate for prompt
    
    def _format_mappings(self, mappings: List[Dict[str, str]]) -> str:
        """Format mappings for prompt"""
        if not mappings:
            return "No mappings provided"
        return "\n".join([
            f"  {m.get('left')} ← → {m.get('right')}"
            for m in mappings
        ])
    
    def _format_conflicts(self, conflicts: List[Dict[str, Any]]) -> str:
        """Format detected conflicts"""
        if not conflicts:
            return "No schema conflicts detected"
        return "\n".join([
            f"  [{c.get('severity')}] {c.get('type')}: {c.get('description')}"
            for c in conflicts
        ])
    
    def _parse_conflicts_from_response(
        self,
        response: str,
        schema_conflicts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse conflicts from Gemini's response"""
        # Start with detected schema conflicts
        all_conflicts = list(schema_conflicts)
        
        # Try to extract additional conflicts from response
        # Look for severity keywords
        import re
        severity_pattern = r"\[(CRITICAL|HIGH|MEDIUM|LOW)\](.*?)(?=\[|$)"
        matches = re.findall(severity_pattern, response, re.DOTALL)
        
        for severity, description in matches:
            all_conflicts.append({
                "type": "GEMINI_DETECTED",
                "severity": severity,
                "description": description.strip()[:200]
            })
        
        return all_conflicts
    
    def _summarize_severity(self, conflicts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize conflicts by severity"""
        summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for conflict in conflicts:
            severity = conflict.get("severity", "MEDIUM")
            summary[severity] = summary.get(severity, 0) + 1
        return summary
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract actionable recommendations"""
        # Simple extraction - look for numbered lists or bullet points
        lines = response.split("\n")
        recommendations = []
        for line in lines:
            if line.strip().startswith(("1.", "2.", "3.", "-", "•")):
                recommendations.append(line.strip())
        return recommendations[:10]  # Top 10
    
    def _needs_human_review(self, conflicts: List[Dict[str, Any]]) -> bool:
        """Determine if human review is required"""
        critical_count = sum(1 for c in conflicts if c.get("severity") == "CRITICAL")
        high_count = sum(1 for c in conflicts if c.get("severity") == "HIGH")
        return critical_count > 0 or high_count > 2
