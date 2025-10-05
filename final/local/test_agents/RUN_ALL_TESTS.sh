#!/bin/bash
# Run all agent tests in sequence
# Each test builds on the previous one

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        EY Data Integration - Agent Test Suite                ║"
echo "║                                                              ║"
echo "║  Testing each agent individually before integration          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Change to test directory
cd "$(dirname "$0")"

echo "🔧 Setup: Checking dependencies..."
python3 -c "import asyncio, logging" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Python dependencies missing"
    exit 1
fi
echo "✅ Dependencies OK"
echo ""

# Test 1: Snowflake Ingestion
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 TEST 1: Snowflake Ingestion Agent"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 01_test_snowflake_ingestion.py
if [ $? -ne 0 ]; then
    echo "❌ Test 1 failed. Fix before proceeding."
    exit 1
fi
echo "✅ Test 1 passed"
echo ""
read -p "Press Enter to continue to Test 2..."
echo ""

# Test 2: Gemini Schema
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧠 TEST 2: Gemini Schema Agent"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 02_test_gemini_schema.py
if [ $? -ne 0 ]; then
    echo "❌ Test 2 failed. Fix before proceeding."
    exit 1
fi
echo "✅ Test 2 passed"
echo ""
read -p "Press Enter to continue to Test 3..."
echo ""

# Test 3: Gemini Mapping
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 TEST 3: Gemini Mapping Agent"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 03_test_gemini_mapping.py
if [ $? -ne 0 ]; then
    echo "❌ Test 3 failed. Fix before proceeding."
    exit 1
fi
echo "✅ Test 3 passed"
echo ""
read -p "Press Enter to continue to Test 4..."
echo ""

# Test 4: Master Agent
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 TEST 4: Master Agent"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1" | python3 04_test_master_agent.py  # Auto-select option 1 (resource allocation)
if [ $? -ne 0 ]; then
    echo "❌ Test 4 failed."
    exit 1
fi
echo "✅ Test 4 passed"
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   ALL TESTS PASSED! 🎉                       ║"
echo "║                                                              ║"
echo "║  All agents are working individually                         ║"
echo "║  Ready to integrate into full pipeline                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Test Results Summary:"
echo "   ✅ Snowflake Ingestion Agent - Data uploaded to Snowflake"
echo "   ✅ Gemini Schema Agent - Semantic analysis working"
echo "   ✅ Gemini Mapping Agent - Column mappings generated"
echo "   ✅ Master Agent - Autonomous decision making operational"
echo ""
echo "🚀 Next Steps:"
echo "   1. Test remaining agents (Merge, Quality, Jira)"
echo "   2. Integrate agents into full pipeline"
echo "   3. Test end-to-end flow via API"
echo ""
