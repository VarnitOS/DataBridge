# 🚀 Quick Start - Test Agents One by One

## Step 1: Run Test 1 (Snowflake Ingestion)

```bash
cd test_agents
python3 01_test_snowflake_ingestion.py
```

**This will:**
- Create a sample CSV file
- Upload it to Snowflake
- Create a table
- Show you the row count and columns

**You should see:**
```
✅ SUCCESS! Data ingested to Snowflake
📊 Table Name:     RAW_test_session_001_DATASET_1
📈 Rows Loaded:    5
📋 Column Count:   8
```

## Step 2: Run Test 2 (Gemini Schema Analysis)

```bash
python3 02_test_gemini_schema.py
```

**Press Enter when asked for table name** (it will use the table from Test 1)

**This will:**
- Query Snowflake for the table schema
- Send schema + sample data to Gemini 2.5 Pro
- Get AI-powered semantic understanding
- Show what each column means

**You should see:**
```
✅ SUCCESS! Gemini analyzed the schema
🏷️  Business Domain: CRM
🔑 Primary Key:    cust_id
```

## Step 3: Run Test 3 (Gemini Mapping)

```bash
python3 03_test_gemini_mapping.py
```

**This will:**
- Use Gemini to propose column mappings between 2 datasets
- Show confidence scores
- Flag ambiguous mappings

**You should see:**
```
✅ SUCCESS! Gemini proposed column mappings
✅ cust_id ↔ customer_number
   → Confidence: 95%
   → Unified Name: customer_id
```

## Step 4: Run Test 4 (Master Agent)

```bash
python3 04_test_master_agent.py
```

**Choose option 1** (Resource Allocation - doesn't need Snowflake)

**This will:**
- Show autonomous decision making
- Test different dataset sizes
- See how Master Agent scales resources

## Run All Tests at Once

```bash
./RUN_ALL_TESTS.sh
```

This runs all 4 tests in sequence with pauses for review.

## That's It!

You're now testing agents **one at a time** instead of all together.

Much easier to debug and understand! 🎉
