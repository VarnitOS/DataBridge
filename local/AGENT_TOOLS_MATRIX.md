# 🤖 Agent Tools Matrix - Complete A2A Communication Map

## 📋 Overview

This document shows **which agents can call which other agents** via the A2A (Agent-to-Agent) system.

Every agent registers with the **Agent Registry** and exposes tools that other agents can discover and invoke.

---

## 🗺️ Agent Communication Map

```
                    ┌─────────────────────┐
                    │  AGENT REGISTRY     │
                    │  (Central Hub)      │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌──────────────┐      ┌──────────────┐
│ MASTER        │      │ GEMINI       │      │ SNOWFLAKE    │
│ ORCHESTRATOR  │      │ AGENTS       │      │ AGENTS       │
└───────┬───────┘      └──────┬───────┘      └──────┬───────┘
        │                     │                      │
        │ Can call:           │ Can call:            │ Can call:
        │ • All agents        │ • Schema Reader      │ • Query Executor
        │                     │ • Ingestion          │ • Stage Manager
        │                     │ • Conflict Detector  │
        └─────────────────────┴──────────────────────┘
                         All via Registry
```

---

## 📊 Complete Agent List

### **1. Master Orchestrator** 🎯
- **Type:** `master_orchestrator`
- **Capabilities:** ALL (orchestrator role)
- **Tools Exposed:** `orchestrate_full_pipeline`

**Can Call (A2A):**
- ✅ Snowflake Ingestion Agent
- ✅ Gemini Schema Reader Agent  
- ✅ Gemini Mapping Agent
- ✅ Gemini Conflict Detector Agent
- ✅ Gemini SQL Generator Agent
- ✅ Any other registered agent

**Called By:**
- FastAPI routes
- Frontend (indirectly via API)

**Example Usage:**
```python
# Master Agent discovers and calls Ingestion Agent
result = await master.invoke_capability(
    capability=AgentCapability.DATA_INGESTION,
    parameters={"file_path": "data.csv", ...}
)
```

---

### **2. Snowflake Ingestion Agent** 📥
- **Type:** `snowflake_ingestion`
- **Capabilities:** `DATA_INGESTION`
- **Tools Exposed:** `ingest_csv_to_snowflake`

**Can Call (A2A):**
- ✅ Snowflake Query Executor (if needed)
- ✅ Snowflake Stage Manager (if needed)

**Called By:**
- Master Orchestrator
- Any agent needing data ingestion

**What It Does:**
1. Uploads CSV to Snowflake stage
2. Creates table with auto-detected schema
3. Loads data using COPY INTO
4. Returns table name and stats

---

### **3. Gemini Schema Reader Agent** 📊
- **Type:** `gemini_schema_reader`
- **Capabilities:** `SCHEMA_ANALYSIS`
- **Tools Exposed:** `read_and_analyze_schema`

**Can Call (A2A):**
- ✅ Snowflake Ingestion Agent (if table doesn't exist)
- ✅ Any Snowflake agent for queries

**Called By:**
- Master Orchestrator
- Gemini Mapping Agent (to fetch schemas)
- Any agent needing schema analysis

**What It Does:**
1. Reads table schema from Snowflake
2. Gets sample data
3. Sends to Gemini for semantic analysis
4. Returns structured schema with insights

---

### **4. Gemini Mapping Agent** 🔗 **NEW!**
- **Type:** `gemini_mapping`
- **Capabilities:** `SCHEMA_ANALYSIS`
- **Tools Exposed:** `propose_column_mappings`

**Can Call (A2A):**
- ✅ Gemini Schema Reader Agent (to fetch schemas if not provided)
- ✅ Gemini Conflict Detector Agent (for validation)

**Called By:**
- Master Orchestrator
- Frontend (via API)

**What It Does:**
1. **Calls Schema Reader Agent** to get both table schemas (A2A!)
2. Uses Gemini to propose intelligent mappings
3. Returns confidence scores + reasoning
4. Identifies conflicts for Jira escalation

**Example A2A Flow:**
```python
# Mapping Agent internally calls Schema Reader Agent
schema1_result = await mapping_agent.invoke_capability(
    capability=AgentCapability.SCHEMA_ANALYSIS,
    parameters={"table_name": "TABLE_1", ...}
)
# Gets schema automatically via A2A!
```

---

### **5. Gemini Conflict Detector Agent** ⚠️
- **Type:** `gemini_conflict_detector`
- **Capabilities:** `CONFLICT_DETECTION`
- **Tools Exposed:** `detect_data_conflicts`

**Can Call (A2A):**
- ✅ Gemini Schema Reader Agent (to analyze schemas)
- ✅ Jira Agent (to create tickets)

**Called By:**
- Master Orchestrator
- Gemini Mapping Agent (for validation)

**What It Does:**
1. Detects type mismatches, duplicates, semantic conflicts
2. Rates severity (CRITICAL, HIGH, MEDIUM, LOW)
3. **Calls Jira Agent** if critical issues found
4. Returns conflict report

---

### **6. Gemini SQL Generator Agent** 🔧
- **Type:** `gemini_sql_generator`
- **Capabilities:** `SQL_GENERATION`
- **Tools Exposed:** `generate_merge_sql`

**Can Call (A2A):**
- ✅ Gemini Schema Reader Agent (for schema context)
- ✅ Gemini Mapping Agent (for mapping context)

**Called By:**
- Master Orchestrator
- Any agent needing SQL generation

**What It Does:**
1. Takes approved mappings
2. Uses Gemini to generate optimized Snowflake SQL
3. **Proposes SQL but DOES NOT execute**
4. Returns SQL as text for user approval

---

## 🔄 Complete A2A Communication Flows

### **Flow 1: Full Pipeline (Master Orchestrator)**

```
Master Agent
  │
  ├─► Ingestion Agent (dataset 1)
  │     └─► Returns: table_name_1
  │
  ├─► Ingestion Agent (dataset 2)
  │     └─► Returns: table_name_2
  │
  ├─► Schema Reader Agent (table 1)
  │     └─► Returns: schema_1 + analysis
  │
  ├─► Schema Reader Agent (table 2)
  │     └─► Returns: schema_2 + analysis
  │
  ├─► Mapping Agent
  │     ├─► (internally calls Schema Reader if needed)
  │     └─► Returns: mappings + conflicts
  │
  ├─► Conflict Detector Agent
  │     ├─► (calls Jira Agent if critical)
  │     └─► Returns: conflict_report
  │
  └─► SQL Generator Agent
        └─► Returns: proposed_sql
```

### **Flow 2: Mapping Agent (Autonomous Schema Fetching)**

```
Mapping Agent
  │
  ├─► Schema Reader Agent (table 1) ← A2A call
  │     └─► Returns: schema_1
  │
  ├─► Schema Reader Agent (table 2) ← A2A call
  │     └─► Returns: schema_2
  │
  └─► Gemini API (propose mappings)
        └─► Returns: mappings with confidence scores
```

### **Flow 3: Conflict Escalation**

```
Conflict Detector Agent
  │
  ├─► Detects critical conflict
  │
  ├─► Jira Agent ← A2A call
  │     └─► Creates ticket: "EY-1234"
  │
  └─► Returns: conflict_report + jira_ticket_id
```

---

## 📋 Tools Registry Reference

### **By Capability**

| Capability | Tools Available | Agent(s) |
|-----------|-----------------|----------|
| `DATA_INGESTION` | `ingest_csv_to_snowflake`, `orchestrate_full_pipeline` | Snowflake Ingestion, Master Orchestrator |
| `SCHEMA_ANALYSIS` | `read_and_analyze_schema`, `propose_column_mappings` | Gemini Schema Reader, Gemini Mapping |
| `CONFLICT_DETECTION` | `detect_data_conflicts` | Gemini Conflict Detector |
| `SQL_GENERATION` | `generate_merge_sql` | Gemini SQL Generator |

### **Tool Discovery Example**

```python
from core.agent_registry import agent_registry, AgentCapability

# Discover all agents that can do schema analysis
tools = agent_registry.discover_tools(
    capability=AgentCapability.SCHEMA_ANALYSIS
)

# Returns:
# [
#   AgentTool(name="read_and_analyze_schema", agent_id="schema_001"),
#   AgentTool(name="propose_column_mappings", agent_id="mapping_001")
# ]
```

---

## 🎯 Agent Autonomy Rules

### **Who Can Call Who**

| Caller Agent | Can Call | Why |
|-------------|----------|-----|
| **Master Orchestrator** | ALL agents | Orchestrator role, needs full control |
| **Gemini Mapping** | Schema Reader | Needs schemas to propose mappings |
| **Gemini Conflict Detector** | Schema Reader, Jira Agent | Needs schemas + ticket creation |
| **Gemini SQL Generator** | Schema Reader, Mapping Agent | Needs context for SQL generation |
| **Schema Reader** | Snowflake agents | Needs to query data |
| **Snowflake Ingestion** | Stage Manager, Query Executor | Needs Snowflake infrastructure |

### **Circular Dependency Prevention**

❌ **Not Allowed:**
- Schema Reader calling Mapping Agent (would create loop)
- Mapping Agent calling Conflict Detector that calls Mapping Agent
- Any agent calling itself

✅ **Allowed:**
- Master → Any agent (top-level orchestration)
- Gemini agents → Schema Reader (read-only operation)
- Any agent → Jira Agent (external integration)

---

## 🚀 Adding a New Agent

### **Template for New Agent**

```python
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool

class MyNewAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            agent_type="my_new_agent",
            capabilities=[AgentCapability.MY_CAPABILITY],
            auto_register=True  # ← Automatically registers!
        )
    
    def _define_tools(self):
        """Define what this agent can do for others"""
        self._tools = [
            AgentTool(
                name="my_tool",
                description="Does something useful",
                capability=AgentCapability.MY_CAPABILITY,
                parameters={...},
                handler=self._handle_my_tool,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_my_tool(self, params):
        """This gets called via A2A when other agents invoke the tool"""
        return {"result": "success"}
    
    async def my_method(self):
        """Can call other agents"""
        result = await self.invoke_capability(
            capability=AgentCapability.SCHEMA_ANALYSIS,
            parameters={...}
        )
```

### **Update This Matrix**

After adding a new agent:
1. Add it to the "Complete Agent List" section
2. Document which agents it can call
3. Document which agents call it
4. Update the communication flows

---

## 📊 Current System Stats

- **Total Agents Registered:** 6
- **Total Tools Available:** 6
- **Total Capabilities:** 4
- **A2A Calls Possible:** 15+ combinations

---

## 🎉 Summary

**Key Points:**
- ✅ All agents auto-register with the registry
- ✅ Agents discover each other by capability (not by name)
- ✅ No hardcoded dependencies between agents
- ✅ Master Orchestrator can call any agent
- ✅ Gemini agents collaborate (Mapping calls Schema Reader)
- ✅ System is fully modular - add agents without changing existing code

**This is how a production multi-agent system should work! 🚀**
