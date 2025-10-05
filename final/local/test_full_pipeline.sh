#!/bin/bash
# Full agent pipeline test - triggers ALL agents!

echo "🚀 EY Data Integration - Full Agent Pipeline Test"
echo "=================================================="
echo ""

# Step 1: Upload datasets
echo "📤 Step 1: Uploading datasets..."
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/upload" \
  -F "dataset1=@sample_dataset_1.csv" \
  -F "dataset2=@sample_dataset_2.csv")

SESSION_ID=$(echo $UPLOAD_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo "✅ Session created: $SESSION_ID"
echo ""

# Step 2: Analyze schemas (triggers Gemini agents)
echo "🧠 Step 2: Analyzing schemas (spawning Gemini agents)..."
ANALYZE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\"}")

echo "$ANALYZE_RESPONSE" | python3 -m json.tool
echo ""

# Step 3: Approve and merge (triggers Merge + Quality agents)
echo "🔗 Step 3: Approving mappings (spawning Merge & Quality agents)..."
APPROVE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/approve" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"approved_mappings\": [],
    \"merge_type\": \"full_outer\"
  }")

JOB_ID=$(echo $APPROVE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "$APPROVE_RESPONSE" | python3 -m json.tool
echo ""

# Step 4: Check status
echo "📊 Step 4: Checking job status..."
sleep 2
curl -s "http://localhost:8000/api/v1/status/$JOB_ID" | python3 -m json.tool
echo ""

echo "=================================================="
echo "✅ Pipeline Complete!"
echo ""
echo "💡 Watch your agent_monitor.html to see all agents working in real-time!"
echo "💡 Session ID: $SESSION_ID"
echo "💡 Job ID: $JOB_ID"
echo ""
echo "Check server logs to see agent communication:"
echo "  tail -f /dev/ttys* | grep -E 'Agent|Gemini|Merge|Quality'"
