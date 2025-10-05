# 🧪 Agent Test Suite

**Build and test each agent individually before integration**

## Philosophy

Instead of building everything at once and hoping it works, we:
1. Build one agent at a time
2. Test it in isolation
3. See exactly what it outputs
4. Fix issues immediately
5. Move to next agent
6. Finally integrate them all

## Test Structure

```
test_agents/
├── test_harness.py              # Reusable test framework
├── 01_test_snowflake_ingestion.py   # TEST 1: Upload CSV to Snowflake
├── 02_test_gemini_schema.py         # TEST 2: AI schema analysis
├── 03_test_gemini_mapping.py        # TEST 3: Column mapping proposals
├── 04_test_master_agent.py          # TEST 4: Autonomous orchestration
├── RUN_ALL_TESTS.sh                 # Run all tests in sequence
└── README.md                        # This file
```

## Prerequisites

1. **Snowflake credentials** in `.env`:
   ```bash
   SNOWFLAKE_ACCOUNT=your_account
   SNOWFLAKE_USER=your_user
   SNOWFLAKE_PASSWORD=your_password
   SNOWFLAKE_WAREHOUSE=your_warehouse
   SNOWFLAKE_DATABASE=your_database
   ```

2. **Gemini API key** in `.env`:
   ```bash
   GEMINI_API_KEY=your_key
   GEMINI_MODEL=gemini-2.5-pro
   ```

3. **Python dependencies installed**:
   ```bash
   pip3 install -r ../requirements.txt
   ```

## Running Individual Tests

### Test 1: Snowflake Ingestion Agent

**What it does:**
- Uploads CSV to Snowflake stage
- Auto-detects schema using `INFER_SCHEMA`
- Creates table and loads data
- Returns row/column counts

**Run:**
```bash
python3 01_test_snowflake_ingestion.py
```

**Expected Output:**
```
✅ SUCCESS! Data ingested to Snowflake
────────────────────────────────────────
📊 Table Name:     RAW_test_session_001_DATASET_1
📈 Rows Loaded:    5
📋 Column Count:   8
📦 Stage Name:     @EY_STAGE_test_session_001_1
```

---

### Test 2: Gemini Schema Agent

**What it does:**
- Queries Snowflake for table metadata
- Gets sample data
- Sends to Gemini 2.5 Pro for semantic analysis
- Returns structured schema understanding

**Run:**
```bash
python3 02_test_gemini_schema.py
```

**Expected Output:**
```
✅ SUCCESS! Gemini analyzed the schema
────────────────────────────────────────
📊 Table:          RAW_test_session_001_DATASET_1
🏷️  Business Domain: CRM
🔑 Primary Key:    cust_id
🔗 Join Keys:      cust_id, email_addr
📋 Columns Found:  8
```

---

### Test 3: Gemini Mapping Agent

**What it does:**
- Takes schema analysis from 2 datasets
- Uses Gemini 2.5 Pro to propose column mappings
- Provides confidence scores
- Flags ambiguous mappings for Jira escalation

**Run:**
```bash
python3 03_test_gemini_mapping.py
```

**Expected Output:**
```
✅ SUCCESS! Gemini proposed column mappings
────────────────────────────────────────
✅ High Confidence Mappings: 3
⚠️  Medium Confidence:        2
❌ Low Confidence (Conflicts): 1
🎫 Jira Escalations Needed:  1
```

---

### Test 4: Master Agent

**What it does:**
- Analyzes dataset complexity
- Autonomously decides resource allocation
- Spawns agent pools dynamically
- Orchestrates full pipeline

**Run:**
```bash
python3 04_test_master_agent.py
```

**Choose:**
1. Resource Allocation Test (no Snowflake needed)
2. Full Orchestration Test (requires previous tests)

**Expected Output:**
```
🤖 Testing Master Agent decision making:

📊 Scenario: Small dataset
   Rows: 5,000
   Columns: 8
   Complexity: low

   🎯 Master Agent Decision:
   ├─ Gemini Agents:    1
   ├─ Merge Agents:     2
   ├─ Quality Agents:   3
   └─ Snowflake WH:     SMALL
```

---

## Running All Tests

Run the complete test suite in sequence:

```bash
chmod +x RUN_ALL_TESTS.sh
./RUN_ALL_TESTS.sh
```

This will:
1. Run Test 1 → pause for review
2. Run Test 2 → pause for review
3. Run Test 3 → pause for review
4. Run Test 4 → complete

## Test Results

All test outputs are logged to: `test_agents.log`

## Adding New Agent Tests

To test a new agent:

1. Create `05_test_your_agent.py`:
```python
#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_harness import test_agent, print_header
from agents.your_module.your_agent import YourAgent

async def main():
    print_header("YOUR AGENT TEST")
    
    result = await test_agent(
        YourAgent,
        "Test description",
        param1="value1",
        param2="value2"
    )
    
    # Print results, check for errors, etc.

if __name__ == "__main__":
    asyncio.run(main())
```

2. Make it executable:
```bash
chmod +x 05_test_your_agent.py
```

3. Run it:
```bash
python3 05_test_your_agent.py
```

## Troubleshooting

### Snowflake Connection Failed
```
❌ FAILED: Snowflake connection error
```

**Fix:**
- Check `.env` file has correct credentials
- Ensure warehouse is running
- Verify network allows Snowflake connections
- Test with: `python3 -c "from sf_infrastructure.connector import snowflake_connector; print(snowflake_connector)"`

### Gemini API Error
```
❌ FAILED: Gemini API key invalid
```

**Fix:**
- Check `GEMINI_API_KEY` in `.env`
- Verify API quota not exceeded
- Ensure model is `gemini-2.5-pro`
- Test with: `python3 -c "import google.generativeai as genai; genai.configure(api_key='your_key')"`

### Import Errors
```
ModuleNotFoundError: No module named 'agents'
```

**Fix:**
- Run from `test_agents/` directory
- Ensure parent directory in path
- Check `sys.path.insert` in test file

## Next Steps

After all tests pass:
1. ✅ Individual agents work in isolation
2. 🔄 Integrate agents into API routes
3. 🚀 Test end-to-end pipeline via FastAPI
4. 🎯 Run full demo

## Questions?

Refer back to the main roadmap:
- Architecture overview
- Agent specifications
- MVP flow
- API endpoints
