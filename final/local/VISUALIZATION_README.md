# 🎨 Real-Time Agent Communication Visualization

## What This Does

This visualization shows **real-time agent communication** in your multi-agent system with:
- **Interactive graph** showing all agents as nodes
- **Animated "liquid flows"** (green particles) when agents communicate
- **Real-time event log** showing all A2A (Agent-to-Agent) calls
- **Live statistics** (agent count, event count, active agents)

## How It Works

1. **Event Bus** (`core/event_bus.py`) - Broadcasts agent events
2. **WebSocket Server** (`visualization_server.py`) - Serves the UI and broadcasts events
3. **Interactive UI** (`visualization.html`) - Beautiful D3.js graph with animations
4. **Agent Registry** - Automatically emits events when agents communicate

## Quick Start

### Step 1: Start the Visualization Server

```bash
python3 visualization_server.py
```

This starts the server on **http://localhost:8001**

### Step 2: Open the Visualization

Open your browser to:
```
http://localhost:8001
```

You should see:
- All registered agents as colored nodes in a circle
- Connection status: "Connected" (green dot)
- Stats showing 0 events (waiting for activity)

### Step 3: Run the Demo

In a **separate terminal**:

```bash
python3 demo_visualization.py
```

## What You'll See

### 🎨 Visual Effects

**Agent Nodes:**
- **Color-coded by type:**
  - 🟢 Snowflake Agents (green)
  - 🟠 Gemini Agents (orange)
  - 🔵 Merge Agents (cyan)
  - 🟣 Quality Agents (purple)
  - 🌸 Orchestration Agents (pink)

**Animated Flows:**
- **Green flowing particles** move from one agent to another
- **Glowing lines** connect agents during communication
- **Pulsing effect** on active agents

**Event Log:**
- 📤 Outgoing calls (agent → agent)
- ✅ Successful responses
- ❌ Errors (if any)
- Timestamps for each event

### 📊 Demo Flow

Watch as the agents communicate:

1. **Mapping Agent** → **Schema Reader Agent** (fetch schema for table 1)
2. **Mapping Agent** → **Schema Reader Agent** (fetch schema for table 2)
3. **Join Agent** → **Snowflake** (execute merge)
4. **Null Checker** → **Snowflake** (validate data)
5. **Duplicate Detector** → **Snowflake** (check duplicates)
6. **Stats Agent** → **Snowflake** (profile data)

All happening in **real-time** with beautiful animations!

## Advanced Usage

### Run Your Own Pipeline

Any agent code that uses the `AgentRegistry` will automatically broadcast events:

```python
from agents.gemini.mapping_agent import GeminiMappingAgent

mapping_agent = GeminiMappingAgent(agent_id="my_mapper")

# This will show up in the visualization!
result = await mapping_agent.propose_mappings(table1, table2)
```

### Monitor Production Pipelines

Keep the visualization server running and it will show **all agent activity** in real-time.

Perfect for:
- Debugging agent communication
- Monitoring production data pipelines
- Demo presentations (looks amazing!)

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Browser (http://localhost:8001)                │
│  ├─ visualization.html (D3.js graph)            │
│  └─ WebSocket connection                        │
└────────────────┬────────────────────────────────┘
                 │
                 │ WebSocket
                 ▼
┌─────────────────────────────────────────────────┐
│  visualization_server.py (FastAPI)              │
│  └─ Broadcasts events to all clients            │
└────────────────┬────────────────────────────────┘
                 │
                 │ Subscribe
                 ▼
┌─────────────────────────────────────────────────┐
│  core/event_bus.py (Event Bus)                  │
│  └─ Receives events from AgentRegistry          │
└────────────────┬────────────────────────────────┘
                 │
                 │ Emit events
                 ▼
┌─────────────────────────────────────────────────┐
│  core/agent_registry.py                         │
│  └─ Emits events when agents call each other    │
└─────────────────────────────────────────────────┘
```

## Troubleshooting

**"Connection failed"**
- Make sure `visualization_server.py` is running
- Check that port 8001 is not blocked

**"No agents showing"**
- Run `demo_visualization.py` to initialize agents
- Or run any test script that uses agents

**"No events"**
- Agents need to actually communicate for events to appear
- Run the demo script to trigger agent communication

## For Your EY Demo

**Say this:**
> "This shows our multi-agent architecture in action. Each node is an autonomous agent. Watch as the Mapping Agent autonomously discovers and calls the Schema Reader Agent—no manual orchestration required. The green flows represent real data and decisions moving through the system in real-time."

**Highlight:**
- ✅ Real-time monitoring
- ✅ Agent autonomy (A2A communication)
- ✅ Distributed architecture (cloud-ready)
- ✅ Production-ready observability

---

**This is the kind of visualization that wins hackathons!** 🏆
