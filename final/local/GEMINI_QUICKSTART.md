# Gemini Agent System - Quick Start 🚀

## ✅ What You Now Have

A **modular Gemini 2.0 Flash agent system** that understands Snowflake tools and provides intelligent data integration analysis.

### 3 Core Gemini Agents:

1. **GeminiSchemaReaderAgent** - Reads and analyzes schemas
2. **GeminiSQLGeneratorAgent** - Generates SQL queries (merge, transform, quality checks)
3. **GeminiConflictDetectorAgent** - Detects conflicts before merging

---

## 🎯 Key Concept: Propose, Don't Execute

**These agents are ADVISORS:**

- ✅ They **analyze** your data
- ✅ They **propose** SQL queries
- ✅ They **recommend** which Snowflake tools to use
- ❌ They **DO NOT execute** anything without your approval

**You** decide when to run the SQL.

---

## 🧪 Test It Now

```bash
cd test_agents

# Step 1: Ingest data (already passed! ✅)
python3 01_test_snowflake_ingestion.py

# Step 2: Analyze schema with Gemini
python3 02_test_gemini_schema.py
```

---

## 📖 How to Use in Your Code

### Example 1: Analyze a Schema

```python
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent

agent = GeminiSchemaReaderAgent(agent_id="schema_001")

result = await agent.execute({
    "type": "read_schema",
    "table_name": "RAW_test_session_001_DATASET_1",
    "include_sample": True,
    "sample_size": 10
})

# What you get back:
print(result['gemini_analysis'])      # AI's understanding of the schema
print(result['recommended_tools'])    # Tools Gemini suggests using
print(result['schema'])               # Raw schema from Snowflake
print(result['confidence'])           # How confident Gemini is (0.0-1.0)
```

**Output Example:**
```
"This table contains customer transaction data. The 'customer_id' column 
appears to be a unique identifier (VARCHAR), while 'transaction_amount' 
is a monetary value (NUMBER). Potential join key: customer_id. 
Data quality score: 0.85."
```

---

### Example 2: Generate Merge SQL

```python
from agents.gemini.sql_generator_agent import GeminiSQLGeneratorAgent

agent = GeminiSQLGeneratorAgent(agent_id="sql_gen_001")

result = await agent.execute({
    "type": "generate_merge_sql",
    "table1": "RAW_session_001_DATASET_1",
    "table2": "RAW_session_001_DATASET_2",
    "schema1": [...],  # From schema reader
    "schema2": [...],  # From schema reader
    "merge_type": "full_outer",
    "join_columns": [{"left": "customer_id", "right": "client_id"}]
})

# Gemini generates SQL but DOES NOT execute it
print(result['proposed_sql'])  
# "SELECT t1.customer_id, t1.name, t2.email FROM table1 t1 FULL OUTER JOIN..."

print(result['warning'])
# "⚠️ SQL NOT EXECUTED - User must approve and provide final schema"
```

**User Approval Flow:**
```python
# Show user the SQL
print("Proposed SQL:")
print(result['proposed_sql'])

# Get approval
if user_approves():
    # THEN execute
    from sf_infrastructure.connector import snowflake_connector
    await snowflake_connector.execute_non_query(result['proposed_sql'])
    print("✅ Merge complete!")
```

---

### Example 3: Detect Conflicts

```python
from agents.gemini.conflict_detector_agent import GeminiConflictDetectorAgent

agent = GeminiConflictDetectorAgent(agent_id="conflict_001")

result = await agent.execute({
    "type": "detect_conflicts",
    "table1": "RAW_session_001_DATASET_1",
    "table2": "RAW_session_001_DATASET_2",
    "schema1": [...],
    "schema2": [...],
    "proposed_mappings": [{"left": "customer_id", "right": "client_id"}]
})

# What you get:
for conflict in result['conflicts']:
    print(f"[{conflict['severity']}] {conflict['description']}")

# Example output:
# [HIGH] Type mismatch: customer_id is VARCHAR in table1 but NUMBER in table2
# [MEDIUM] Potential duplicates detected in join key
# [LOW] Column 'email' has 15% nulls in table2

if result['requires_human_review']:
    print("⚠️ CRITICAL conflicts detected! Manual review required.")
    # Send to Jira Agent (you'll build this next)
```

---

## 🔧 Available Tools Gemini Understands

These are defined in `base_gemini_agent.py` and Gemini knows about them:

```python
available_tools = [
    "read_table_schema",      # Read Snowflake schema
    "execute_sql_query",      # Run SQL queries
    "get_column_statistics",  # Get null counts, distinct values, etc.
    "detect_conflicts",       # Find data conflicts
]
```

When you ask Gemini to analyze something, it will **recommend which tools to use** based on the context.

---

## 🏗️ How It's Modular

### Anyone Can Use These Agents

```python
# In your backend API:
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent

@app.post("/analyze-schema")
async def analyze_schema(table_name: str):
    agent = GeminiSchemaReaderAgent(agent_id=f"api_schema_{uuid4()}")
    result = await agent.execute({
        "type": "read_schema",
        "table_name": table_name,
        "include_sample": True
    })
    return result

# In your CLI tool:
from agents.gemini.sql_generator_agent import GeminiSQLGeneratorAgent

def generate_merge_sql_cli(args):
    agent = GeminiSQLGeneratorAgent(agent_id="cli_sql_gen")
    result = asyncio.run(agent.execute({
        "type": "generate_merge_sql",
        "table1": args.table1,
        "table2": args.table2,
        "merge_type": args.merge_type
    }))
    print(result['proposed_sql'])

# In your Jupyter notebook:
from agents.gemini.conflict_detector_agent import GeminiConflictDetectorAgent

agent = GeminiConflictDetectorAgent(agent_id="notebook_conflicts")
conflicts = await agent.execute({...})
display(conflicts)
```

---

## ⚙️ Configuration

### Set Your Gemini API Key

```bash
# In .env file
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp  # or gemini-2.5-pro when available
```

### Adjust Agent Behavior

```python
agent = GeminiSchemaReaderAgent(
    agent_id="custom_001",
    config={
        "temperature": 0.1,        # Lower = more deterministic
        "max_output_tokens": 4096, # Longer responses
        "custom_param": "value"
    }
)
```

---

## 📚 Full Pipeline Example

```python
# 1. Ingest two CSVs
from agents.snowflake.ingestion_agent import SnowflakeIngestionAgent

ingest = SnowflakeIngestionAgent(agent_id="ingest_001")
table1_result = await ingest.execute({
    "type": "ingest_file",
    "file_path": "customers.csv",
    "session_id": "demo_session",
    "dataset_num": 1
})
table1 = table1_result['table_name']

# 2. Analyze schema
from agents.gemini.schema_reader_agent import GeminiSchemaReaderAgent

schema_agent = GeminiSchemaReaderAgent(agent_id="schema_001")
schema1 = await schema_agent.execute({
    "type": "read_schema",
    "table_name": table1,
    "include_sample": True
})

print("Gemini says:", schema1['gemini_analysis'])

# 3. Detect conflicts
from agents.gemini.conflict_detector_agent import GeminiConflictDetectorAgent

conflict_agent = GeminiConflictDetectorAgent(agent_id="conflict_001")
conflicts = await conflict_agent.execute({
    "type": "detect_conflicts",
    "table1": table1,
    "table2": table2,
    "schema1": schema1['schema'],
    "schema2": schema2['schema'],
    "proposed_mappings": [{"left": "id", "right": "customer_id"}]
})

if conflicts['requires_human_review']:
    print("⚠️ Review needed!")
    # Create Jira ticket here
    
# 4. Generate merge SQL
from agents.gemini.sql_generator_agent import GeminiSQLGeneratorAgent

sql_agent = GeminiSQLGeneratorAgent(agent_id="sql_001")
merge_sql = await sql_agent.execute({
    "type": "generate_merge_sql",
    "table1": table1,
    "table2": table2,
    "schema1": schema1['schema'],
    "schema2": schema2['schema'],
    "merge_type": "full_outer",
    "join_columns": [{"left": "id", "right": "customer_id"}]
})

# 5. User approves and executes
print("Proposed SQL:")
print(merge_sql['proposed_sql'])

if user_approves():
    from sf_infrastructure.connector import snowflake_connector
    await snowflake_connector.execute_non_query(merge_sql['proposed_sql'])
    print("✅ Merge complete!")
```

---

## 🚀 Next Steps

1. **Test the Gemini agents**: Run `python3 02_test_gemini_schema.py`
2. **Integrate into your API**: Use them in FastAPI routes
3. **Build Jira Agent**: For creating tickets on conflicts
4. **Build Master Agent**: Orchestrates all agents together

See `agents/gemini/README.md` for full documentation.

---

**You're ready to go! 🎉**
