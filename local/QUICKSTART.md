# Quick Start Guide - EY Data Integration SaaS

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd /Users/varriza/Documents/HACKARTHONS/HackTheValley/local
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy and edit .env
cp .env.example .env

# Minimum required configuration:
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=EY_DATA_INTEGRATION

GEMINI_API_KEY=your_gemini_key
```

### 3. Start the Server
```bash
python main.py
```

Server will start at: http://localhost:8000

### 4. Test the API

Open http://localhost:8000/docs for interactive API documentation.

#### Upload Datasets
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "dataset1=@examples/dataset1_customers.csv" \
  -F "dataset2=@examples/dataset2_clients.csv"
```

Response:
```json
{
  "session_id": "abc12345",
  "status": "uploaded",
  "dataset1": {...},
  "dataset2": {...}
}
```

#### Analyze Schemas (Gemini 2.5 Pro)
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc12345"}'
```

This will:
- Master Agent analyzes workload
- Spawns N Gemini agents
- Returns proposed column mappings

#### Approve & Merge
```bash
curl -X POST http://localhost:8000/api/v1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc12345",
    "approved_mappings": [...],
    "merge_type": "full_outer"
  }'
```

Returns `job_id` for tracking.

#### Check Status
```bash
curl http://localhost:8000/api/v1/status/{job_id}
```

#### Download Results
```bash
curl http://localhost:8000/api/v1/download/abc12345?format=csv \
  --output merged_data.csv
```

## Docker Quick Start

```bash
# Build and run with docker-compose
docker-compose up --build

# Or build and run single container
docker build -t ey-integration .
docker run -p 8000:8000 --env-file .env ey-integration
```

## Testing with Example Data

The `examples/` directory contains sample datasets:

- **dataset1_customers.csv**: 10 customer records
- **dataset2_clients.csv**: 8 client records (3 overlap, 5 unique)

Intentional conflicts for testing:
- Column naming differences: `cust_id` vs `customer_number`
- Email case: `john@example.com` vs `JOHN@EXAMPLE.COM`
- Type differences: Integer vs string IDs

## Architecture at a Glance

```
Master Agent decides: "This workload needs 2 Gemini agents + 5 merge agents"
                                    ↓
                      Gemini agents analyze schemas
                                    ↓
                      Propose mappings (confidence scores)
                                    ↓
            If confidence < 70% → Create Jira ticket (if enabled)
                                    ↓
                      User approves mappings
                                    ↓
                Merge agents execute SQL in Snowflake
                                    ↓
                Quality agents validate results
                                    ↓
                      Download merged dataset
```

## Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/upload` | Upload 2 datasets |
| POST | `/api/v1/analyze` | Gemini schema analysis |
| POST | `/api/v1/approve` | Start merge |
| GET | `/api/v1/status/{job_id}` | Check progress |
| POST | `/api/v1/validate` | Quality checks |
| GET | `/api/v1/download/{session_id}` | Download result |
| GET | `/api/v1/health` | Health check |
| WS | `/api/v1/ws/{session_id}` | Real-time updates |

## Troubleshooting

### "Snowflake connection failed"
- Check `.env` credentials
- Ensure warehouse is running
- Verify network access

### "Gemini API error"
- Verify `GEMINI_API_KEY`
- Check quota limits
- Ensure model is `gemini-2.5-pro`

### "Import errors"
- Activate virtual environment
- Run `pip install -r requirements.txt`
- Check Python version >= 3.10

## Next Steps

1. **Connect your Snowflake instance**
2. **Add your Gemini API key**
3. **Upload your own datasets**
4. **Enable Jira integration (optional)**
5. **Add Datadog monitoring (optional)**

## Demo Flow

For hackathon demo:
1. Start server
2. Upload example datasets
3. Show Master Agent decision (check logs)
4. Display Gemini mappings
5. Show conflict detection
6. Execute merge
7. Display quality report
8. Download results

**Total demo time: ~3 minutes**

## Support

- API Documentation: http://localhost:8000/docs
- Roadmap: See detailed roadmap document
- Examples: `examples/` directory

---

**Ready to integrate data intelligently!** 🚀

