"""
Gemini Agent Suite - Modular AI agents powered by Gemini 2.0 Flash

All agents follow the same pattern:
1. Analyze using Gemini's intelligence
2. Recommend Snowflake tools to use
3. Propose SQL/actions but DO NOT execute
4. Return structured results for user approval
5. Communicate via A2A (Agent-to-Agent) registry
"""
from agents.gemini.base_gemini_agent import BaseGeminiAgent
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
from agents.gemini.mapping_agent import GeminiMappingAgent
from agents.gemini.sql_generator_agent import GeminiSQLGeneratorAgent
from agents.gemini.conflict_detector_agent import GeminiConflictDetectorAgent

__all__ = [
    "BaseGeminiAgent",
    "GeminiSchemaReaderAgent",
    "GeminiMappingAgent",
    "GeminiSQLGeneratorAgent",
    "GeminiConflictDetectorAgent",
]