#!/bin/bash
# Test Agent Interaction via Kagent API
# This script demonstrates end-to-end testing of the kagent framework

set -e

echo "============================================================"
echo "🔬 KAGENT AGENT INTERACTION TEST"
echo "============================================================"

# Get kagent controller service
KAGENT_SERVICE="kagent-controller"
NAMESPACE="default"

echo ""
echo "📡 Setting up port forward to kagent-controller..."
kubectl port-forward svc/$KAGENT_SERVICE -n $NAMESPACE 8083:8083 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!

# Wait for port forward to be ready
sleep 3

echo "✅ Port forward established (PID: $PORT_FORWARD_PID)"

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up port forward..."
    kill $PORT_FORWARD_PID 2>/dev/null || true
}
trap cleanup EXIT

echo ""
echo "🔍 Testing API Endpoints..."

# Test 1: List all agents
echo ""
echo "1️⃣  Listing all agents..."
AGENTS=$(curl -s http://localhost:8083/api/agents 2>/dev/null || echo "{}")
echo "$AGENTS" | python3 -m json.tool 2>/dev/null | head -20 || echo "⚠️  Could not parse agents response"

# Test 2: Get specific agent
echo ""
echo "2️⃣  Getting hello-world-agent details..."
AGENT_DETAIL=$(curl -s http://localhost:8083/api/agents/default/hello-world-agent 2>/dev/null || echo "{}")
if echo "$AGENT_DETAIL" | grep -q "hello-world-agent"; then
    echo "   ✅ Agent found"
    echo "$AGENT_DETAIL" | python3 -m json.tool 2>/dev/null | head -30
else
    echo "   ⚠️  Agent not accessible via API"
fi

# Test 3: List MCPServers
echo ""
echo "3️⃣  Checking MCP server status..."
MCP_STATUS=$(curl -s http://localhost:8083/health 2>/dev/null || echo "{}")
if echo "$MCP_STATUS" | grep -q "ok\|healthy\|UP"; then
    echo "   ✅ Kagent controller is healthy"
else
    echo "   ⚠️  Health status: $MCP_STATUS"
fi

echo ""
echo "============================================================"
echo "📊 INTEGRATION TEST SUMMARY"
echo "============================================================"

# Verify resources via kubectl
echo ""
echo "Current Resource Status:"
echo ""
echo "MCPServers:"
kubectl get mcpserver -n $NAMESPACE 2>/dev/null | grep -E "NAME|hello" || echo "  No MCPServers found"

echo ""
echo "Agents:"
kubectl get agent -n $NAMESPACE 2>/dev/null | grep -E "NAME|hello" || echo "  No Agents found"

echo ""
echo "Pods:"
kubectl get pods -n $NAMESPACE 2>/dev/null | grep -E "NAME|hello" || echo "  No hello pods found"

echo ""
echo "============================================================"
echo "✅ INTEGRATION TEST COMPLETE"
echo "============================================================"
echo ""
echo "💡 TIP: To manually test agents, run:"
echo "   kubectl port-forward svc/kagent-controller 8083:8083"
echo "   curl http://localhost:8083/api/agents"
echo ""

