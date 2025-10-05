"""
Base Gemini Agent - Foundation for all Gemini-powered agents
Uses Gemini 2.5 Pro with function calling to understand available tools
"""
import google.generativeai as genai
from typing import Dict, Any, List, Optional
import logging
from core.config import settings
import json

logger = logging.getLogger(__name__)


class BaseGeminiAgent:
    """
    Base class for Gemini-powered agents
    Provides function calling, tool awareness, and structured output
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        self.agent_id = agent_id
        self.config = config or {}
        
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',  # Using Gemini 2.5 Pro for superior reasoning
            generation_config={
                "temperature": 0.3,  # Low temperature for deterministic outputs
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )
        
        # Available Snowflake tools this agent can recommend
        self.available_tools = self._define_available_tools()
        
        logger.info(f"✅ Initialized {self.__class__.__name__} [{agent_id}] with Gemini 2.5 Pro")
    
    def _define_available_tools(self) -> List[Dict[str, Any]]:
        """
        Define the Snowflake tools available to this agent
        Gemini will understand these and recommend which to use
        """
        return [
            {
                "name": "read_table_schema",
                "description": "Read the schema (column names, types, sample data) from a Snowflake table",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Full table name in Snowflake (e.g., RAW_session_001_DATASET_1)"
                        },
                        "include_sample": {
                            "type": "boolean",
                            "description": "Whether to include sample rows (default: true)"
                        },
                        "sample_size": {
                            "type": "integer",
                            "description": "Number of sample rows to fetch (default: 10)"
                        }
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "execute_sql_query",
                "description": "Execute a SQL query on Snowflake and return results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute"
                        },
                        "explain": {
                            "type": "boolean",
                            "description": "Whether to return query explanation (default: false)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_column_statistics",
                "description": "Get statistical information about specific columns (null count, distinct values, min/max, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Table name to analyze"
                        },
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of column names to analyze"
                        }
                    },
                    "required": ["table_name", "columns"]
                }
            },
            {
                "name": "detect_conflicts",
                "description": "Detect data conflicts between two tables (duplicates, type mismatches, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table1": {"type": "string"},
                        "table2": {"type": "string"},
                        "join_columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Columns to use for conflict detection"
                        }
                    },
                    "required": ["table1", "table2", "join_columns"]
                }
            }
        ]
    
    async def analyze_with_tools(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze a problem using Gemini with tool awareness
        Returns recommended tools and reasoning
        """
        try:
            # Build full prompt with tool context
            full_prompt = self._build_tool_aware_prompt(prompt, context or {})
            
            # Get Gemini's analysis
            response = self.model.generate_content(full_prompt)
            
            # Parse response
            result = {
                "agent_id": self.agent_id,
                "analysis": response.text,
                "recommended_tools": self._extract_tool_recommendations(response.text),
                "confidence": self._extract_confidence(response.text)
            }
            
            logger.info(f"[{self.agent_id}] Analysis complete: {len(result['recommended_tools'])} tools recommended")
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Analysis failed: {e}")
            raise
    
    def _build_tool_aware_prompt(self, user_prompt: str, context: Dict[str, Any]) -> str:
        """Build a prompt that includes available tool descriptions"""
        tools_desc = "\n\n".join([
            f"**{tool['name']}**: {tool['description']}\nParameters: {json.dumps(tool['parameters'], indent=2)}"
            for tool in self.available_tools
        ])
        
        context_str = json.dumps(context, indent=2) if context else "No additional context"
        
        return f"""You are an expert data integration AI agent with access to Snowflake tools.

## Available Tools:
{tools_desc}

## Context:
{context_str}

## Your Task:
{user_prompt}

## Instructions:
1. Analyze the task carefully
2. Recommend which tools to use (do NOT execute them yourself)
3. Provide step-by-step reasoning
4. Include SQL queries if relevant
5. Identify any potential conflicts or issues
6. Rate your confidence (0.0-1.0)

## Response Format:
Provide a structured analysis with:
- Recommended Tools: List of tool names and parameters
- Reasoning: Why these tools are needed
- Proposed SQL: Any SQL queries to run
- Conflicts: Any issues detected
- Confidence: Your confidence score

Begin your analysis:"""
    
    def _extract_tool_recommendations(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract tool recommendations from Gemini's response"""
        # Simple extraction - look for tool names in response
        recommendations = []
        for tool in self.available_tools:
            if tool['name'] in response_text.lower():
                recommendations.append({
                    "tool": tool['name'],
                    "reason": "Mentioned in analysis"
                })
        return recommendations
    
    def _extract_confidence(self, response_text: str) -> float:
        """Extract confidence score from response"""
        # Look for confidence patterns
        import re
        confidence_patterns = [
            r"confidence[:\s]+([0-9.]+)",
            r"confidence score[:\s]+([0-9.]+)",
            r"([0-9.]+)/1\.0",
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, response_text.lower())
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        
        return 0.85  # Default confidence
    
    async def _generate_content(self, prompt: str) -> Dict[str, Any]:
        """
        Simple content generation helper
        Returns text response from Gemini
        """
        try:
            response = self.model.generate_content(prompt)
            return {
                "text": response.text,
                "success": True
            }
        except Exception as e:
            logger.error(f"[{self.agent_id}] Content generation failed: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Base execute method - override in subclasses
        """
        raise NotImplementedError("Subclasses must implement execute()")
