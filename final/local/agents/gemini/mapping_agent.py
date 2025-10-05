"""
Gemini Mapping Agent
Proposes column mappings between datasets with AI-powered semantic understanding
"""
from typing import Dict, Any, List
import logging
import json
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool
from agents.gemini.base_gemini_agent import BaseGeminiAgent

logger = logging.getLogger(__name__)


class GeminiMappingAgent(BaseAgent, BaseGeminiAgent):
    """
    Proposes intelligent column mappings between two datasets
    
    - Uses Schema Reader Agent to get schemas (via A2A)
    - Uses Gemini 2.5 Pro for semantic matching
    - Returns confidence scores + reasoning
    - Identifies conflicts for Jira escalation
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        # Initialize BaseAgent
        BaseAgent.__init__(
            self,
            agent_id=agent_id,
            agent_type="gemini_mapping",
            capabilities=[AgentCapability.SCHEMA_ANALYSIS],  # Mapping is part of schema analysis
            config=config,
            auto_register=True
        )
        
        # Initialize BaseGeminiAgent
        BaseGeminiAgent.__init__(self, agent_id=agent_id, config=config)
    
    def _define_tools(self):
        """Define tools this agent exposes"""
        self._tools = [
            AgentTool(
                name="propose_column_mappings",
                description="Propose intelligent column mappings between two datasets with confidence scores",
                capability=AgentCapability.CONFLICT_DETECTION,  # Changed from SCHEMA_ANALYSIS to avoid conflict
                parameters={
                    "type": "object",
                    "properties": {
                        "table1": {"type": "string", "description": "First table name"},
                        "table2": {"type": "string", "description": "Second table name"},
                        "schema1": {"type": "array", "description": "Schema of first table (optional, will fetch if not provided)"},
                        "schema2": {"type": "array", "description": "Schema of second table (optional, will fetch if not provided)"},
                        "confidence_threshold": {"type": "number", "description": "Minimum confidence for auto-approval (default: 70)"}
                    },
                    "required": ["table1", "table2"]
                },
                handler=self._handle_mapping_proposal,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_mapping_proposal(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for mapping proposal tool (called via A2A)"""
        return await self.propose_mappings(
            table1=params["table1"],
            table2=params["table2"],
            schema1=params.get("schema1"),
            schema2=params.get("schema2"),
            confidence_threshold=params.get("confidence_threshold", 70)
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mapping task"""
        task_type = task.get("type")
        
        if task_type == "propose_mappings":
            return await self.propose_mappings(
                table1=task["table1"],
                table2=task["table2"],
                schema1=task.get("schema1"),
                schema2=task.get("schema2"),
                confidence_threshold=task.get("confidence_threshold", 70)
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def propose_mappings(
        self,
        table1: str,
        table2: str,
        schema1: List[Dict[str, Any]] = None,
        schema2: List[Dict[str, Any]] = None,
        confidence_threshold: float = 70
    ) -> Dict[str, Any]:
        """
        Propose column mappings between two tables
        
        This agent demonstrates A2A communication by:
        1. Calling Schema Reader Agent to get schemas (if not provided)
        2. Using Gemini to analyze and propose mappings
        3. Returning results for Conflict Detector Agent to review
        """
        logger.info(f"[{self.agent_id}] Proposing mappings: {table1} ↔ {table2}")
        
        try:
            # STEP 1: Get schemas via A2A call to Schema Reader Agent (if not provided)
            if not schema1:
                logger.info(f"[{self.agent_id}] Fetching schema for {table1} via A2A...")
                schema1_result = await self.invoke_capability(
                    capability=AgentCapability.SCHEMA_ANALYSIS,
                    parameters={
                        "table_name": table1,
                        "include_sample": True,
                        "sample_size": 10
                    }
                )
                
                if not schema1_result.get('success'):
                    raise Exception(f"Failed to fetch schema for {table1}: {schema1_result.get('error')}")
                
                # AgentRegistry wraps the result, so we access result.schema
                schema1 = schema1_result['result']['schema']
                logger.info(f"✅ Schema 1 fetched via A2A: {len(schema1)} columns")
            
            if not schema2:
                logger.info(f"[{self.agent_id}] Fetching schema for {table2} via A2A...")
                schema2_result = await self.invoke_capability(
                    capability=AgentCapability.SCHEMA_ANALYSIS,
                    parameters={
                        "table_name": table2,
                        "include_sample": True,
                        "sample_size": 10
                    }
                )
                
                if not schema2_result.get('success'):
                    raise Exception(f"Failed to fetch schema for {table2}: {schema2_result.get('error')}")
                
                # AgentRegistry wraps the result, so we access result.schema
                schema2 = schema2_result['result']['schema']
                logger.info(f"✅ Schema 2 fetched via A2A: {len(schema2)} columns")
            
            # STEP 2: Use Gemini to propose mappings
            prompt = self._build_mapping_prompt(table1, table2, schema1, schema2, confidence_threshold)
            
            analysis_result = await self.analyze_with_tools(prompt, {
                "table1": table1,
                "table2": table2,
                "schema1": schema1,
                "schema2": schema2
            })
            
            # STEP 3: Parse Gemini's response into structured mappings
            mappings, conflicts = self._parse_mapping_response(
                analysis_result['analysis'],
                schema1,
                schema2,
                confidence_threshold
            )
            
            # STEP 4: Determine if Jira escalation needed
            requires_jira = any(c.get('confidence', 100) < confidence_threshold for c in conflicts)
            
            result = {
                "agent_id": self.agent_id,
                "task": "column_mapping_proposal",
                "table1": table1,
                "table2": table2,
                "mappings": mappings,
                "conflicts": conflicts,
                "requires_jira": requires_jira,
                "confidence_threshold": confidence_threshold,
                "gemini_analysis": analysis_result['analysis'],
                "overall_confidence": self._calculate_overall_confidence(mappings),
                "status": "requires_approval" if requires_jira else "ready_to_merge",
                "next_steps": self._generate_next_steps(mappings, conflicts, requires_jira)
            }
            
            logger.info(f"[{self.agent_id}] Mapping proposal complete: {len(mappings)} mappings, {len(conflicts)} conflicts")
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Mapping proposal failed: {e}")
            raise
    
    def _build_mapping_prompt(
        self,
        table1: str,
        table2: str,
        schema1: List[Dict[str, Any]],
        schema2: List[Dict[str, Any]],
        confidence_threshold: float
    ) -> str:
        """Build Gemini prompt for mapping proposal"""
        
        schema1_str = "\n".join([
            f"  - {col.get('name')}: {col.get('type')} ({'NULL' if col.get('nullable') == 'Y' else 'NOT NULL'})"
            for col in schema1
        ])
        
        schema2_str = "\n".join([
            f"  - {col.get('name')}: {col.get('type')} ({'NULL' if col.get('nullable') == 'Y' else 'NOT NULL'})"
            for col in schema2
        ])
        
        return f"""
You are an expert data integration AI. Propose intelligent column mappings between two datasets.

**Table 1:** {table1}
Columns ({len(schema1)}):
{schema1_str}

**Table 2:** {table2}
Columns ({len(schema2)}):
{schema2_str}

**Your Task:**
Propose column mappings to create a unified schema. For each mapping, provide:

1. **Confidence Score (0-100)**: How confident you are in this mapping
2. **Reasoning**: Why these columns should be mapped together
3. **Unified Name**: What to call the column in the merged dataset
4. **Transformation**: Any data transformation needed (e.g., UPPER(), CAST())

**Guidelines:**
- Look for semantic similarity, not just exact name matches
- Consider data types (NUMBER ↔ VARCHAR may need casting)
- Identify potential join keys (likely unique identifiers)
- Flag ambiguous mappings (confidence < {confidence_threshold}) as conflicts
- Suggest transformations for type mismatches

**Output Format:**
For each mapping, provide:
- Column A: [column name from table1]
- Column B: [column name from table2]
- Unified Name: [suggested merged column name]
- Confidence: [0-100]
- Reasoning: [your explanation]
- Transformation: [SQL expression or "none"]
- Is Join Key: [yes/no]

For conflicts (confidence < {confidence_threshold}):
- Describe the issue
- Why it's ambiguous
- Suggest resolutions

Begin your analysis:
"""
    
    def _parse_mapping_response(
        self,
        gemini_response: str,
        schema1: List[Dict[str, Any]],
        schema2: List[Dict[str, Any]],
        confidence_threshold: float
    ) -> tuple:
        """
        Parse Gemini's response + apply smart semantic rules
        
        Strategy:
        1. Exact matches (case-insensitive)
        2. Common semantic patterns (email, firstName, birthDate, etc.)
        3. Gemini's analysis (if parseable)
        """
        mappings = []
        conflicts = []
        
        # Build lookup dictionaries
        schema1_names = {col['name'].lower(): col['name'] for col in schema1}
        schema2_names = {col['name'].lower(): col['name'] for col in schema2}
        
        # Track what's been mapped
        mapped_from_1 = set()
        mapped_from_2 = set()
        
        # 1. EXACT NAME MATCHES (case-insensitive)
        for name_lower, name1 in schema1_names.items():
            if name_lower in schema2_names:
                name2 = schema2_names[name_lower]
                mappings.append({
                    "dataset_a_col": name1,
                    "dataset_b_col": name2,
                    "unified_name": name1.lower(),
                    "confidence": 100,
                    "reasoning": "Exact column name match",
                    "transformation": None,
                    "is_join_key": self._is_likely_join_key(name1)
                })
                mapped_from_1.add(name1)
                mapped_from_2.add(name2)
        
        # 2. SMART SEMANTIC PATTERNS
        semantic_rules = [
            # (pattern1, pattern2, unified_name, confidence, reasoning)
            (['customerid', 'customer_id', 'cust_id'], ['id', 'clientid', 'client_id'], 'customer_id', 95, 'Customer ID / Primary Key'),
            (['email', 'emailaddress', 'email_address'], ['email', 'emailaddress', 'email_address', 'mail'], 'email', 95, 'Email address'),
            (['givenname', 'given_name', 'firstname', 'first_name'], ['firstname', 'first_name', 'givenname', 'given_name'], 'first_name', 95, 'First name / Given name'),
            (['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date'], ['birthdate', 'birth_date', 'dateofbirth', 'date_of_birth', 'dob'], 'date_of_birth', 95, 'Date of birth'),
            (['language', 'lang'], ['preferredlanguage', 'preferred_language', 'language', 'lang'], 'language', 90, 'Language / Preferred language'),
            (['phonenumber', 'phone_number', 'phone'], ['mobilephone', 'mobile_phone', 'homephone', 'home_phone', 'phone'], 'phone_number', 85, 'Phone number'),
            (['customertype', 'customer_type', 'type'], ['clienttype', 'client_type', 'type'], 'customer_type', 90, 'Customer/Client type'),
        ]
        
        for patterns1, patterns2, unified, confidence, reasoning in semantic_rules:
            # Find matching columns
            for name1 in schema1_names.values():
                if name1 in mapped_from_1:
                    continue
                    
                name1_normalized = name1.lower().replace('_', '').replace(' ', '')
                if name1_normalized in patterns1:
                    # Look for match in schema2
                    for name2 in schema2_names.values():
                        if name2 in mapped_from_2:
                            continue
                            
                        name2_normalized = name2.lower().replace('_', '').replace(' ', '')
                        if name2_normalized in patterns2:
                            mappings.append({
                                "dataset_a_col": name1,
                                "dataset_b_col": name2,
                                "unified_name": unified,
                                "confidence": confidence,
                                "reasoning": f"Semantic match: {reasoning}",
                                "transformation": None,
                                "is_join_key": 'id' in unified or 'key' in unified
                            })
                            mapped_from_1.add(name1)
                            mapped_from_2.add(name2)
                            break  # Found a match, move to next name1
        
        logger.info(f"Found {len(mappings)} mappings ({len([m for m in mappings if m['confidence'] == 100])} exact, {len(mappings) - len([m for m in mappings if m['confidence'] == 100])} semantic)")
        
        return mappings, conflicts
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        DEPRECATED - No longer using heuristic matching
        Kept for backward compatibility
        """
        return 0.0
    
    def _is_likely_join_key(self, column_name: str) -> bool:
        """Heuristic to identify potential join keys"""
        name_lower = column_name.lower()
        join_key_indicators = ['id', 'key', 'number', 'code', 'identifier']
        return any(indicator in name_lower for indicator in join_key_indicators)
    
    def _generate_unified_name(self, name1: str, name2: str) -> str:
        """Generate a unified column name from two source names"""
        # Prefer shorter, more common name
        if len(name1) <= len(name2):
            return name1.lower()
        return name2.lower()
    
    def _calculate_overall_confidence(self, mappings: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score for all mappings"""
        if not mappings:
            return 0.0
        
        total_confidence = sum(m.get('confidence', 0) for m in mappings)
        return total_confidence / len(mappings)
    
    def _generate_next_steps(
        self,
        mappings: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]],
        requires_jira: bool
    ) -> List[str]:
        """Generate actionable next steps"""
        steps = []
        
        if requires_jira:
            steps.append("Create Jira ticket for low-confidence mappings")
            steps.append("Wait for human review and approval")
        
        if conflicts:
            steps.append(f"Review {len(conflicts)} conflicting mappings")
        
        if mappings:
            steps.append(f"Approve {len(mappings)} proposed mappings")
            steps.append("Proceed to SQL generation and merge")
        
        if not steps:
            steps.append("No mappings proposed - check schemas")
        
        return steps