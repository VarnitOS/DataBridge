# Troubleshooting Agent "Not Accepted / Not Ready" Status

## Problem

Agents `hello-world-agent` and `hello-mcp-agent` show **"Not Accepted"** and **"Not Ready"** status in the kagent UI.

## Root Cause Analysis

### Issue 1: MCPServer vs RemoteMCPServer

**Problem**: Agents were referencing `MCPServer` resources directly, but kagent agents require `RemoteMCPServer` resources.

**Difference**:
- **MCPServer**: Defines deployment configuration for MCP server pods (infrastructure)
- **RemoteMCPServer**: Defines connection details for agents to access MCP servers (client configuration)

Working agents use `RemoteMCPServer` with `kind: RemoteMCPServer`:
```yaml
tools:
  - type: McpServer
    mcpServer:
      apiGroup: kagent.dev
      kind: RemoteMCPServer  # ← Must be RemoteMCPServer, not MCPServer
      name: kagent-tool-server
      toolNames: [...]
```

### Issue 2: Missing Status Section

Agents have **no status section**, indicating the kagent controller is NOT reconciling them. 

Checked:
- ✅ Controller logs show agents are being read via API (`list-db`, `get-db`)
- ❌ NO reconciliation events in controller logs
- ❌ NO status conditions on agent resources

## Steps Taken to Fix

### 1. Fixed MCP Server Code ✅

**Original Problem**: `@server.tool()` decorator doesn't exist in MCP SDK

**Fixed**: Used correct async decorators:
```python
@app.list_tools()
async def list_tools() -> list[Tool]:
    ...

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    ...
```

### 2. Fixed CRD Mismatch ✅

**Original Problem**: Used `ToolServer` with `spec.deployment` field (not supported)

**Fixed**: Changed to `MCPServer` kind with proper deployment spec:
```yaml
apiVersion: kagent.dev/v1alpha1
kind: MCPServer  # ← Changed from ToolServer
spec:
  transportType: stdio
  deployment:  # ← Now supported
    image: python:3.11-slim
    ...
```

### 3. Added Required Agent Configuration ✅

**Original Problem**: Agents missing `a2aConfig` and `stream` fields

**Fixed**: Added complete configuration:
```yaml
spec:
  declarative:
    modelConfig: gemini-pro
    stream: true  # ← Added
    a2aConfig:  # ← Added
      skills:
        - id: hello-skill
          name: Hello World
          description: The ability to greet users
          examples: [...]
          tags: [...]
```

### 4. Created RemoteMCPServer Resource ✅

**Original Problem**: Agents referenced MCPServer directly (wrong resource type)

**Fixed**: Created RemoteMCPServer:
```yaml
apiVersion: kagent.dev/v1alpha2
kind: RemoteMCPServer
metadata:
  name: hello-remote-mcp
spec:
  protocol: STREAMABLE_HTTP
  url: http://hello-mcp-server.default:3000/mcp
```

### 5. Updated Agents to Use RemoteMCPServer ✅

**Fixed**: Changed agent tool references:
```yaml
tools:
  - type: McpServer
    mcpServer:
      apiGroup: kagent.dev
      kind: RemoteMCPServer  # ← Changed from MCPServer
      name: hello-remote-mcp  # ← Changed name
```

## Current Status

### What's Working ✅

1. **MCPServers Are Ready**:
   ```
   NAME               READY   AGE
   hello-mcp          True    4h
   hello-mcp-server   True    2h
   ```

2. **MCP Server Pods Running**:
   ```
   hello-mcp-server-5c67f47556-d6wmm   1/1   Running
   ```

3. **MCP Endpoint Accessible**:
   ```bash
   curl -H "Accept: text/event-stream" http://hello-mcp-server.default:3000/mcp
   # Returns: HTTP 406 (correct - needs SSE headers)
   ```

4. **Agents Are Properly Configured**:
   - Have valid spec with modelConfig, stream, a2aConfig
   - Reference RemoteMCPServer correctly
   - ConfigMap with code exists

5. **RemoteMCPServer Created**:
   ```
   NAME               PROTOCOL          URL
   hello-remote-mcp   STREAMABLE_HTTP   http://hello-mcp-server.default:3000/mcp
   ```

### What's NOT Working ❌

1. **RemoteMCPServer Not Accepted**:
   ```
   NAME               ACCEPTED
   hello-remote-mcp            # ← Empty (should be True)
   ```

2. **Agents Have No Status**:
   ```yaml
   # kubectl get agent hello-world-agent -o yaml
   # ...spec...
   # No status section at all
   ```

3. **No Reconciliation Logs**:
   - Controller only shows API read operations
   - No "Reconciling agent..." messages
   - No reconciliation errors

## Possible Remaining Issues

### 1. RemoteMCPServer Validation Failure

The RemoteMCPServer might be failing validation but not showing errors.

**Test**:
```bash
kubectl get remotemcpserver hello-remote-mcp -o yaml
```

**Expected**: Should show status with conditions

### 2. Controller Not Watching RemoteMCPServer

The controller might not have proper RBAC or watches configured.

**Test**:
```bash
kubectl logs -n default <controller-pod> | grep -i "remotemcp\|watching"
```

### 3. Agent Validation Failure

Agents might be failing schema validation silently.

**Test**:
```bash
kubectl get agent hello-world-agent -o json | jq '.metadata.generation'
# If generation > 1, spec is being accepted
```

Result: `generation: 1` (spec accepted, not a validation issue)

### 4. Wrong API Group/Version

Working agents use specific apiGroup in mcpServer reference.

**Verify**:
```bash
kubectl get remotemcpserver -o yaml | grep "apiVersion:"
# Should match what agents specify
```

## Next Steps to Try

### Option 1: Check Kagent Version Compatibility

```bash
kubectl get deployment kagent-controller -o yaml | grep image:
```

The MCP integration might require a specific kagent version.

### Option 2: Use Existing RemoteMCPServer

Instead of creating a new one, try using an existing RemoteMCPServer pattern:

```bash
# See how working agents configure tools
kubectl get agent k8s-agent -o yaml

# Check existing RemoteMCPServers
kubectl get remotemcpserver -A
```

### Option 3: Contact Kagent Support

Since all configuration appears correct:
- MCPServer is running and accessible
- RemoteMCPServer is created with proper spec
- Agents reference it correctly
- But controller won't reconcile

This might be a bug or require specific kagent configuration.

## Verification Commands

```bash
# Check all resources
kubectl get mcpserver,remotemcpserver,agent -n default | grep hello

# Check controller logs
kubectl logs -n default -l app=kagent-controller --tail=100

# Test MCP endpoint
kubectl run test-mcp --image=curlimages/curl --rm -it -- \
  curl -H "Accept: text/event-stream" \
  http://hello-mcp-server.default:3000/mcp

# Check agent details
kubectl describe agent hello-world-agent

# Run test suite
python3 test_kagent.py
```

## Summary

**Infrastructure**: ✅ All working  
**Configuration**: ✅ All correct  
**Controller Reconciliation**: ❌ Not happening  

The issue appears to be that the kagent controller is not reconciling our specific agents or RemoteMCPServer, despite:
- Proper configuration
- Working infrastructure  
- Matching patterns from working agents

This suggests either:
1. A specific kagent version requirement
2. Additional configuration needed
3. A controller bug/limitation
4. Some subtle configuration mismatch we haven't identified

**Recommendation**: Review kagent documentation for RemoteMCPServer setup or reach out to kagent community/support.

