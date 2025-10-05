# Agent-to-Agent (A2A) Communication System 🤝

## 🎯 The Problem You Asked to Solve

**Before (Manual Orchestration):**
```python
# User has to manually call each agent
ingest_agent = SnowflakeIngestionAgent(...)
result1 = await ingest_agent.execute({...})

schema_agent = GeminiSchemaReaderAgent(...)
result2 = await schema_agent.execute({...})

conflict_agent = GeminiConflictDetectorAgent(...)
result3 = await conflict_agent.execute({...})

# etc... user orchestrates everything
```

**After (Automatic A2A Communication):**
```python
# Master Agent automatically discovers and calls all agents
master = MasterOrchestratorAgent()
result = await master.execute({
    "type": "full_pipeline",
    "file1_path": "dataset1.csv",
    "file2_path": "dataset2.csv",
    "session_id": "demo_001"
})

# Master Agent:
# 1. Discovers Ingestion Agent → calls it
# 2. Discovers Schema Agent → calls it  
# 3. Discovers Conflict Detector → calls it
# 4. Discovers SQL Generator → calls it
# 5. All automatic via Agent Registry!
```

---

## 🏗️ How It Works (MCP-Style)

### 1. Agent Registry = Tool Server

```python
from core.agent_registry import agent_registry

# Like MCP's tool server - agents register their capabilities
agent_registry.register_agent(
    agent_id="snowflake_ingest_001",
    agent_type="snowflake_ingestion",
    capabilities=[AgentCapability.DATA_INGESTION],
    tools=[
        AgentTool(
            name="ingest_csv_to_snowflake",
            description="Upload CSV file to Snowflake table",
            capability=AgentCapability.DATA_INGESTION,
            parameters={...},
            handler=self._handle_ingest  # ← This function gets called
        )
    ]
)
```

### 2. Agents Discover Each Other

```python
# Gemini agent needs to read a schema
schema_agent = GeminiSchemaReaderAgent()

# Discover who can provide data ingestion
available_agents = schema_agent.discover_agents(
    capability=AgentCapability.DATA_INGESTION
)
# Returns: [{"agent_id": "snowflake_ingest_001", ...}]

# Or discover specific tools
tools = schema_agent.discover_tools(
    capability=AgentCapability.DATA_INGESTION
)
# Returns: [AgentTool(name="ingest_csv_to_snowflake", ...)]
```

### 3. Agents Invoke Each Other (A2A)

```python
# Gemini agent calls Snowflake agent directly
result = await schema_agent.invoke_capability(
    capability=AgentCapability.DATA_INGESTION,
    parameters={
        "type": "ingest_file",
        "file_path": "data.csv",
        "session_id": "demo"
    }
)

# Under the hood:
# 1. Registry finds agent with DATA_INGESTION capability
# 2. Routes the call to that agent's handler
# 3. Agent executes and returns result
# 4. Result flows back to Gemini agent
```

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Agent Registry                        │
│                  (MCP Tool Server)                      │
│                                                          │
│  • Agent Discovery                                       │
│  • Tool Registration                                     │
│  • A2A Routing                                          │
└──────────────┬──────────────────────────────────────────┘
               │
               │ All agents register here
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌──────────┐      ┌──────────┐
│  Gemini  │      │Snowflake │
│  Agent   │      │  Agent   │
│          │      │          │
│  Tools:  │      │  Tools:  │
│  • read  │◄────►│  •ingest │
│  • sql   │ A2A  │  •query  │
│  • detect│      │  •schema │
└──────────┘      └──────────┘
      ▲                 ▲
      │                 │
      │  Master Agent   │
      │  orchestrates   │
      └─────────────────┘
```

---

## 🚀 Real Example: Full Pipeline with A2A

```python
from agents.master_orchestrator import MasterOrchestratorAgent
from core.agent_registry import agent_registry

# Initialize all agents (they auto-register)
from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent
from agents.gemini.conflict_detector_agent import GeminiConflictDetectorAgent
from agents.gemini.sql_generator_agent import GeminiSQLGeneratorAgent

# Agents register themselves automatically
ingest_agent = SnowflakeIngestionAgent(agent_id="ingest_001")
schema_agent = GeminiSchemaReaderAgent(agent_id="schema_001")
conflict_agent = GeminiConflictDetectorAgent(agent_id="conflict_001")
sql_agent = GeminiSQLGeneratorAgent(agent_id="sql_001")

# Check registry
status = agent_registry.get_registry_status()
print(f"Registered agents: {status['total_agents']}")
print(f"Available tools: {status['total_tools']}")

# Now Master Agent can orchestrate everything
master = MasterOrchestratorAgent()

result = await master.execute({
    "type": "full_pipeline",
    "file1_path": "customers.csv",
    "file2_path": "clients.csv",
    "session_id": "demo_session"
})

# What happens (automatic A2A):
# 1. Master → Ingestion Agent (ingest customers.csv)
# 2. Master → Ingestion Agent (ingest clients.csv)
# 3. Master → Schema Agent (analyze table 1)
# 4. Master → Schema Agent (analyze table 2)
# 5. Master → Conflict Detector (find conflicts)
# 6. Master → SQL Generator (create merge SQL)
# 7. Master returns complete result

print(result['pipeline_state'])
# {
#   "steps_completed": ["ingest_dataset_1", "ingest_dataset_2", 
#                       "analyze_schema_1", "analyze_schema_2",
#                       "detect_conflicts", "generate_sql"],
#   "conflicts": [...],
#   "proposed_sql": "SELECT...",
#   "status": "completed"
# }
```

---

## 🔧 How to Add Your Own Agent

### Step 1: Inherit from BaseAgent

```python
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool

class MyCustomAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            agent_type="my_custom_agent",
            capabilities=[AgentCapability.DATA_QUALITY],  # What you provide
            auto_register=True  # Auto-register with registry
        )
    
    def _define_tools(self):
        """Expose your capabilities as tools"""
        self._tools = [
            AgentTool(
                name="check_data_quality",
                description="Run quality checks on dataset",
                capability=AgentCapability.DATA_QUALITY,
                parameters={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string"}
                    },
                    "required": ["table_name"]
                },
                handler=self._handle_quality_check,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_quality_check(self, params: Dict[str, Any]):
        """Your tool handler"""
        table_name = params['table_name']
        # Your logic here
        return {"quality_score": 0.95}
    
    async def execute(self, task: Dict[str, Any]):
        # Your execution logic
        pass
```

### Step 2: Use It

```python
# Your agent auto-registers
my_agent = MyCustomAgent(agent_id="custom_001")

# Other agents can now discover and call it
result = await other_agent.invoke_capability(
    capability=AgentCapability.DATA_QUALITY,
    parameters={"table_name": "MY_TABLE"}
)
```

---

## 🎯 Benefits of A2A System

### 1. **Automatic Discovery**
- Agents find each other at runtime
- No hardcoded dependencies
- Easy to add new agents

### 2. **Loose Coupling**
- Agents don't need to know about each other
- Communication via registry (like MCP server)
- Change implementations without breaking others

### 3. **Dynamic Orchestration**
- Master Agent routes to available agents
- Fallback if agent unavailable
- Load balancing possible

### 4. **Gemini Can See All Tools**
```python
# Gemini gets full tool list automatically
tools = agent_registry.get_all_tools_for_gemini()

# Gemini can now recommend which agent to use:
# "To ingest data, call tool: ingest_csv_to_snowflake"
# "To analyze schema, call tool: read_table_schema"
```

---

## 📚 API Reference

### Agent Registry

```python
from core.agent_registry import agent_registry, AgentCapability

# Register an agent
agent_registry.register_agent(
    agent_id="my_agent",
    agent_type="custom",
    capabilities=[AgentCapability.DATA_QUALITY],
    tools=[...]
)

# Discover agents
agents = agent_registry.discover_agents(
    capability=AgentCapability.DATA_INGESTION
)

# Invoke tool (A2A call)
result = await agent_registry.invoke_tool(
    tool_name="ingest_csv_to_snowflake",
    parameters={...},
    requester_agent_id="my_agent"
)

# Invoke by capability
result = await agent_registry.invoke_capability(
    capability=AgentCapability.SCHEMA_ANALYSIS,
    parameters={...}
)
```

### Base Agent

```python
from core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    # Call other agents
    async def my_method(self):
        result = await self.invoke_agent(
            tool_name="some_tool",
            parameters={...}
        )
        
        # Or by capability
        result = await self.invoke_capability(
            capability=AgentCapability.SQL_GENERATION,
            parameters={...}
        )
```

---

## 🎬 Complete Example: Master Agent Orchestration

See `agents/master_orchestrator.py` for full implementation.

**Key points:**
1. Master Agent discovers all available agents
2. Routes tasks to appropriate agents
3. Chains results (output of one → input of next)
4. Handles errors and retries
5. All communication via registry (A2A)

**Run it:**
```python
from agents.master_orchestrator import MasterOrchestratorAgent

master = MasterOrchestratorAgent()
result = await master.orchestrate_full_pipeline(
    file1_path="data1.csv",
    file2_path="data2.csv",
    session_id="demo",
    merge_type="full_outer",
    auto_approve=False  # Require user approval for merge
)
```

---

## 🚀 Next Steps

1. **Test the A2A system** - See agents discover each other
2. **Add more agents** - They'll auto-integrate
3. **Build Jira Agent** - For ticket creation
4. **Add monitoring** - See A2A calls in real-time

**Your agent system now works like MCP! 🎉**
