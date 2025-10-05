# 🤖 EY Data Integration AI Assistant - API Documentation

## Overview

The EY Data Integration AI Assistant is powered by a **Gemini 2.5 Pro orchestration agent** that understands natural language and coordinates 6+ specialized agents to perform enterprise data integration tasks.

---

## 🚀 Main API Endpoint

### **POST /chat**

**URL:** `http://localhost:8002/chat`

**Description:** Main conversational interface to the Gemini orchestration agent

**Request Body:**
```json
{
  "message": "string (required) - Natural language message",
  "session_id": "string (optional) - Session identifier for conversation continuity",
  "user_id": "string (optional) - User identifier"
}
```

**Response:**
```json
{
  "answer": "string - AI response with results",
  "confidence": "integer - Confidence score (0-100)",
  "reasoning": "string - Explanation of actions taken (optional)",
  "suggested_action": "object - Next steps (optional)"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "merge RAW_ACCOUNTS_DATASET_1 and RAW_ACCOUNTS_DATASET_2",
    "session_id": "demo_001"
  }'
```

**Example Response:**
```json
{
  "answer": "✅ I've completed your merge request:\n\n✅ Analyze table schemas: Complete\n✅ AI-powered column mapping: Complete\n✅ Execute SQL merge: Complete\n✅ Validate merged data: Complete\n\n📊 Created: MERGED_RAW_ACCOUNTS_DATASET_0_RAW_ACCOUNTS_DATASET_0\n   • 30,040 rows merged\n\n💡 Next: You can query the merged data or run more quality checks.",
  "confidence": 95,
  "reasoning": "Executed 4 actions: Analyze table schemas, AI-powered column mapping, Execute SQL merge, Validate merged data"
}
```

---

## 📊 Web Interface

### **GET /**

**URL:** `http://localhost:8002/`

**Description:** Beautiful web-based chat interface

**Returns:** HTML page with:
- Modern gradient UI
- Real-time typing indicators
- Quick action buttons
- Conversation history

---

## 🎯 Supported Operations

### 1. **Merge Datasets**

**Natural Language:**
- "merge TABLE1 and TABLE2"
- "combine RAW_ACCOUNTS_1 and RAW_ACCOUNTS_2"
- "join DATASET_A with DATASET_B"

**What Happens:**
1. Schema Reader Agent analyzes both tables
2. Mapping Agent proposes AI-powered column mappings
3. Join Agent executes FULL OUTER JOIN (preserves all data)
4. Stats Agent validates the merged result

**Response Time:** ~40 seconds (actual work)

---

### 2. **Analyze Table Schema**

**Natural Language:**
- "analyze UNIFIED_ACCOUNTS"
- "what's in the TRANSACTIONS table?"
- "show me the schema of CUSTOMER_DATA"

**What Happens:**
1. Schema Reader Agent reads table structure
2. Gemini analyzes column types and relationships
3. Returns schema summary with sample data

**Response Time:** ~5 seconds

---

### 3. **Validate Data Quality**

**Natural Language:**
- "validate data quality in UNIFIED_ACCOUNTS"
- "check TRANSACTIONS for issues"
- "are there any problems with CUSTOMER_DATA?"

**What Happens:**
1. Validation Monitor runs sanity checks
2. Stats Agent computes quality metrics
3. Returns issues found (NULL data, duplicates, etc.)

**Response Time:** ~3 seconds

---

### 4. **Get Help / Capabilities**

**Natural Language:**
- "hello"
- "what can you do?"
- "help"

**Response Time:** Instant (0.03 seconds)

---

## 🧠 Agent Architecture

The system uses **6 specialized agents** orchestrated by the main Gemini agent:

| Agent | Capability | Purpose |
|-------|-----------|---------|
| **Validation Monitor** | `data_quality` | Real-time quality checks |
| **Snowflake Ingestion** | `data_ingestion` | Upload files to Snowflake |
| **Schema Reader** | `schema_analysis` | Analyze table structures |
| **Mapping Agent** | `conflict_detection` | AI-powered column mapping |
| **Join Agent** | `merge_execution` | Execute SQL merges |
| **Stats Agent** | `data_quality` | Statistical analysis |

**All agents are auto-initialized on server startup.**

See `agents.yaml` for full configuration.

---

## 🐍 Python Client

```python
import requests

def chat(message: str, session_id: str = "default"):
    response = requests.post(
        "http://localhost:8002/chat",
        json={
            "message": message,
            "session_id": session_id
        }
    )
    return response.json()

# Example: Merge datasets
result = chat("merge TABLE1 and TABLE2", session_id="my_session")
print(result['answer'])
```

**Full client example:** See `api_client_example.py`

---

## 📈 Performance

| Operation | Response Time |
|-----------|--------------|
| Simple queries (hello, help) | **0.03 seconds** |
| Schema analysis | **~5 seconds** |
| Data quality validation | **~3 seconds** |
| Full merge workflow | **~40 seconds** |

**Note:** Merge times depend on:
- Table size
- Schema complexity
- Number of columns
- Gemini API latency

---

## 🔧 Server Management

### Start Server
```bash
python3 chatbot_server.py
```

### Check Status
```bash
curl http://localhost:8002/
```

### View Logs
```bash
tail -f /tmp/chatbot_FAST.log
```

### Stop Server
```bash
lsof -ti:8002 | xargs kill
```

---

## 🎨 Visualization

**Real-time Agent Communication:** `http://localhost:8001`

Shows:
- Agent nodes
- Communication flows
- Event logs
- System statistics

---

## 📚 Data Available

Current Snowflake tables:
- `UNIFIED_ACCOUNTS` - 79,511 rows
- `UNIFIED_TRANSACTIONS` - 397,250 rows
- `MERGED_*` - Various merged datasets

---

## 🚨 Error Handling

The API returns friendly error messages:

```json
{
  "answer": "I encountered an error: <details>. Please try again.",
  "confidence": 0,
  "reasoning": "Exception: <error type>"
}
```

**Common Issues:**
- Table not found → Check table name spelling
- Slow response → System is processing (check logs)
- Connection error → Ensure server is running

---

## 🎯 Best Practices

1. **Use clear table names** - Spell them exactly as they appear in Snowflake
2. **Be specific** - "merge TABLE1 and TABLE2" is better than "merge data"
3. **Use session IDs** - Maintains conversation context
4. **Check confidence** - Values < 50 may indicate issues

---

## 📞 Support

- **YAML Config:** `agents.yaml`
- **Client Example:** `api_client_example.py`
- **Agent Code:** `agents/orchestration/conversational_agent.py`
- **Server Code:** `chatbot_server.py`

---

## 🏆 Production Ready

✅ Natural language interface  
✅ Multi-agent orchestration  
✅ Real-time execution  
✅ Snowflake integration  
✅ Quality validation  
✅ Error handling  
✅ Session management  

**Ready for your hackathon demo!** 🚀
