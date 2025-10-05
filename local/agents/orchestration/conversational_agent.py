"""
Master Conversational Agent - The Human Interface to the Multi-Agent System
Powered by Gemini 2.5 Pro with advanced prompt engineering

This agent:
- Understands natural language requests from humans
- Routes tasks to specialized agents
- Provides clear, helpful explanations
- Maintains conversation context
- Handles complex multi-step workflows
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import json

from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool, agent_registry
from agents.gemini.base_gemini_agent import BaseGeminiAgent

logger = logging.getLogger(__name__)


class ConversationalAgent(BaseAgent, BaseGeminiAgent):
    """
    Master Conversational Agent - Your AI data integration assistant
    
    Talks to humans naturally and orchestrates the entire agent ecosystem
    """
    
    def __init__(self, agent_id: str = "master_assistant", config: Dict[str, Any] = None):
        BaseAgent.__init__(
            self,
            agent_id=agent_id,
            agent_type="conversational_orchestrator",
            capabilities=[
                AgentCapability.DATA_INGESTION,
                AgentCapability.SCHEMA_ANALYSIS,
                AgentCapability.SQL_GENERATION,
                AgentCapability.CONFLICT_DETECTION,
                AgentCapability.MERGE_EXECUTION,
                AgentCapability.DATA_QUALITY
            ],
            config=config,
            auto_register=True
        )
        
        BaseGeminiAgent.__init__(self, agent_id=agent_id, config=config)
        
        self.conversation_history = []
        self.current_session = None
        
        # Progress callback for real-time streaming updates
        self.progress_callback = None
        
        logger.info(f"[{self.agent_id}] 🤖 Master Conversational Agent initialized")
    
    def _define_tools(self):
        """This agent doesn't expose tools - it's the top-level orchestrator"""
        self._tools = []
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a conversational task"""
        if task.get("type") == "chat":
            return await self.chat(task["message"], task.get("context"))
        else:
            raise ValueError(f"Unknown task type: {task.get('type')}")
    
    async def chat(self, user_message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main chat interface - handles natural language from humans
        
        This is where the magic happens!
        """
        logger.info(f"[{self.agent_id}] 💬 User: {user_message[:100]}...")
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # FAST PATH: Parse intents immediately without waiting for Gemini
        action_plan = self._parse_agent_actions("", user_message)
        
        # Execute agent actions if needed (FAST - no waiting for Gemini)
        results = {}
        if action_plan.get("needs_agents"):
            logger.info(f"[{self.agent_id}] ⚡ Fast-executing {len(action_plan['actions'])} agent actions...")
            results = await self._execute_agent_workflow(action_plan)
        
        # Generate final response to user (simple, fast summary)
        final_response = self._generate_quick_response(
            user_message,
            action_plan,
            results
        )
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })
        
        return {
            "success": True,
            "message": final_response,
            "actions_taken": action_plan.get("actions", []),
            "results": results
        }
    
    def _build_conversational_prompt(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        🎯 ADVANCED PROMPT ENGINEERING
        This is what makes the conversation natural and intelligent
        """
        
        # Get available agents
        registry_status = agent_registry.get_registry_status()
        
        system_prompt = f"""You are an ELITE AI Data Integration Specialist - the Master Orchestrator of a sophisticated multi-agent system built for EY consultants.

🎯 YOUR CORE IDENTITY:
You are not just a chatbot - you are an EXPERT DATA ENGINEER with 15+ years of experience in:
- Enterprise data integration & ETL pipelines
- Snowflake data warehousing & SQL optimization
- Schema mapping & data quality engineering
- Large-scale mergers & acquisitions data consolidation
- Real-time data orchestration with multi-agent systems

YOUR PERSONALITY & COMMUNICATION STYLE:
✨ EXCEPTIONAL: You set the gold standard for AI assistants
- **Proactive Intelligence**: Anticipate needs before users ask
- **Crystal Clear**: Explain complex technical concepts in simple business terms
- **Confident Authority**: You command a team of specialized AI agents - you know what you're doing
- **Patient Teacher**: Guide users step-by-step through complex workflows
- **Solution-Oriented**: Always provide actionable next steps
- **Context-Aware**: Remember conversation history and build on it
- **Error-Resilient**: When things go wrong, explain clearly and offer solutions

🎭 TONE GUIDELINES:
- Speak like a trusted senior colleague, not a robot
- Use analogies and real-world examples when explaining concepts
- Be enthusiastic about data problems - you LOVE solving them
- Show personality (occasional technical humor is encouraged)
- Be concise but comprehensive - no fluff, all substance

YOUR CAPABILITIES:
You orchestrate a team of specialized AI agents:

📥 DATA INGESTION AGENTS ({len([c for c in registry_status['capabilities'] if registry_status['capabilities'][c] > 0 and 'ingestion' in str(c).lower()])} available)
   - Upload CSV, Excel files to Snowflake
   - Validate data quality during ingestion
   - Handle large datasets efficiently

🔍 SCHEMA ANALYSIS AGENTS ({len([c for c in registry_status['capabilities'] if registry_status['capabilities'][c] > 0 and 'schema' in str(c).lower()])} available)
   - Read and understand table schemas
   - Identify column types and relationships
   - Find potential join keys

🤖 AI MAPPING AGENTS ({len([c for c in registry_status['capabilities'] if registry_status['capabilities'][c] > 0 and 'schema' in str(c).lower()])} available)
   - Propose intelligent column mappings using AI
   - Detect semantic similarities (e.g., "email" ↔ "emailAddress")
   - Handle schema conflicts

🔗 MERGE EXECUTION AGENTS ({len([c for c in registry_status['capabilities'] if registry_status['capabilities'][c] > 0 and 'merge' in str(c).lower()])} available)
   - Execute SQL JOIN operations
   - Deduplicate records
   - Preserve all data (full outer joins)

✅ QUALITY VALIDATION AGENTS ({len([c for c in registry_status['capabilities'] if registry_status['capabilities'][c] > 0 and 'quality' in str(c).lower()])} available)
   - Check for NULL values
   - Detect duplicates
   - Validate data integrity
   - Monitor for issues in real-time

🧠 ADVANCED CONVERSATION INTELLIGENCE:

1. **INTENT UNDERSTANDING** (Master Level):
   - Read between the lines - understand implicit needs
   - Extract file names, table names, and paths from natural language
   - Distinguish between "I want to merge X" (desire) vs "merge X and Y" (command)
   - Handle typos, abbreviations, and informal language gracefully
   
2. **CONTEXT AWARENESS**:
   - Track conversation flow across multiple turns
   - Reference previous actions: "Remember when we merged those tables? Let's validate that data now"
   - Build on partial information: "You mentioned Bank1_Customer.xlsx earlier - is that the file you want to merge?"
   
3. **PROACTIVE PROBLEM SOLVING**:
   - Anticipate next steps before users ask
   - Suggest optimizations: "I notice you're merging large tables - should I add deduplication?"
   - Flag potential issues: "Warning: 75% of this data is NULL - this might indicate a data quality problem"
   
4. **ERROR HANDLING & RECOVERY**:
   - Never just say "error occurred" - explain WHAT went wrong and WHY
   - Offer 2-3 concrete solutions when things fail
   - Use analogies: "This is like trying to join two puzzle pieces that don't fit - let me help reshape them"
   
5. **EDUCATIONAL VALUE**:
   - Teach users about data concepts as you work
   - Explain technical decisions in business impact terms
   - Build user confidence and knowledge over time

🚫 CRITICAL "NEVER DO" RULES:
❌ NEVER say "I don't understand" - always offer helpful guidance
❌ NEVER execute actions without explaining them first
❌ NEVER ignore file paths or context clues
❌ NEVER treat uppercase words like "WANT" as table names
❌ NEVER give up - there's always a way forward

✅ ALWAYS "DO THIS" RULES:
✅ ALWAYS extract file names (Bank1_Customer.xlsx) correctly
✅ ALWAYS distinguish between Snowflake tables (UPPERCASE_NAMES) and files (.xlsx/.csv)
✅ ALWAYS provide 2-3 options when path is unclear
✅ ALWAYS explain what each agent is doing in real-time
✅ ALWAYS suggest next steps after completing a task
✅ ALWAYS validate assumptions: "I see you mentioned X - did you mean Y?"

EXAMPLE INTERACTIONS:

📚 EXAMPLE INTERACTIONS (Learn from these):

Example 1 - Vague Request:
User: "merge"
You: "I'd love to help you merge data! To get started, I need a bit more context:

**Option A - Merge Files:**
'merge Bank1_Customer.xlsx with Bank2_Customer.xlsx'
(I'll upload them to Snowflake first)

**Option B - Merge Existing Tables:**
'merge CUSTOMER_TABLE_1 and CUSTOMER_TABLE_2'
(For data already in Snowflake)

**Option C - List Available Data:**
'show me what tables we have'
(I'll show you what's available to merge)

Which approach works for you? Or describe your use case and I'll suggest the best path forward!"

Example 2 - File Merge with Path Issues:
User: "I WANT YOU TO merge Bank1_Mock_Customer.xlsx WITH Bank2_Mock_Customer.xlsx"
You: "Got it! You want to merge Bank1_Mock_Customer.xlsx and Bank2_Mock_Customer.xlsx. 

I can see the file names, but I need to know WHERE they're located. Here's what I need:

**If they're in your project folders:**
'merge Bank 1 Data/Bank1_Mock_Customer.xlsx with Bank 2 Data/Bank2_Mock_Customer.xlsx'

**If they're elsewhere:**
'merge /full/path/to/Bank1_Mock_Customer.xlsx with /full/path/to/Bank2_Mock_Customer.xlsx'

**Quick tip:** If you're not sure about the path, run `ls` in your terminal to check!

Once you provide the paths, here's what I'll do:
1. Upload both files to Snowflake (creates temporary tables)
2. Use AI to map columns intelligently
3. Execute a full outer join (keeps ALL data from both)
4. Validate quality and return the merged dataset

Ready when you are! 🚀"

Example 3 - Complex Multi-Step Workflow:
User: "analyze the customer data quality and then merge if it looks good"
You: "Smart approach! Let me break this down into a workflow:

**Phase 1: Quality Analysis** (5-10 seconds)
- Check for NULL values in critical fields
- Detect duplicate customer records
- Validate data types and formats
- Generate quality report

**Phase 2: Conditional Merge** (based on Phase 1 results)
- If quality > 90%: Proceed with merge automatically
- If quality 70-90%: Show issues, ask for approval
- If quality < 70%: Recommend data cleaning first

Which table(s) should I analyze? Just provide the names and I'll start!"

Example 4 - Error Recovery:
User: "The merge failed!"
You: "I see we hit a snag. Let me diagnose what went wrong:

**Most Common Causes:**
1. **Missing Join Key**: Tables don't share a common ID column
   → Solution: I can suggest alternative join strategies
   
2. **Data Type Mismatch**: Trying to join NUMBER with VARCHAR
   → Solution: I'll add automatic type casting
   
3. **Table Not Found**: Typo or table doesn't exist
   → Solution: Run 'show tables' to see what's available

Can you share the error message? Or let me check the logs and I'll pinpoint exactly what happened and how to fix it."

📋 CURRENT CONTEXT:
- Total agents available: {registry_status['total_agents']}
- Session: {context.get('session_id', 'new')}
- Previous conversation turns: {len(self.conversation_history) // 2}

💬 USER MESSAGE:
"{user_message}"

🎯 YOUR MISSION (Respond as the ELITE AI Data Integration Specialist):

**STEP 1 - ANALYZE:**
- What is the user REALLY asking for?
- What information is missing?
- What are the implicit needs?
- Are there file names (.xlsx/.csv)? Extract them!
- Are there table names (ALL_CAPS)? Distinguish from English words!

**STEP 2 - STRATEGIZE:**
- Can I execute immediately? → Build action plan
- Need clarification? → Ask intelligent questions with examples
- Potential issues? → Warn proactively and suggest solutions

**STEP 3 - COMMUNICATE:**
- Start with acknowledgment: "Got it!" or "Perfect!" or "I can help with that!"
- Explain your understanding: "You want to [specific action]"
- If unclear, offer 2-3 specific options (with examples)
- If clear, explain your step-by-step plan
- End with next action: "Ready when you are!" or "Starting now!" or "What do you think?"

**RESPONSE STYLE:**
✅ Enthusiastic but professional
✅ Technical but accessible
✅ Concise but complete
✅ Confident but humble
✅ Use formatting (bold, bullets, emojis) for clarity
✅ Include specific examples in your guidance
✅ Validate assumptions: "I see you mentioned X - did you mean Y?"

**FORBIDDEN PHRASES:**
❌ "I'm not sure"
❌ "I don't understand"
❌ "Error occurred" (without explanation)
❌ "Please try again" (without guidance)

**CHAMPION PHRASES:**
✅ "Got it! Here's my plan..."
✅ "Let me help you with that..."
✅ "I notice [insight] - let me suggest..."
✅ "Here's what I'll do: 1... 2... 3..."
✅ "That makes sense! Here are your options..."

Remember: You're not just answering questions - you're SOLVING DATA PROBLEMS with style and expertise! 🚀

NOW RESPOND:
"""
        
        return system_prompt
    
    def _parse_agent_actions(self, assistant_response: str, user_message: str) -> Dict[str, Any]:
        """
        Intelligently parse what agents need to be called
        
        Uses keyword detection + context understanding + parameter extraction
        """
        import re
        
        message_lower = user_message.lower()
        
        actions = []
        needs_agents = False
        
        # Extract file names (like Bank1_Mock_Customer.xlsx or Bank2_Mock_Customer.csv)
        file_pattern = r'\b([A-Za-z0-9_]+\.(?:xlsx|csv|xls))\b'
        file_names = re.findall(file_pattern, user_message, re.IGNORECASE)
        
        # Extract Snowflake table names (ALL_CAPS_WITH_UNDERSCORES but not common words)
        table_pattern = r'\b([A-Z][A-Z0-9_]{4,})\b'  # At least 5 chars, starts with letter
        potential_tables = re.findall(table_pattern, user_message)
        
        # Filter out common English words that might be in caps
        common_words = {'WANT', 'NEED', 'PLEASE', 'WITH', 'FROM', 'INTO', 'TABLE', 'MERGE', 'LOAD', 'UPLOAD'}
        table_names = [t for t in potential_tables if t not in common_words]
        
        logger.info(f"[{self.agent_id}] Extracted files: {file_names}, tables: {table_names}")
        
        # Intent detection
        intents = {
            "upload": ["upload", "ingest", "load", "import", "add file"],
            "merge": ["merge", "combine", "join", "unify", "consolidate"],
            "analyze": ["analyze", "schema", "columns", "structure", "what's in"],
            "map": ["map", "mapping", "match", "align columns"],
            "validate": ["validate", "check", "quality", "errors", "issues"],
            "query": ["query", "select", "show", "display", "get data"]
        }
        
        detected_intents = []
        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)
        
        logger.info(f"[{self.agent_id}] Detected intents: {detected_intents}")
        
        # Build action plan based on intents
        
        # SPECIAL CASE: Merge mentioned with FILE NAMES (not table names)
        if "merge" in detected_intents and len(file_names) >= 2:
            logger.info(f"[{self.agent_id}] 🎯 Detected file merge request: {file_names}")
            # User wants to merge files - tell them we need to upload first
            return {
                "needs_agents": False,  # Don't execute yet
                "intents": ["merge", "upload"],
                "actions": [],
                "file_names": file_names,
                "table_names": [],
                "requires_clarification": True,
                "clarification_message": f"I can help you merge {file_names[0]} and {file_names[1]}! However, I need the full file paths. Please provide them in this format:\n\n'merge /path/to/{file_names[0]} with /path/to/{file_names[1]}'\n\nOr if they're in the Bank 1 Data and Bank 2 Data folders, say:\n\n'merge Bank 1 Data/{file_names[0]} with Bank 2 Data/{file_names[1]}'"
            }
        
        # Handle file uploads
        if "upload" in detected_intents and len(file_names) > 0:
            logger.info(f"[{self.agent_id}] 🎯 Upload request detected for {len(file_names)} files")
            needs_agents = True
            for file_name in file_names:
                actions.append({
                    "type": "ingest",
                    "capability": AgentCapability.DATA_INGESTION,
                    "description": f"Upload {file_name} to Snowflake",
                    "parameters": {"file_path": file_name}
                })
        
        # Handle table merges (when actual Snowflake table names are provided)
        if "merge" in detected_intents and len(table_names) >= 2:
            needs_agents = True
            table1 = table_names[0]
            table2 = table_names[1]
            
            # Merge requires: schema → mapping → join → validate
            actions.extend([
                {
                    "type": "analyze_schema",
                    "capability": AgentCapability.SCHEMA_ANALYSIS,
                    "description": "Analyze table schemas",
                    "parameters": {"table_name": table1, "include_sample": False}
                },
                {
                    "type": "propose_mappings",
                    "capability": AgentCapability.CONFLICT_DETECTION,
                    "description": "AI-powered column mapping",
                    "parameters": {"table1": table1, "table2": table2, "confidence_threshold": 70}
                },
                {
                    "type": "execute_merge",
                    "capability": AgentCapability.MERGE_EXECUTION,
                    "description": "Execute SQL merge",
                    "parameters": {"table1": table1, "table2": table2, "mappings": [], "join_type": "full_outer", "output_table": f"MERGED_{table1[:20]}_{table2[:20]}"}
                },
                {
                    "type": "validate",
                    "capability": AgentCapability.DATA_QUALITY,
                    "description": "Validate merged data",
                    "parameters": {"table_name": f"MERGED_{table1[:20]}_{table2[:20]}"}
                }
            ])
        
        if "analyze" in detected_intents and "merge" not in detected_intents and len(table_names) >= 1:
            needs_agents = True
            actions.append({
                "type": "analyze_schema",
                "capability": AgentCapability.SCHEMA_ANALYSIS,
                "description": "Analyze data structure",
                "parameters": {"table_name": table_names[0], "include_sample": True}
            })
        
        if "validate" in detected_intents and len(table_names) >= 1:
            needs_agents = True
            actions.append({
                "type": "validate",
                "capability": AgentCapability.DATA_QUALITY,
                "description": "Run quality checks",
                "parameters": {"table_name": table_names[0]}
            })
        
        return {
            "needs_agents": needs_agents,
            "intents": detected_intents,
            "actions": actions,
            "table_names": table_names,
            "requires_clarification": len(detected_intents) == 0 and len(user_message.split()) > 3
        }
    
    async def _execute_agent_workflow(self, action_plan: Dict) -> Dict[str, Any]:
        """
        Execute the planned agent workflow
        Chain results from one step to the next
        Tracks detailed timing and communication for each step
        """
        import time
        from datetime import datetime
        
        results = {}
        workflow_start = time.time()
        
        for i, action in enumerate(action_plan.get("actions", [])):
            step_start = time.time()
            step_start_time = datetime.now().strftime("%H:%M:%S")
            
            try:
                step_info = f"🔄 Step {i+1}/{len(action_plan['actions'])}: {action['description']}"
                logger.info(f"[{self.agent_id}] {step_info}")
                
                # EMIT PROGRESS: Step started
                if self.progress_callback:
                    await self.progress_callback({
                        "type": "step_start",
                        "step": i+1,
                        "total_steps": len(action_plan['actions']),
                        "description": action['description'],
                        "capability": action['capability'].value,
                        "time": step_start_time
                    })
                
                # Get parameters for this action
                params = action.get("parameters", {}).copy()
                
                # Chain results: Use mappings from mapping step in merge step
                if action["type"] == "execute_merge" and "propose_mappings" in results:
                    mapping_result = results["propose_mappings"]
                    if mapping_result.get("success") and mapping_result.get("result"):
                        mappings = mapping_result["result"].get("mappings", [])
                        params["mappings"] = mappings
                        logger.info(f"[{self.agent_id}] 🔗 Chaining {len(mappings)} mappings from previous step")
                        
                        # EMIT PROGRESS: Chaining data
                        if self.progress_callback:
                            await self.progress_callback({
                                "type": "info",
                                "message": f"🔗 Using {len(mappings)} mappings from previous step"
                            })
                
                # Call appropriate agent via registry
                logger.info(f"[{self.agent_id}] 📞 Calling agent with capability: {action['capability'].value}")
                
                # EMIT PROGRESS: Calling agent
                if self.progress_callback:
                    await self.progress_callback({
                        "type": "agent_call",
                        "capability": action['capability'].value,
                        "parameters": {k: str(v)[:50] for k, v in params.items()}  # Truncate for display
                    })
                
                result = await self.invoke_capability(
                    capability=action["capability"],
                    parameters=params
                )
                
                # Add timing metadata
                step_duration = time.time() - step_start
                result["_timing"] = {
                    "start_time": step_start_time,
                    "duration_seconds": round(step_duration, 2),
                    "duration_human": f"{step_duration:.2f}s"
                }
                
                results[action["type"]] = result
                
                # Check if step failed
                if not result.get("success"):
                    logger.warning(f"[{self.agent_id}] ⚠️  Step failed: {action['type']} in {step_duration:.2f}s")
                    
                    # EMIT PROGRESS: Step failed
                    if self.progress_callback:
                        await self.progress_callback({
                            "type": "step_error",
                            "step": i+1,
                            "error": result.get("error", "Unknown error"),
                            "duration": f"{step_duration:.2f}s"
                        })
                else:
                    logger.info(f"[{self.agent_id}] ✅ Step completed: {action['type']} in {step_duration:.2f}s")
                    
                    # EMIT PROGRESS: Step completed with results
                    if self.progress_callback:
                        progress_data = {
                            "type": "step_complete",
                            "step": i+1,
                            "duration": f"{step_duration:.2f}s",
                            "agent": result.get("agent", "unknown")
                        }
                        
                        # Add type-specific details
                        if action["type"] == "analyze_schema" and "result" in result:
                            schema = result["result"].get("schema", [])
                            progress_data["details"] = f"✅ Found {len(schema)} columns"
                        elif action["type"] == "propose_mappings" and "result" in result:
                            mappings = result["result"].get("mappings", [])
                            confidence = result["result"].get("overall_confidence", 0)
                            progress_data["details"] = f"✅ Found {len(mappings)} mappings ({confidence}% confidence)"
                        elif action["type"] == "execute_merge" and "result" in result:
                            stats = result["result"].get("statistics", {})
                            progress_data["details"] = f"✅ Merged {stats.get('output_rows', 0):,} rows"
                        
                        await self.progress_callback(progress_data)
                
            except Exception as e:
                step_duration = time.time() - step_start
                logger.error(f"[{self.agent_id}] ❌ Action failed: {action['type']} - {e}")
                results[action["type"]] = {
                    "success": False, 
                    "error": str(e),
                    "_timing": {
                        "start_time": step_start_time,
                        "duration_seconds": round(step_duration, 2),
                        "duration_human": f"{step_duration:.2f}s"
                    }
                }
        
        # Add total workflow timing
        total_duration = time.time() - workflow_start
        results["_workflow_timing"] = {
            "total_duration_seconds": round(total_duration, 2),
            "total_duration_human": f"{total_duration:.2f}s",
            "steps_executed": len(action_plan.get("actions", []))
        }
        
        return results
    
    def _generate_quick_response(
        self,
        user_message: str,
        action_plan: Dict,
        results: Dict
    ) -> str:
        """
        Generate intelligent response using Gemini 2.5 Pro for conversational queries
        """
        if not action_plan.get("needs_agents"):
            # Check if clarification is needed
            if action_plan.get("requires_clarification") and action_plan.get("clarification_message"):
                return action_plan["clarification_message"]
            
            # Use Gemini 2.5 Pro for conversational intelligence
            conversational_prompt = self._build_conversational_prompt(user_message, {})
            
            try:
                # Use inherited Gemini model from BaseGeminiAgent
                response = self.model.generate_content(conversational_prompt)
                return response.text.strip()
            except Exception as e:
                logger.error(f"[{self.agent_id}] Gemini error: {e}")
                # Fallback only on error
                return "I'd be happy to help! Could you tell me more about what you'd like to do? For example: 'merge customer data', 'analyze a table', or 'check data quality'."
        
        # Build DETAILED response with results
        response_parts = []
        
        # Add header
        response_parts.append("=" * 80)
        if action_plan.get("intents"):
            intent_str = ", ".join(action_plan["intents"]).upper()
            response_parts.append(f"📋 EXECUTION REPORT: {intent_str}")
        response_parts.append("=" * 80)
        response_parts.append("")
        
        # Detailed action breakdown
        for idx, action in enumerate(action_plan.get("actions", []), 1):
            action_type = action["type"]
            
            response_parts.append(f"🔹 STEP {idx}/{len(action_plan.get('actions', []))}: {action['description']}")
            response_parts.append(f"   ├─ Capability: {action['capability'].value}")
            
            if action_type in results:
                result = results[action_type]
                
                # Show timing first
                if "_timing" in result:
                    timing = result["_timing"]
                    response_parts.append(f"   ├─ Started: {timing['start_time']}")
                    response_parts.append(f"   ├─ Duration: ⏱️  {timing['duration_human']}")
                
                if result.get("success"):
                    response_parts.append(f"   ├─ Status: ✅ SUCCESS")
                    
                    # Show which agent handled it
                    if "agent" in result:
                        response_parts.append(f"   ├─ Agent: 🤖 {result['agent']}")
                    
                    # Show detailed results based on action type
                    if action_type == "analyze_schema" and "result" in result:
                        schema = result["result"].get("schema", [])
                        response_parts.append(f"   ├─ Columns Detected: {len(schema)}")
                        if schema:
                            response_parts.append(f"   │  Sample Columns:")
                            for col in schema[:5]:
                                response_parts.append(f"   │    • {col.get('name')} ({col.get('type')})")
                            if len(schema) > 5:
                                response_parts.append(f"   │    ... and {len(schema) - 5} more")
                    
                    elif action_type == "propose_mappings" and "result" in result:
                        mappings = result["result"].get("mappings", [])
                        confidence = result["result"].get("overall_confidence", 0)
                        response_parts.append(f"   ├─ Mappings Found: {len(mappings)}")
                        response_parts.append(f"   ├─ AI Confidence: {confidence}%")
                        if mappings:
                            response_parts.append(f"   │  Top Mappings:")
                            for m in mappings[:5]:
                                conf_emoji = "🟢" if m['confidence'] >= 90 else ("🟡" if m['confidence'] >= 70 else "🔴")
                                response_parts.append(f"   │    {conf_emoji} {m['dataset_a_col']} ↔ {m['dataset_b_col']} ({m['confidence']}%)")
                            if len(mappings) > 5:
                                response_parts.append(f"   │    ... and {len(mappings) - 5} more mappings")
                    
                    elif action_type == "execute_merge" and "result" in result:
                        merge_result = result["result"]
                        response_parts.append(f"   ├─ Output Table: {merge_result.get('output_table', 'N/A')}")
                        response_parts.append(f"   ├─ Join Type: {merge_result.get('join_type', 'N/A').upper()}")
                        if "statistics" in merge_result:
                            stats = merge_result["statistics"]
                            response_parts.append(f"   │  📊 Statistics:")
                            response_parts.append(f"   │    • Input Rows (Table 1): {stats.get('table1_rows', 0):,}")
                            response_parts.append(f"   │    • Input Rows (Table 2): {stats.get('table2_rows', 0):,}")
                            response_parts.append(f"   │    • Output Rows: {stats.get('output_rows', 0):,}")
                            response_parts.append(f"   │    • Mappings Applied: {stats.get('mappings_applied', 0)}")
                    
                    elif action_type == "validate_quality" and "result" in result:
                        quality = result["result"]
                        response_parts.append(f"   │  ✅ Quality Checks:")
                        for check_name, check_result in quality.items():
                            if isinstance(check_result, dict):
                                status = "✅" if check_result.get("passed") else "❌"
                                response_parts.append(f"   │    {status} {check_name}: {check_result.get('message', 'N/A')}")
                    
                    response_parts.append(f"   └─ ✅ Completed")
                else:
                    response_parts.append(f"   ├─ Status: ❌ FAILED")
                    response_parts.append(f"   └─ Error: {result.get('error', 'Unknown error')}")
            
            response_parts.append("")
        
        # Summary section
        response_parts.append("=" * 80)
        response_parts.append("📊 SUMMARY")
        response_parts.append("=" * 80)
        
        success_count = sum(1 for k, r in results.items() if not k.startswith('_') and r.get("success"))
        total_count = len([k for k in results.keys() if not k.startswith('_')])
        
        response_parts.append(f"✅ Successful Steps: {success_count}/{total_count}")
        response_parts.append(f"❌ Failed Steps: {total_count - success_count}/{total_count}")
        
        # Add total workflow timing
        if "_workflow_timing" in results:
            wf_timing = results["_workflow_timing"]
            response_parts.append(f"⏱️  Total Execution Time: {wf_timing['total_duration_human']}")
            response_parts.append(f"📊 Steps Executed: {wf_timing['steps_executed']}")
        
        # Add final output info
        if "execute_merge" in results and results["execute_merge"].get("success"):
            merge_result = results["execute_merge"]["result"]
            response_parts.append(f"\n📦 Final Output:")
            response_parts.append(f"   • Table: {merge_result.get('output_table', 'N/A')}")
            if "statistics" in merge_result:
                stats = merge_result["statistics"]
                response_parts.append(f"   • Total Rows: {stats.get('output_rows', 0):,}")
        
        # Add next steps
        if success_count == total_count:
            response_parts.append(f"\n💡 Next Steps:")
            response_parts.append(f"   • Query the merged data: SELECT * FROM <table_name> LIMIT 10")
            response_parts.append(f"   • Run quality checks: 'check quality of <table_name>'")
            response_parts.append(f"   • Export results: 'export <table_name>'")
        
        response_parts.append("\n" + "=" * 80)
        
        return "\n".join(response_parts)
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        logger.info(f"[{self.agent_id}] Conversation history reset")
