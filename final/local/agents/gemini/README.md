# Gemini Agent Suite 🤖

> **Modular AI agents powered by Gemini 2.0 Flash for intelligent data integration**

## Philosophy

**These agents are SMART ADVISORS, not executors.**

- ✅ They **analyze** and **propose** solutions
- ✅ They **recommend tools** to use from Snowflake
- ✅ They **generate SQL** for review
- ❌ They **DO NOT execute** SQL directly
- ❌ They **DO NOT modify** data without user approval

**User is ALWAYS in control.**

---

## Available Agents

### 1. **GeminiSchemaReaderAgent** 📊

**Purpose**: Read and understand database schemas with AI-powered semantic analysis

**What it does**:
- Reads table schema from Snowflake
- Uses Gemini to understand column semantics (e.g., "customer_id" = unique identifier)
- Identifies data types and suggests improvements
- Detects potential join keys
- Rates data quality
- Proposes transformations

**Usage**:
```python
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent

agent = GeminiSchemaReaderAgent(agent_id="schema_reader_001")

result = await agent.execute({
    "type": "read_schema",
    "table_name": "RAW_session_001_DATASET_1",
    "include_sample": True,
    "sample_size": 10
})

print(result['gemini_analysis'])  # AI analysis
print(result['recommended_tools'])  # Tools Gemini suggests using
print(result['confidence'])  # Confidence score
```

**Output**:
```json
{
  "agent_id": "schema_reader_001",
  "table_name": "RAW_session_001_DATASET_1",
  "schema": [...],
  "gemini_analysis": "This table contains customer data with...",
  "recommended_tools": [
    {"tool": "get_column_statistics", "reason": "To analyze null rates"}
  ],
  "confidence": 0.92
}
```

---

### 2. **GeminiSQLGeneratorAgent** 🔧

**Purpose**: Generate optimized SQL queries for data operations

**What it does**:
- Generates merge/join SQL
- Creates transformation queries
- Produces data quality check queries
- **Returns SQL as text, NOT executed**

**Usage**:
```python
from agents.gemini.sql_generator_agent import GeminiSQLGeneratorAgent

agent = GeminiSQLGeneratorAgent(agent_id="sql_gen_001")

result = await agent.execute({
    "type": "generate_merge_sql",
    "table1": "RAW_session_001_DATASET_1",
    "table2": "RAW_session_001_DATASET_2",
    "schema1": [...],
    "schema2": [...],
    "merge_type": "full_outer",
    "join_columns": [{"left": "customer_id", "right": "client_id"}]
})

# SQL is PROPOSED, not executed
print(result['proposed_sql'])
print(result['warning'])  # "⚠️ SQL NOT EXECUTED - User must approve"
```

**Output**:
```json
{
  "agent_id": "sql_gen_001",
  "task": "merge_sql_generation",
  "proposed_sql": "SELECT t1.*, t2.* FROM table1 t1 FULL OUTER JOIN...",
  "explanation": "This query performs a full outer join...",
  "confidence": 0.88,
  "warning": "⚠️ SQL NOT EXECUTED - User must approve",
  "next_steps": [
    "Review the proposed SQL",
    "Verify join keys are correct",
    "Approve for execution"
  ]
}
```

---

### 3. **GeminiConflictDetectorAgent** ⚠️

**Purpose**: Detect data conflicts before merging datasets

**What it does**:
- Schema conflicts (type mismatches)
- Data conflicts (duplicate keys, inconsistent values)
- Semantic conflicts (same column name, different meaning)
- Rates severity: CRITICAL, HIGH, MEDIUM, LOW
- Proposes resolution strategies

**Usage**:
```python
from agents.gemini.conflict_detector_agent import GeminiConflictDetectorAgent

agent = GeminiConflictDetectorAgent(agent_id="conflict_detector_001")

result = await agent.execute({
    "type": "detect_conflicts",
    "table1": "RAW_session_001_DATASET_1",
    "table2": "RAW_session_001_DATASET_2",
    "schema1": [...],
    "schema2": [...],
    "proposed_mappings": [{"left": "customer_id", "right": "client_id"}]
})

print(result['conflicts'])  # List of conflicts
print(result['severity_summary'])  # {"CRITICAL": 2, "HIGH": 5, ...}
print(result['requires_human_review'])  # True if critical issues found
```

**Output**:
```json
{
  "agent_id": "conflict_detector_001",
  "conflicts": [
    {
      "type": "TYPE_MISMATCH",
      "severity": "HIGH",
      "left_column": "customer_id",
      "right_column": "client_id",
      "left_type": "VARCHAR",
      "right_type": "NUMBER",
      "description": "Type mismatch: VARCHAR vs NUMBER"
    }
  ],
  "severity_summary": {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 3, "LOW": 2},
  "requires_human_review": true,
  "recommended_actions": [
    "Cast client_id to VARCHAR before joining",
    "Verify client_id format is consistent"
  ]
}
```

---

## Architecture

### Tool-Calling Pattern

All Gemini agents understand **available Snowflake tools**:

```python
# Defined in BaseGeminiAgent
available_tools = [
    {
        "name": "read_table_schema",
        "description": "Read schema from Snowflake table",
        "parameters": {...}
    },
    {
        "name": "execute_sql_query",
        "description": "Execute SQL and return results",
        "parameters": {...}
    },
    {
        "name": "get_column_statistics",
        "description": "Get column stats (nulls, distinct, min/max)",
        "parameters": {...}
    },
    {
        "name": "detect_conflicts",
        "description": "Detect conflicts between tables",
        "parameters": {...}
    }
]
```

Gemini analyzes your request and **recommends which tools to use**, but **you** decide when to execute them.

---

## Workflow Example

### Full Data Integration Pipeline

```python
# Step 1: Ingest data
from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent

ingestion = SnowflakeIngestionAgent(agent_id="ingest_001")
result1 = await ingestion.execute({
    "type": "ingest_file",
    "file_path": "dataset1.csv",
    "session_id": "demo_session",
    "dataset_num": 1
})
table1 = result1['table_name']  # "RAW_demo_session_DATASET_1"

# Step 2: Analyze schema with Gemini
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent

schema_reader = GeminiSchemaReaderAgent(agent_id="schema_001")
schema_analysis = await schema_reader.execute({
    "type": "read_schema",
    "table_name": table1,
    "include_sample": True
})

print("Gemini's take:", schema_analysis['gemini_analysis'])

# Step 3: Detect conflicts (if merging two datasets)
from agents.gemini.conflict_detector_agent import GeminiConflictDetectorAgent

conflict_detector = GeminiConflictDetectorAgent(agent_id="conflict_001")
conflicts = await conflict_detector.execute({
    "type": "detect_conflicts",
    "table1": table1,
    "table2": table2,
    "schema1": schema_analysis['schema'],
    "schema2": schema_analysis2['schema'],
    "proposed_mappings": [{"left": "customer_id", "right": "client_id"}]
})

if conflicts['requires_human_review']:
    print("⚠️ CRITICAL conflicts detected! Review required.")
    for conflict in conflicts['conflicts']:
        print(f"  - {conflict['severity']}: {conflict['description']}")

# Step 4: Generate merge SQL
from agents.gemini.sql_generator_agent import GeminiSQLGeneratorAgent

sql_generator = GeminiSQLGeneratorAgent(agent_id="sql_gen_001")
merge_sql = await sql_generator.execute({
    "type": "generate_merge_sql",
    "table1": table1,
    "table2": table2,
    "schema1": schema_analysis['schema'],
    "schema2": schema_analysis2['schema'],
    "merge_type": "full_outer",
    "join_columns": [{"left": "customer_id", "right": "client_id"}]
})

print("Proposed SQL:")
print(merge_sql['proposed_sql'])

# Step 5: USER APPROVAL - then execute
user_approved = input("Approve this SQL? (yes/no): ")
if user_approved.lower() == "yes":
    from sf_infrastructure.connector import snowflake_connector
    await snowflake_connector.execute_non_query(merge_sql['proposed_sql'])
    print("✅ Merge complete!")
else:
    print("❌ Merge cancelled by user")
```

---

## Extending the System

### Creating a New Gemini Agent

1. **Inherit from BaseGeminiAgent**:
```python
from agents.gemini.base_gemini_agent import BaseGeminiAgent

class MyCustomAgent(BaseGeminiAgent):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Your custom logic
        prompt = "Analyze this..."
        result = await self.analyze_with_tools(prompt, context)
        return result
```

2. **Define Available Tools** (optional):
```python
def _define_available_tools(self):
    return super()._define_available_tools() + [
        {
            "name": "my_custom_tool",
            "description": "Does something special",
            "parameters": {...}
        }
    ]
```

3. **Use it**:
```python
agent = MyCustomAgent(agent_id="custom_001")
result = await agent.execute({"type": "custom_task", ...})
```

---

## Configuration

### Environment Variables

```bash
# .env file
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp  # or gemini-2.5-pro
```

### Agent Configuration

```python
agent = GeminiSchemaReaderAgent(
    agent_id="unique_agent_id",
    config={
        "temperature": 0.3,  # Lower = more deterministic
        "max_output_tokens": 8192,
        "custom_setting": "value"
    }
)
```

---

## Best Practices

1. **Always review Gemini's proposals** - Don't blindly execute SQL
2. **Check confidence scores** - Low confidence (<0.7) = needs human review
3. **Use conflict detection** before merging - Saves hours of debugging
4. **Provide context** - More context = better analysis
5. **Log everything** - Gemini's reasoning is valuable for debugging

---

## Testing

Run individual agent tests:

```bash
# Test Schema Reader
cd test_agents
python3 02_test_gemini_schema.py

# Test SQL Generator
python3 03_test_gemini_sql_generator.py

# Test Conflict Detector
python3 04_test_gemini_conflicts.py
```

---

## Troubleshooting

### "Gemini API key not found"
- Check `.env` file has `GEMINI_API_KEY=...`
- Ensure `python-dotenv` is loading the file

### "Model not found: gemini-2.5-pro"
- Use `gemini-2.0-flash-exp` instead (available now)
- Or check your Gemini API access level

### "Confidence score too low"
- Provide more context in the task
- Include sample data
- Check if table schema is complete

---

## License

Built for EY Data Integration Hackathon 🚀
