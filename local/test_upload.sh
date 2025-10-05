#!/bin/bash
# Test script to trigger real agent pipeline

echo "🚀 Uploading datasets to trigger agent pipeline..."
echo ""

# Upload the files
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "dataset1=@sample_dataset_1.csv" \
  -F "dataset2=@sample_dataset_2.csv" \
  | python3 -m json.tool

echo ""
echo "✅ Upload complete! Check your agent_monitor.html to see agents working!"
echo "   The agents are now processing the datasets in real-time."
