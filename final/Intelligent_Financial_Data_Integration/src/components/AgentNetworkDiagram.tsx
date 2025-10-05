// src/components/AgentNetworkDiagram.tsx
import { useEffect, useState } from "react";
import { 
  Bot, 
  Network, 
  Database, 
  GitMerge, 
  ShieldAlert, 
  Sparkles,
  Activity,
  Shield,
  FileSearch,
  Zap,
  Brain,
  Lock,
  TrendingUp,
  CheckCircle2,
  FileText,
  Trash2,
  AlertCircle,
  BarChart3,
  Eye
} from "lucide-react";

interface Agent {
  id: string;
  name: string;
  icon: any;
  x: number;
  y: number;
  color: string;
  status: "active" | "idle" | "processing";
}

interface Connection {
  from: string;
  to: string;
  active: boolean;
}

interface AgentNetworkDiagramProps {
  currentStep?: string;
}

// Cute Robot SVG Component
const RobotIcon = ({ className, color }: { className?: string; color?: string }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 200 200" 
    fill="none"
    className={className}
  >
    {/* Antenna left */}
    <circle cx="60" cy="30" r="8" fill={color || "currentColor"}/>
    <line x1="60" y1="38" x2="60" y2="60" stroke={color || "currentColor"} strokeWidth="4"/>
    
    {/* Antenna right */}
    <circle cx="140" cy="30" r="8" fill={color || "currentColor"}/>
    <line x1="140" y1="38" x2="140" y2="60" stroke={color || "currentColor"} strokeWidth="4"/>
    
    {/* Head */}
    <rect x="50" y="60" width="100" height="60" rx="8" fill="none" stroke={color || "currentColor"} strokeWidth="6"/>
    
    {/* Eyes */}
    <circle cx="80" cy="85" r="8" fill={color || "currentColor"}/>
    <circle cx="120" cy="85" r="8" fill={color || "currentColor"}/>
    
    {/* Smile */}
    <path d="M 75 105 Q 100 115 125 105" stroke={color || "currentColor"} strokeWidth="5" fill="none" strokeLinecap="round"/>
    
    {/* Ears/Side panels */}
    <rect x="35" y="75" width="15" height="30" rx="4" fill="none" stroke={color || "currentColor"} strokeWidth="4"/>
    <rect x="150" y="75" width="15" height="30" rx="4" fill="none" stroke={color || "currentColor"} strokeWidth="4"/>
    
    {/* Body neck */}
    <rect x="85" y="120" width="30" height="15" fill="none" stroke={color || "currentColor"} strokeWidth="4"/>
    
    {/* Body */}
    <path d="M 60 135 Q 60 170 100 170 Q 140 170 140 135 Z" fill="none" stroke={color || "currentColor"} strokeWidth="6"/>
    
    {/* Body detail */}
    <line x1="150" y1="145" x2="155" y2="150" stroke={color || "currentColor"} strokeWidth="4" strokeLinecap="round"/>
    <line x1="150" y1="155" x2="155" y2="160" stroke={color || "currentColor"} strokeWidth="4" strokeLinecap="round"/>
  </svg>
);

export function AgentNetworkDiagram({ currentStep = "upload" }: AgentNetworkDiagramProps) {
  // Calculate positions for agents in a perfect circle
  const centerX = 50;
  const centerY = 50;
  const radius = 35; // Distance from center
  const totalAgents = 14; // Total agents in the circle
  const angleStep = (2 * Math.PI) / totalAgents;
  
  const getCircularPosition = (index: number) => {
    const angle = index * angleStep - Math.PI / 2; // Start from top (0°)
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  };

  const [agents, setAgents] = useState<Agent[]>([
    // Center - Master Orchestrator (hub)
    {
      id: "master",
      name: "Master Orchestrator",
      icon: Network,
      x: centerX,
      y: centerY,
      color: "from-purple-600 to-purple-800",
      status: "active",
    },
    // Circular arrangement - All agents evenly spaced
    {
      id: "schema_reader",
      name: "Schema Reader",
      icon: FileSearch,
      ...getCircularPosition(0),
      color: "from-blue-500 to-blue-700",
      status: "idle",
    },
    {
      id: "mapping",
      name: "Mapping Agent",
      icon: GitMerge,
      ...getCircularPosition(1),
      color: "from-cyan-500 to-cyan-700",
      status: "idle",
    },
    {
      id: "conflict_detector",
      name: "Conflict Detector",
      icon: ShieldAlert,
      ...getCircularPosition(2),
      color: "from-orange-500 to-orange-700",
      status: "idle",
    },
    {
      id: "sql_generator",
      name: "SQL Generator",
      icon: Database,
      ...getCircularPosition(3),
      color: "from-green-500 to-green-700",
      status: "idle",
    },
    {
      id: "ingestion",
      name: "Snowflake Ingestion",
      icon: Database,
      ...getCircularPosition(4),
      color: "from-blue-400 to-blue-600",
      status: "idle",
    },
    {
      id: "null_checker",
      name: "Null Checker",
      icon: AlertCircle,
      ...getCircularPosition(5),
      color: "from-red-500 to-red-700",
      status: "idle",
    },
    {
      id: "duplicate_detector",
      name: "Duplicate Detector",
      icon: Trash2,
      ...getCircularPosition(6),
      color: "from-amber-500 to-amber-700",
      status: "idle",
    },
    {
      id: "dedupe",
      name: "Dedupe Agent",
      icon: Trash2,
      ...getCircularPosition(7),
      color: "from-yellow-500 to-yellow-700",
      status: "idle",
    },
    {
      id: "join",
      name: "Join Agent",
      icon: GitMerge,
      ...getCircularPosition(8),
      color: "from-indigo-500 to-indigo-700",
      status: "idle",
    },
    {
      id: "validation_monitor",
      name: "Validation Monitor",
      icon: Eye,
      ...getCircularPosition(9),
      color: "from-teal-500 to-teal-700",
      status: "idle",
    },
    {
      id: "stats",
      name: "Stats Agent",
      icon: BarChart3,
      ...getCircularPosition(10),
      color: "from-violet-500 to-violet-700",
      status: "idle",
    },
    {
      id: "quality",
      name: "Quality Agent",
      icon: CheckCircle2,
      ...getCircularPosition(11),
      color: "from-pink-500 to-pink-700",
      status: "idle",
    },
    {
      id: "conversational",
      name: "Chat Agent",
      icon: Bot,
      ...getCircularPosition(12),
      color: "from-purple-400 to-purple-600",
      status: "idle",
    },
    {
      id: "schema",
      name: "Schema Agent",
      icon: Database,
      ...getCircularPosition(13),
      color: "from-slate-500 to-slate-700",
      status: "idle",
    },
  ]);

  const [connections, setConnections] = useState<Connection[]>([
    // Master Orchestrator can call ALL agents (hub and spoke model)
    { from: "master", to: "ingestion", active: false },
    { from: "master", to: "schema_reader", active: false },
    { from: "master", to: "mapping", active: false },
    { from: "master", to: "conflict_detector", active: false },
    { from: "master", to: "sql_generator", active: false },
    { from: "master", to: "join", active: false },
    { from: "master", to: "quality", active: false },
    { from: "master", to: "conversational", active: false },
    { from: "master", to: "validation_monitor", active: false },
    
    // Gemini agents collaborate
    { from: "mapping", to: "schema_reader", active: false },
    { from: "conflict_detector", to: "schema_reader", active: false },
    { from: "sql_generator", to: "schema_reader", active: false },
    { from: "sql_generator", to: "mapping", active: false },
    
    // Data ingestion flow
    { from: "ingestion", to: "schema_reader", active: false },
    { from: "ingestion", to: "schema", active: false },
    
    // Quality checks flow
    { from: "null_checker", to: "quality", active: false },
    { from: "duplicate_detector", to: "quality", active: false },
    { from: "stats", to: "quality", active: false },
    { from: "validation_monitor", to: "quality", active: false },
    
    // Merge operations
    { from: "join", to: "sql_generator", active: false },
    { from: "dedupe", to: "join", active: false },
    { from: "duplicate_detector", to: "dedupe", active: false },
    
    // Final validation
    { from: "quality", to: "join", active: false },
    { from: "validation_monitor", to: "null_checker", active: false },
    { from: "validation_monitor", to: "duplicate_detector", active: false },
  ]);

  const [activeConnection, setActiveConnection] = useState(0);

  // Update agent status based on current step (matching actual pipeline from AGENT_TOOLS_MATRIX)
  useEffect(() => {
    const updatedAgents = [...agents];
    const updatedConnections = [...connections];
    
    // Reset all agents to idle
    updatedAgents.forEach(agent => {
      if (agent.id !== "master") {
        agent.status = "idle";
      }
    });
    
    // Reset all connections
    updatedConnections.forEach(conn => conn.active = false);
    
    switch (currentStep) {
      case "upload":
        // Step 1: Data Ingestion & Validation
        updatedAgents.forEach(agent => {
          if (["ingestion", "conversational", "schema_reader", "schema", "validation_monitor"].includes(agent.id)) {
            agent.status = "active";
          }
        });
        updatedConnections.filter(c => 
          (c.from === "master" && c.to === "ingestion") ||
          (c.from === "master" && c.to === "conversational") ||
          (c.from === "ingestion" && c.to === "schema_reader") ||
          (c.from === "ingestion" && c.to === "schema") ||
          (c.from === "master" && c.to === "validation_monitor")
        ).forEach(c => c.active = true);
        break;
        
      case "mapping":
        // Step 2: Schema Analysis, Mapping & Quality Checks
        updatedAgents.forEach(agent => {
          if (["schema_reader", "mapping", "validation_monitor", "null_checker", "duplicate_detector", "quality", "stats"].includes(agent.id)) {
            agent.status = "active";
          }
        });
        updatedConnections.filter(c => 
          (c.from === "master" && c.to === "schema_reader") ||
          (c.from === "master" && c.to === "mapping") ||
          (c.from === "mapping" && c.to === "schema_reader") ||
          (c.from === "validation_monitor" && c.to === "null_checker") ||
          (c.from === "validation_monitor" && c.to === "duplicate_detector") ||
          (c.from === "null_checker" && c.to === "quality") ||
          (c.from === "stats" && c.to === "quality")
        ).forEach(c => c.active = true);
        break;
        
      case "conflicts":
        // Step 3: Conflict Detection & Deduplication
        updatedAgents.forEach(agent => {
          if (["conflict_detector", "schema_reader", "duplicate_detector", "dedupe", "quality", "validation_monitor"].includes(agent.id)) {
            agent.status = "active";
          }
        });
        updatedConnections.filter(c => 
          (c.from === "master" && c.to === "conflict_detector") ||
          (c.from === "conflict_detector" && c.to === "schema_reader") ||
          (c.from === "duplicate_detector" && c.to === "quality") ||
          (c.from === "duplicate_detector" && c.to === "dedupe") ||
          (c.from === "validation_monitor" && c.to === "quality")
        ).forEach(c => c.active = true);
        break;
        
      case "results":
        // Step 4: SQL Generation, Merge, Join & Final Quality
        updatedAgents.forEach(agent => {
          if (["sql_generator", "schema_reader", "mapping", "join", "dedupe", "quality", "stats"].includes(agent.id)) {
            agent.status = "active";
          }
        });
        updatedConnections.filter(c => 
          (c.from === "master" && c.to === "sql_generator") ||
          (c.from === "sql_generator" && c.to === "schema_reader") ||
          (c.from === "sql_generator" && c.to === "mapping") ||
          (c.from === "master" && c.to === "join") ||
          (c.from === "join" && c.to === "sql_generator") ||
          (c.from === "dedupe" && c.to === "join") ||
          (c.from === "master" && c.to === "quality") ||
          (c.from === "quality" && c.to === "join") ||
          (c.from === "stats" && c.to === "quality")
        ).forEach(c => c.active = true);
        break;
    }
    
    setConnections(updatedConnections);
    setAgents(updatedAgents);
  }, [currentStep]);

  // Animate connections
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveConnection((prev) => (prev + 1) % connections.length);
    }, 1500);
    return () => clearInterval(interval);
  }, [connections.length]);

  // Calculate curved path between two agents for more flowy appearance
  const getConnectionPath = (from: Agent, to: Agent) => {
    const midX = (from.x + to.x) / 2;
    const midY = (from.y + to.y) / 2;
    // Create a smooth curve through the midpoint
    return `M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`;
  };

  const getAgent = (id: string) => agents.find((a) => a.id === id);

  return (
    <div className="h-full w-full">
      {/* SVG Network Diagram */}
      <div className="relative w-full h-full flex items-center justify-center">
        <svg
          viewBox="0 0 100 100"
          className="w-full h-full"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Background geometric circle to show structure */}
          <circle
            cx="50"
            cy="50"
            r="35"
            fill="none"
            stroke="#d1d5db"
            strokeWidth="0.4"
            strokeDasharray="3,3"
            opacity="0.5"
          />
          
          {/* Center point indicator */}
          <circle
            cx="50"
            cy="50"
            r="1.5"
            fill="#9ca3af"
            opacity="0.4"
          />
          
          {/* Render connections first (so they appear behind nodes) */}
          {connections.map((conn, idx) => {
            const fromAgent = getAgent(conn.from);
            const toAgent = getAgent(conn.to);
            if (!fromAgent || !toAgent) return null;

            const isAnimating = activeConnection === idx && conn.active;

            return (
              <g key={`${conn.from}-${conn.to}`}>
                {/* Curved connection line */}
                <path
                  d={getConnectionPath(fromAgent, toAgent)}
                  stroke={conn.active ? "url(#gradient-active)" : "url(#gradient-inactive)"}
                  strokeWidth={conn.active ? "0.5" : "0.25"}
                  opacity={conn.active ? "0.8" : "0.3"}
                  fill="none"
                  className="transition-all duration-500"
                />
                
                {/* Animated particle flowing along the curve */}
                {isAnimating && (
                  <circle r="1" fill="#22c55e" className="drop-shadow-lg">
                    <animateMotion
                      dur="1.5s"
                      repeatCount="1"
                      path={getConnectionPath(fromAgent, toAgent)}
                    />
                  </circle>
                )}
              </g>
            );
          })}

          {/* Gradients for connections */}
          <defs>
            <linearGradient id="gradient-active" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="1" />
              <stop offset="100%" stopColor="#16a34a" stopOpacity="1" />
            </linearGradient>
            <linearGradient id="gradient-inactive" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#6b7280" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#4b5563" stopOpacity="0.3" />
            </linearGradient>
          </defs>
        </svg>

        {/* Agent labels positioned absolutely with cute robot icons */}
        {agents.map((agent) => {
          const isActive = connections.some(
            (c) => (c.from === agent.id || c.to === agent.id) && c.active
          );

          // White by default, green when active
          const robotColor = isActive ? "#22c55e" : "#ffffff";
          const textColor = isActive ? "text-green-500" : "text-white";

          return (
            <div
              key={`label-${agent.id}`}
              className="absolute flex flex-col items-center group"
              style={{
                left: `${agent.x}%`,
                top: `${agent.y}%`,
                transform: "translate(-50%, -50%)",
              }}
            >
              {/* Robot Icon - Simple, no background */}
              <div className="relative">
                <RobotIcon 
                  className={`w-12 h-12 transition-all duration-300 ${
                    isActive ? "scale-125" : "scale-100 group-hover:scale-110"
                  }`}
                  color={robotColor}
                />
              </div>

              {/* Agent name label */}
              <div
                className={`mt-1.5 text-[10px] font-bold text-center transition-all duration-300 whitespace-nowrap ${textColor}`}
              >
                {agent.name}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
