# Kagent Framework with MCP Integration

This project demonstrates the complete setup and testing of the **kagent framework** with **Model Context Protocol (MCP)** servers.

## 🎯 Overview

This repository contains:
- **MCP Servers**: Python-based MCP servers that expose tools via stdio
- **Kagent Agents**: AI agents configured to use MCP tools
- **Kubernetes Manifests**: Complete deployment configurations
- **Test Suite**: Comprehensive validation of the entire setup

## 📁 Project Structure

```
.
├── test/
│   ├── hello.py           # Original simple hello tool
│   ├── hello_mcp.py       # MCP server implementation
│   └── Dockerfile         # Docker configuration
├── Dockerfiles/
│   └── Dockerfile         # Organized Dockerfile
├── hello-mcp-tool.yaml            # ConfigMap with MCP server code
├── hello-mcp-server.yaml          # MCPServer resource
├── hello-mcp-agent.yaml           # Agent using MCP server
├── hello-agent.yaml               # Alternative agent config
├── gemini-model.yaml              # Gemini model configuration
├── test_kagent.py                 # Comprehensive test suite
└── README.md                      # This file
```

## 🚀 Components

### 1. MCP Servers

**hello-mcp MCPServer**
- Runs a simple Python tool via stdio
- Exposes a `hello` tool that returns "Hello World"
- Status: ✅ Ready and Running

**hello-mcp-server MCPServer**
- Full MCP server implementation with proper protocol
- Async tool handling
- Status: ✅ Ready and Running

### 2. Agents

**hello-world-agent**
- Declarative agent using Gemini model
- References MCPServer/hello-mcp
- Configured with a2aConfig skills
- Tool: hello

**hello-mcp-agent**
- Advanced MCP agent
- References MCPServer/hello-mcp-server
- Full skill-based configuration
- Tool: hello

### 3. Model Configuration

- **Model**: gemini-2.5-pro
- **Provider**: OpenAI (via kagent)
- **Status**: ✅ Configured and ready

## 📋 Prerequisites

- Kubernetes cluster (local or cloud)
- kubectl configured
- Python 3.x
- kagent framework installed

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/shaunp18/HackValley.git
cd HackValley
```

### 2. Deploy MCP Servers

```bash
# Deploy ConfigMap with MCP server code
kubectl apply -f hello-mcp-tool.yaml

# Deploy MCPServers
kubectl apply -f hello-mcp-server.yaml
```

### 3. Deploy Agents

```bash
# Deploy model configuration
kubectl apply -f gemini-model.yaml

# Deploy agents
kubectl apply -f hello-mcp-agent.yaml
kubectl apply -f hello-agent.yaml
```

### 4. Verify Deployment

```bash
# Check MCPServers
kubectl get mcpserver

# Check Agents
kubectl get agent

# Check pods
kubectl get pods | grep hello
```

## ✅ Testing

### Run Comprehensive Test Suite

```bash
python3 test_kagent.py
```

### Test Results

```
============================================================
📊 KAGENT FRAMEWORK TEST SUMMARY
============================================================
✅ Passed: 15
❌ Failed: 0
📈 Total:  15
============================================================
🎉 ALL TESTS PASSED!
```

### What is Tested

- ✅ MCPServer resources exist and are ready
- ✅ MCPServer pods are running
- ✅ MCP services are accessible
- ✅ MCP server logs show proper initialization
- ✅ Agent resources are properly configured
- ✅ Agents reference correct MCPServers
- ✅ ModelConfig is set up correctly
- ✅ ConfigMaps contain required code
- ✅ Kagent controller is running
- ✅ Kagent UI is running

## 🔍 Verification Commands

### Check MCPServer Status

```bash
kubectl get mcpserver hello-mcp -o yaml
kubectl get mcpserver hello-mcp-server -o yaml
```

### Check Agent Status

```bash
kubectl describe agent hello-world-agent
kubectl describe agent hello-mcp-agent
```

### View MCP Server Logs

```bash
kubectl logs -l app=hello-mcp-server
```

### Check Services

```bash
kubectl get svc | grep hello
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Kagent Framework                   │
│  ┌──────────────────────────────────────┐   │
│  │  Agents (hello-world-agent, etc.)    │   │
│  │  - Uses Gemini model                 │   │
│  │  - Configured with a2aConfig         │   │
│  │  - References MCP tools              │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │  MCPServers (hello-mcp-server)       │   │
│  │  - Stdio transport                   │   │
│  │  - Tool registration                 │   │
│  │  - Async handlers                    │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │  Python MCP Server (hello_mcp.py)    │   │
│  │  - list_tools()                      │   │
│  │  - call_tool()                       │   │
│  │  - Returns "Hello World"             │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## 🐛 Troubleshooting

### MCPServer Not Ready

```bash
# Check MCPServer status
kubectl describe mcpserver hello-mcp-server

# Check pod logs
kubectl logs <mcpserver-pod-name>
```

### Agent Not Working

```bash
# Verify MCPServer is running
kubectl get mcpserver

# Check agent configuration
kubectl get agent hello-world-agent -o yaml

# Restart kagent controller
kubectl delete pod -l app=kagent-controller -n default
```

### Tool Invocation Fails

```bash
# Test MCP server directly
kubectl exec -it <mcp-pod-name> -- python /tools/hello_mcp.py

# Check ConfigMap
kubectl get configmap hello-mcp-tool -o yaml
```

## 📚 Key Learnings

### CRD Differences

1. **ToolServer**: Only defines stdio command configuration, doesn't deploy pods
2. **MCPServer**: Full resource with deployment spec, manages pods automatically

### Agent Configuration

- **a2aConfig** (Agent-to-Agent) with skills is required for proper reconciliation
- **stream: true** enables streaming responses
- Tools must reference **MCPServer** (not ToolServer) for proper deployment

### MCP Server Implementation

- Use `@app.list_tools()` to register tool schemas
- Use `@app.call_tool()` to handle tool invocations
- Must use async functions
- Returns `TextContent` objects

## 🔗 Resources

- [Kagent Documentation](https://kagent.dev)
- [MCP Protocol](https://modelcontextprotocol.io)
- [GitHub Repository](https://github.com/shaunp18/HackValley)

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Contributions welcome! Please submit pull requests or open issues on GitHub.

---

**Status**: ✅ All systems operational
**Last Updated**: October 4, 2025
**Test Suite**: 15/15 tests passing

