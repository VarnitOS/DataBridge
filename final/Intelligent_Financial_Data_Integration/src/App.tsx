// src/App.tsx
import { useState, useEffect, useRef } from "react";
import { ParticleCard, GlobalSpotlight } from "./components/Magic/MagicBento";
import LiquidEther from "./components/backgrounds/LiquidEther";
import { MainNavigation } from "./components/MainNavigation";
import { FileUploadZone } from "./components/FileUploadZone";
import { VisualSchemaMappingView } from "./components/VisualSchemaMappingView";
import { MonitoringDashboard } from "./components/MonitoringDashboard";
import { DataPreviewTable } from "./components/DataPreviewTable";
import { ConflictResolutionPanel } from "./components/ConflictResolutionPanel";
import { ProjectManagementPanel } from "./components/ProjectManagementPanel";
import { CollaborationPanel } from "./components/CollaborationPanel";
import { UserProfilePanel } from "./components/UserProfilePanel";
import { ReportGenerator } from "./components/ReportGenerator";
import { Button } from "./components/ui/button";
import { Card } from "./components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Input } from "./components/ui/input";
import { ScrollArea } from "./components/ui/scroll-area";
import { parseCSV, getFieldNames, generateMockBankData } from "./utils/csvParser";
import { generateAIMappings, mergeDatasets } from "./utils/aiMappingSimulator";
import { mockConflicts } from "./utils/mockData";
import { Sparkles, Info, AlertTriangle, Bot, Send, Activity, Zap, Loader2 } from "lucide-react";
import { Progress } from "./components/ui/progress";
import { Badge } from "./components/ui/badge";
import { CustomTab } from "./components/AddTabDialog";
import { AgentNetworkDiagram } from "./components/AgentNetworkDiagram";

type ProcessingStatus = "idle" | "processing" | "success" | "error";
type Step = "upload" | "mapping" | "conflicts" | "results";

interface FieldMapping {
  sourceField: string;
  targetField: string;
  confidence: number;
  status: "confirmed" | "suggested" | "manual";
}

export default function App() {
  const [currentView, setCurrentView] = useState<string>("integration");
  const [customTabs, setCustomTabs] = useState<CustomTab[]>([]);

  const handleUpdateTabLabel = (tabId: string, newLabel: string) => {
    setCustomTabs((prev) =>
      prev.map((tab) => (tab.id === tabId ? { ...tab, label: newLabel } : tab))
    );
  };

  const handleAddTab = (newTab: CustomTab) => {
    setCustomTabs((prev) => [...prev, newTab]);
    setCurrentView(newTab.id);
  };

  const handleCloseTab = (tabId: string) => {
    setCustomTabs((prev) => prev.filter((tab) => tab.id !== tabId));
    if (currentView === tabId) setCurrentView("integration");
  };

  // Add new financial institution
  const addFinancialInstitution = () => {
    const newId = `fi-${financialInstitutions.length + 1}`;
    const newLabel = `Financial Institution ${financialInstitutions.length + 1} Dataset`;
    setFinancialInstitutions((prev) => [
      ...prev,
      { id: newId, label: newLabel, file: null, data: [] },
    ]);
  };

  // Update file for a specific financial institution
  const updateFinancialInstitutionFile = (id: string, file: File | null) => {
    setFinancialInstitutions((prev) =>
      prev.map((fi) => (fi.id === id ? { ...fi, file } : fi))
    );
  };

  // Remove a financial institution (except the first two)
  const removeFinancialInstitution = (id: string) => {
    if (financialInstitutions.length > 2) {
      setFinancialInstitutions((prev) => prev.filter((fi) => fi.id !== id));
    }
  };

  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [sourceData, setSourceData] = useState<Record<string, any>[]>([]);
  const [targetData, setTargetData] = useState<Record<string, any>[]>([]);

  // Multiple financial institution datasets
  const [financialInstitutions, setFinancialInstitutions] = useState<
    Array<{ id: string; label: string; file: File | null; data: Record<string, any>[] }>
  >([
    { id: "fi-1", label: "Financial Institution 1 Dataset", file: null, data: [] },
    { id: "fi-2", label: "Financial Institution 2 Dataset", file: null, data: [] },
  ]);
  const [mappings, setMappings] = useState<FieldMapping[]>([]);
  const [mergedData, setMergedData] = useState<Record<string, any>[]>([]);
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [processingProgress, setProcessingProgress] = useState(0);
  const [activeAgents, setActiveAgents] = useState<Set<string>>(new Set());
  const [currentStep, setCurrentStep] = useState<Step>("upload");
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [conflicts] = useState(mockConflicts);
  const [showProfile, setShowProfile] = useState(false);

  // Chat state
  const [chatMessages, setChatMessages] = useState<
    Array<{ id: string; role: "user" | "assistant"; content: string; timestamp: Date }>
  >([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your EY DataFusion AI assistant powered by Gemini. I can help you understand schema mappings, resolve conflicts, and suggest data normalization strategies. What would you like to know?",
      timestamp: new Date(),
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Step 5: global spotlight wrapper
  const bentoRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom (only if near bottom)
  useEffect(() => {
    const el = chatScrollRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
    if (isNearBottom) el.scrollTop = el.scrollHeight;
  }, [chatMessages]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDarkMode);
  }, [isDarkMode]);

  // Function to update active agents based on chatbot activity
  const updateActiveAgents = (agentIds: string[]) => {
    setActiveAgents(new Set(agentIds));
    
    // Auto-clear after 3 seconds
    setTimeout(() => {
      setActiveAgents(new Set());
    }, 3000);
  };

  // Simulate agent activity when chat messages arrive
  useEffect(() => {
    if (isChatLoading) {
      // Simulate sequential agent activation during processing
      const sequence = [
        { agents: ['system_schema', 'system_monitor'], delay: 500 },
        { agents: ['system_mapping'], delay: 2000 },
        { agents: ['system_join'], delay: 1500 },
        { agents: ['system_monitor', 'system_stats'], delay: 1000 },
      ];

      let timeouts: NodeJS.Timeout[] = [];
      let cumulativeDelay = 0;

      sequence.forEach(({ agents, delay }) => {
        const timeout = setTimeout(() => {
          updateActiveAgents(agents);
        }, cumulativeDelay);
        timeouts.push(timeout);
        cumulativeDelay += delay;
      });

      return () => {
        timeouts.forEach(clearTimeout);
      };
    }
  }, [isChatLoading]);

  const handleAnalyze = async () => {
    const uploadedFiles = financialInstitutions.filter((fi) => fi.file);
    if (uploadedFiles.length < 2) return;

    setStatus("processing");
    setCurrentStep("mapping");
    setProcessingProgress(0);

    const steps = [
      { progress: 20, delay: 500 },
      { progress: 40, delay: 800 },
      { progress: 60, delay: 600 },
      { progress: 80, delay: 700 },
      { progress: 100, delay: 500 },
    ];

    try {
      // Parse all uploaded files
      const parsedData = await Promise.all(
        uploadedFiles.map(async (fi) => ({
          id: fi.id,
          label: fi.label,
          data: await parseCSV(fi.file!),
        }))
      );

      for (const step of steps) {
        await new Promise((r) => setTimeout(r, step.delay));
        setProcessingProgress(step.progress);
      }

      // Update FIs with parsed data
      setFinancialInstitutions((prev) =>
        prev.map((fi) => {
          const parsed = parsedData.find((p) => p.id === fi.id);
          return parsed ? { ...fi, data: parsed.data } : fi;
        })
      );

      // For backward compatibility, set source and target from first two files
      if (parsedData.length >= 2) {
        setSourceData(parsedData[0].data);
        setTargetData(parsedData[1].data);
      }

      // Generate mappings
      const sourceFields = getFieldNames(parsedData[0].data);
      const targetFields = getFieldNames(parsedData[1].data);
      const aiMappings = generateAIMappings(sourceFields, targetFields);

      setMappings(aiMappings);
      setStatus("success");
    } catch (error) {
      setStatus("error");
      console.error("Processing error:", error);
    }
  };

  const handleContinueToConflicts = () => setCurrentStep("conflicts");

  const handleMerge = () => {
    setStatus("processing");
    setProcessingProgress(0);
    setTimeout(() => {
      const merged = mergeDatasets(sourceData, targetData, mappings);
      setMergedData(merged);
      setCurrentStep("results");
      setStatus("success");
      setProcessingProgress(100);
    }, 2000);
  };

  const handleUseMockData = () => {
    const mockSource = generateMockBankData("source");
    const mockTarget = generateMockBankData("target");
    setSourceData(mockSource);
    setTargetData(mockTarget);
    setSourceFile(new File([], "bank_a_data.csv"));
    setTargetFile(new File([], "bank_b_data.csv"));
    setCurrentStep("mapping");
    setStatus("processing");
    setTimeout(() => {
      const sourceFields = getFieldNames(mockSource);
      const targetFields = getFieldNames(mockTarget);
      const aiMappings = generateAIMappings(sourceFields, targetFields);
      setMappings(aiMappings);
      setStatus("success");
    }, 1500);
  };

  const handleStartNew = () => {
    setCurrentStep("upload");
    setSourceFile(null);
    setTargetFile(null);
    setSourceData([]);
    setTargetData([]);
    setMergedData([]);
    setMappings([]);
    setStatus("idle");
    setCurrentView("integration");
  };

  // Handle chat send
  const handleChatSend = async () => {
    if (!chatInput.trim() || isChatLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: "user" as const,
      content: chatInput,
      timestamp: new Date(),
    };

    setChatMessages((prev) => [...prev, userMessage]);
    setChatInput("");
    setIsChatLoading(true);

    try {
      const response = await fetch("http://localhost:8002/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: chatInput,
          session_id: `frontend_session_${Date.now()}`,
        }),
      });

      if (!response.ok) throw new Error("Chat request failed");

      const data = await response.json();
      const aiMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant" as const,
        content: data.answer || data.message || "No response from chatbot",
        timestamp: new Date(),
      };

      setChatMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant" as const,
        content:
          "I apologize, but I'm experiencing technical difficulties. Please ensure the chatbot server is running on localhost:8002.",
        timestamp: new Date(),
      };
      setChatMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // ---- TypeScript-safe helper for the progress pills (fix for ts(2367))
  const doneSteps: readonly Step[] = ["mapping", "conflicts", "results"];
  const isDone = (s: Step) => (doneSteps as readonly Step[]).includes(s);

  return (
    <>
      {/* Global animated background */}
      <div style={{ position: "fixed", inset: 0, zIndex: -1, pointerEvents: "none" }}>
        <LiquidEther colors={["#5227FF", "#FF9FFC", "#B19EEF"]} resolution={0.6} autoDemo />
      </div>

      {/* Step 5: one global spotlight watching everything inside bentoRef */}
      <GlobalSpotlight gridRef={bentoRef} spotlightRadius={300} glowColor="132, 0, 255" />

      {/* Everything below is inside the spotlight's scope */}
      <div ref={bentoRef} className="bento-section">
        {showProfile ? (
          /* ========= PROFILE VIEW ========= */
          <div
            className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"
            style={{ position: "relative" }}
          >
            {/* NAV with solid white background and backdrop blur */}
            <div className="sticky top-0 z-[100] bg-white/95 backdrop-blur-md shadow-md border-b border-gray-200">
              <MainNavigation
                currentView="profile"
                onViewChange={(view) => {
                  setShowProfile(false);
                  setCurrentView(view);
                }}
                onProfileClick={() => setShowProfile(true)}
                customTabs={customTabs}
                onAddTab={handleAddTab}
                onUpdateTabLabel={handleUpdateTabLabel}
              />
            </div>

            <div className="container mx-auto px-6 py-8 max-w-4xl">
              <div className="space-y-6">
                <div className="text-center mb-8">
                  <h1 className="text-3xl font-bold text-white mb-2">User Profile</h1>
                  <p className="text-white/60">Manage your account settings and preferences</p>
                </div>

                <ParticleCard
                  className="card card--border-glow"
                  glowColor="132, 0, 255"
                  enableTilt
                  enableMagnetism
                  particleCount={10}
                >
                  <Card className="p-6">
                    <UserProfilePanel
                      onThemeToggle={() => setIsDarkMode(!isDarkMode)}
                      isDarkMode={isDarkMode}
                    />
                  </Card>
                </ParticleCard>
              </div>
            </div>
          </div>
        ) : (
          /* ======== OTHER VIEWS (default) ======== */
          <div
            className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"
            style={{ position: "relative" }}
          >
            {/* NAV with solid white background and backdrop blur */}
            <div className="sticky top-0 z-[100] bg-white/95 backdrop-blur-md shadow-md border-b border-gray-200">
              <MainNavigation
                currentView={currentView}
                onViewChange={setCurrentView}
                onProfileClick={() => setShowProfile(true)}
                onUpdateTabLabel={handleUpdateTabLabel}
                customTabs={customTabs}
                onAddTab={handleAddTab}
                onCloseTab={handleCloseTab}
              />
            </div>

            <div className="container mx-auto px-6 py-8">
              {/* Projects */}
              {currentView === "projects" && (
                <ProjectManagementPanel
                  onSelectProject={(id) => {
                    console.log("Selected project:", id);
                    setCurrentView("integration");
                  }}
                  onCreateNew={handleStartNew}
                />
              )}

              {/* Collaboration */}
              {currentView === "collaboration" && (
                <div className="max-w-4xl mx-auto">
                  <CollaborationPanel />
                </div>
              )}

              {/* Reports */}
              {currentView === "reports" && (
                <div className="max-w-4xl mx-auto">
                  <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" particleCount={8} enableTilt>
                    <Card className="p-6">
                      <ReportGenerator
                        projectName="Chase & Wells Fargo Merger"
                        recordsProcessed={mergedData.length || 2450000}
                        conflictsResolved={conflicts.length}
                        dataQualityScore={96}
                        mappings={mappings}
                      />
                    </Card>
                  </ParticleCard>
                </div>
              )}

              {/* Custom Tab Content */}
              {currentView.startsWith("custom-") && (
                <div className="max-w-4xl mx-auto">
                  <div className="space-y-6">
                    {/* Title Section */}
                    <div className="text-center">
                      <input
                        type="text"
                        placeholder="Add Title"
                        className="text-3xl font-bold text-white bg-transparent border-none outline-none text-center w-full placeholder-white/60"
                        style={{ fontFamily: "inherit", fontSize: "2rem", fontWeight: "bold" }}
                        onChange={(e) => {
                          const newTitle = e.target.value || "New Tab";
                          handleUpdateTabLabel(currentView, newTitle);
                        }}
                        onBlur={(e) => {
                          if (!e.target.value.trim()) {
                            e.target.value = "New Tab";
                            handleUpdateTabLabel(currentView, "New Tab");
                          }
                        }}
                      />
                    </div>

                    {/* Comment Box */}
                    <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700/50 p-4">
                      <textarea
                        placeholder="Add a comment..."
                        className="w-full bg-transparent text-white placeholder-gray-400 resize-none outline-none min-h-[120px] text-lg"
                        style={{ fontFamily: "inherit", lineHeight: "1.5" }}
                      />
                    </div>

                    {/* Additional Content Area */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-700/30">
                        <h3 className="text-white font-medium mb-2">Notes</h3>
                        <textarea
                          placeholder="Add your notes here..."
                          className="w-full bg-transparent text-white placeholder-gray-400 resize-none outline-none min-h-[100px]"
                        />
                      </div>
                      <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-700/30">
                        <h3 className="text-white font-medium mb-2">Tasks</h3>
                        <textarea
                          placeholder="Add your tasks here..."
                          className="w-full bg-transparent text-white placeholder-gray-400 resize-none outline-none min-h-[100px]"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Agent Network View */}
              {currentView === "agents" && (
                <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 -m-8 p-8">
                  <div className="max-w-7xl mx-auto">
                    {/* Enhanced Header */}
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-3 mb-4 px-4 py-2 bg-purple-500/20 backdrop-blur-sm rounded-full border border-purple-400/30">
                          <Activity className="w-5 h-5 text-purple-400 animate-pulse" />
                          <span className="text-sm font-semibold text-purple-300 tracking-wider uppercase">
                            Live System Monitor
                          </span>
                        </div>
                        <h1 className="text-6xl font-black text-white mb-4 tracking-tight">
                          <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400 drop-shadow-lg">
                            Multi-Agent Network
                          </span>
                        </h1>
                        <p className="text-white/80 text-xl font-light leading-relaxed">
                          Real-time visualization of AI agents communicating and collaborating
                        </p>
                        <div className="mt-6 flex items-center justify-center gap-8 text-sm">
                          <div className="flex items-center gap-2 text-white/60">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                            <span className="font-medium">System Active</span>
                          </div>
                          <div className="flex items-center gap-2 text-white/60">
                            <span className="font-medium">For this merge operation</span>
                          </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      {/* Main Network Visualization */}
                      <div className="lg:col-span-2">
                        <ParticleCard 
                          className="card card--border-glow h-[700px]" 
                          glowColor="168, 85, 247" 
                          particleCount={20} 
                          enableTilt
                          enableMagnetism
                        >
                          <AgentNetworkDiagram currentStep={currentStep} />
                        </ParticleCard>
                      </div>

                      {/* Agent Info Panel */}
                      <div className="space-y-6">
                        <div className="space-y-4">
                          <div className="p-4 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20">
                            <div className="flex items-center gap-3 mb-3">
                              <Activity className="w-5 h-5 text-green-400" />
                              <span className="text-white font-bold text-sm">Running Instances</span>
                            </div>
                            <div className="text-4xl font-black text-white mb-2">3</div>
                            <div className="flex items-center gap-2">
                              <Zap className="w-4 h-4 text-yellow-400" />
                              <span className="text-sm text-white/80">Compute Required: <span className="text-green-400 font-semibold">Low</span></span>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between p-3 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20">
                            <span className="text-white/90 font-semibold text-sm">Total Agents</span>
                            <span className="text-3xl font-black text-green-400 drop-shadow-lg">15</span>
                          </div>
                          <div className="flex items-center justify-between p-3 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20">
                            <span className="text-white/90 font-semibold text-sm">A2A Connections</span>
                            <span className="text-3xl font-black text-blue-400 drop-shadow-lg">26</span>
                          </div>
                        </div>

                        <ParticleCard className="card card--border-glow" glowColor="34, 197, 94" particleCount={8}>
                          <Card className="p-6 bg-gradient-to-br from-green-500/20 to-emerald-500/20 backdrop-blur-xl border-2 border-white/20">
                            <div className="flex items-center gap-3 mb-6">
                              <div className="w-1.5 h-8 bg-gradient-to-b from-green-400 to-emerald-500 rounded-full" />
                              <h3 className="text-2xl font-black text-white tracking-tight">Recent Activity</h3>
                            </div>
                            <div className="space-y-3">
                              <div className="flex items-start gap-3 p-3 bg-white/10 backdrop-blur-sm rounded-lg border-l-4 border-green-500 hover:bg-white/20 transition-all">
                                <div className="w-2 h-2 bg-green-400 rounded-full mt-1.5 animate-pulse shadow-lg" />
                                <div className="flex-1">
                                  <p className="text-white font-semibold text-sm">Master Orchestrator active</p>
                                  <p className="text-white/60 text-xs mt-1">Coordinating pipeline</p>
                                </div>
                              </div>
                              <div className="flex items-start gap-3 p-3 bg-white/10 backdrop-blur-sm rounded-lg border-l-4 border-blue-500 hover:bg-white/20 transition-all">
                                <div className="w-2 h-2 bg-blue-400 rounded-full mt-1.5 animate-pulse shadow-lg" />
                                <div className="flex-1">
                                  <p className="text-white font-semibold text-sm">Mapping Agent → Schema Reader</p>
                                  <p className="text-white/60 text-xs mt-1">A2A communication active</p>
                                </div>
                              </div>
                              <div className="flex items-start gap-3 p-3 bg-white/10 backdrop-blur-sm rounded-lg border-l-4 border-purple-500 hover:bg-white/20 transition-all">
                                <div className="w-2 h-2 bg-purple-400 rounded-full mt-1.5 animate-pulse shadow-lg" />
                                <div className="flex-1">
                                  <p className="text-white font-semibold text-sm">Gemini analyzing schemas</p>
                                  <p className="text-white/60 text-xs mt-1">AI-powered mapping</p>
                                </div>
                              </div>
                            </div>
                          </Card>
                        </ParticleCard>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Integration */}
              {currentView === "integration" && (
                <div className="relative">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Main column - AI Chatbot */}
                  <div className="lg:col-span-2 space-y-6">
                    {/* Step 1 - Embedded Chatbot (NO CARD) */}
                    {currentStep === "upload" && (
                      <div className="mt-16 h-[calc(100vh-12rem)] flex flex-col">
                        {/* Chat header */}
                        <div className="p-4 border-b bg-gradient-to-r from-primary/5 to-primary/10 flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-gradient-to-br from-primary to-primary/80 rounded-lg shadow-lg">
                              <Bot className="w-5 h-5 text-primary-foreground animate-pulse" />
                            </div>
                            <div>
                              <h3 className="font-semibold text-foreground text-xl">AI Assistant</h3>
                              <p className="text-muted-foreground text-sm flex items-center gap-1">
                                <Sparkles className="w-3 h-3" />
                                Powered by Gemini
                              </p>
                            </div>
                          </div>
                          <Badge variant="outline" className="gap-2">
                            <Bot className="w-4 h-4" />
                            Online
                          </Badge>
                        </div>

                        {/* Scrollable chat body */}
                        <div
                          ref={chatScrollRef}
                          className="flex-1 overflow-y-auto p-4"
                          style={{ WebkitOverflowScrolling: "touch" }}
                        >
                          <div className="space-y-4">
                            {chatMessages.map((message) => (
                              <div
                                key={message.id}
                                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                              >
                                <div
                                  className={`max-w-[85%] rounded-lg p-4 ${
                                    message.role === "user"
                                      ? "bg-primary text-primary-foreground"
                                      : "bg-muted"
                                  }`}
                                >
                                  <p className="whitespace-pre-wrap">{message.content}</p>
                                  {message.role === "assistant" && (
                                    <div className="mt-2 pt-2 border-t border-border/50">
                                      <div className="flex flex-wrap gap-1">
                                        <Badge variant="outline" className="text-xs">
                                          <Sparkles className="w-3 h-3 mr-1" />
                                          Gemini AI
                                        </Badge>
                                        <Badge variant="outline" className="text-xs">
                                          <Info className="w-3 h-3 mr-1" />
                                          EY DataFusion
                                        </Badge>
                                      </div>
                                    </div>
                                  )}
                                  <p className="text-xs text-muted-foreground mt-2">
                                    {message.timestamp.toLocaleTimeString()}
                                  </p>
                                </div>
                              </div>
                            ))}
                            {isChatLoading && (
                              <div className="flex justify-start">
                                <div className="max-w-[85%] rounded-lg p-4 bg-muted">
                                  <p className="text-muted-foreground">Gemini is thinking...</p>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Footer input */}
                        <div className="border-t p-4">
                          <div className="flex gap-2">
                            <Input
                              placeholder="Ask about mappings, conflicts, or data quality..."
                              className="flex-1"
                              value={chatInput}
                              onChange={(e) => setChatInput(e.target.value)}
                              onKeyDown={(e) => e.key === "Enter" && handleChatSend()}
                              disabled={isChatLoading}
                            />
                            <Button
                              size="sm"
                              onClick={handleChatSend}
                              disabled={isChatLoading || !chatInput.trim()}
                            >
                              <Send className="w-4 h-4" />
                            </Button>
                          </div>
                          <p className="text-muted-foreground mt-2 text-center text-sm">
                            Natural language queries supported • Powered by Gemini AI
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Mapping header */}
                    {currentStep === "mapping" && mappings.length > 0 && (
                      <div className="space-y-6">
                        <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" particleCount={8} enableTilt>
                          <Card className="p-6">
                            <div className="flex items-center justify-between mb-4">
                              <div>
                                <h2 className="mb-2">Step 2: Review AI-Generated Mappings</h2>
                                <p className="text-muted-foreground">Visual schema mapping with AI confidence scores</p>
                              </div>
                              <Badge variant="outline" className="gap-2">
                                <Sparkles className="w-4 h-4" />
                                Gemini AI
                              </Badge>
                            </div>
                          </Card>
                        </ParticleCard>

                        <VisualSchemaMappingView
                          mappings={mappings}
                          sourceFields={getFieldNames(sourceData)}
                          targetFields={getFieldNames(targetData)}
                          onMappingChange={setMappings}
                          onConfirm={handleContinueToConflicts}
                        />

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <DataPreviewTable title="Bank A Preview" data={sourceData} variant="source" />
                          <DataPreviewTable title="Bank B Preview" data={targetData} variant="target" />
                        </div>
                      </div>
                    )}

                    {/* Conflicts */}
                    {currentStep === "conflicts" && (
                      <div className="space-y-6">
                        <Alert>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>
                            Review and resolve data conflicts before finalizing the merge
                          </AlertDescription>
                        </Alert>

                        <ConflictResolutionPanel
                          conflicts={conflicts}
                          onResolve={(id, resolution) => console.log("Resolved:", id, resolution)}
                          onResolveAll={handleMerge}
                        />

                        <div className="flex gap-3">
                          <Button variant="outline" onClick={() => setCurrentStep("mapping")} className="flex-1">
                            Back to Mappings
                          </Button>
                          <Button onClick={handleMerge} className="flex-1">
                            <Sparkles className="w-4 h-4 mr-2" />
                            Proceed with Merge
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Results */}
                    {currentStep === "results" && mergedData.length > 0 && (
                      <div className="space-y-6">
                        <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" particleCount={8}>
                          <Card className="p-6 bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20">
                            <h2 className="mb-2">Integration Complete!</h2>
                            <p className="text-muted-foreground">
                              Successfully merged {mergedData.length} records from both banking systems with {conflicts.length} conflicts resolved.
                            </p>
                          </Card>
                        </ParticleCard>

                        <MonitoringDashboard
                          recordsProcessed={mergedData.length}
                          totalRecords={mergedData.length}
                          processingTime="2.4s"
                          dataQualityScore={96}
                        />

                        <Tabs defaultValue="merged" className="w-full">
                          <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="merged">Merged Data</TabsTrigger>
                            <TabsTrigger value="source">Bank A</TabsTrigger>
                            <TabsTrigger value="target">Bank B</TabsTrigger>
                          </TabsList>
                          <TabsContent value="merged" className="mt-6">
                            <DataPreviewTable title="Unified Dataset" data={mergedData} variant="merged" />
                          </TabsContent>
                          <TabsContent value="source" className="mt-6">
                            <DataPreviewTable title="Bank A Original Data" data={sourceData} variant="source" />
                          </TabsContent>
                          <TabsContent value="target" className="mt-6">
                            <DataPreviewTable title="Bank B Original Data" data={targetData} variant="target" />
                          </TabsContent>
                        </Tabs>

                        <div className="grid grid-cols-2 gap-3">
                          <Button variant="outline" onClick={() => setCurrentView("reports")}>
                            Generate Report
                          </Button>
                          <Button variant="outline" onClick={handleStartNew}>
                            Start New Integration
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Sidebar - Upload Section & Agent Network */}
                  <div className="space-y-6">
                    {/* Upload Panel */}
                    {currentStep === "upload" && (
                      <div className="mt-16">
                        <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" particleCount={8} enableTilt>
                          <Card className="p-3 h-[calc(100vh-12rem)] flex flex-col">
                            <div className="flex items-center justify-between mb-3">
                              <h3 className="font-semibold text-sm">Upload Datasets</h3>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={handleUseMockData}
                                className="h-7 text-xs px-2"
                              >
                                Load Demo
                              </Button>
                            </div>
                            <Alert className="mb-3 flex-shrink-0 py-2 px-3">
                              <Info className="h-3 w-3" />
                              <AlertDescription className="text-[10px] leading-tight">
                                Upload CSV files from multiple financial institutions.
                              </AlertDescription>
                            </Alert>

                            <ScrollArea className="flex-1 pr-3 -mr-3">
                              <div className="grid grid-cols-2 gap-2">
                                {financialInstitutions.map((fi, index) => (
                                  <div key={fi.id} className="relative">
                                    <FileUploadZone
                                      label={`FI ${index + 1}`}
                                      file={fi.file}
                                      onFileSelect={(file) => updateFinancialInstitutionFile(fi.id, file)}
                                      disabled={status === "processing"}
                                      compact={true}
                                    />
                                    {financialInstitutions.length > 2 && (
                                      <button
                                        onClick={() => removeFinancialInstitution(fi.id)}
                                        className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full flex items-center justify-center text-[9px] hover:bg-red-600 transition-colors z-10"
                                        disabled={status === "processing"}
                                      >
                                        ×
                                      </button>
                                    )}
                                  </div>
                                ))}
                                <Button
                                  onClick={addFinancialInstitution}
                                  variant="outline"
                                  className="h-full min-h-[3.5rem] border border-dashed border-primary/50 hover:border-primary hover:bg-primary/5 transition-colors"
                                  disabled={status === "processing"}
                                >
                                  <div className="flex flex-col items-center gap-0.5">
                                    <span className="text-primary text-sm font-bold">+</span>
                                    <span className="text-[8px] leading-tight text-center">Add FI</span>
                                  </div>
                                </Button>
                              </div>
                            </ScrollArea>

                            <div className="flex-shrink-0 mt-3 space-y-2">
                              <Button
                                onClick={handleAnalyze}
                                disabled={financialInstitutions.filter((fi) => fi.file).length < 2 || status === "processing"}
                                className="w-full h-8 text-xs"
                              >
                                <Sparkles className="w-3 h-3 mr-1.5" />
                                Analyze
                              </Button>
                              {status === "processing" && currentStep === "upload" && (
                                <div>
                                  <Progress value={processingProgress} className="mb-1 h-1" />
                                  <p className="text-center text-muted-foreground text-[10px]">
                                    Processing... {processingProgress}%
                                  </p>
                                </div>
                              )}
                            </div>
                          </Card>
                        </ParticleCard>

                        {/* Agent Pipeline Visualization */}
                        <div>
                          <h3 className="font-semibold text-lg mb-6">Agent Pipeline</h3>
                          <div className="relative">
                            {/* Vertical connector line running through all agents */}
                            <div className="absolute left-3 top-3 bottom-3 w-0.5 bg-gradient-to-b from-green-500 via-green-500 to-muted" />
                            
                            <div className="space-y-0">
                              {/* Agent 1: Schema Analysis */}
                              <div className="relative flex items-start gap-4 pb-4">
                                <div className="relative flex-shrink-0">
                                  <div className={`w-6 h-6 rounded-full border-4 border-background shadow-lg flex items-center justify-center z-10 relative transition-all duration-300 ${
                                    activeAgents.has('system_schema') || activeAgents.has('system_monitor') 
                                      ? 'bg-green-500 animate-pulse' 
                                      : 'bg-muted'
                                  }`}>
                                    {activeAgents.has('system_schema') || activeAgents.has('system_monitor') ? (
                                      <Loader2 className="w-3 h-3 text-white animate-spin" />
                                    ) : (
                                      <span className="text-muted-foreground text-xs font-bold">○</span>
                                    )}
                                  </div>
                                </div>
                                <div className="flex-1 pt-0.5">
                                  <p className={`font-semibold text-sm ${
                                    activeAgents.has('system_schema') || activeAgents.has('system_monitor')
                                      ? 'text-green-500'
                                      : 'text-muted-foreground'
                                  }`}>Schema Reader</p>
                                  <p className="text-[10px] text-muted-foreground ml-2">└─ system_schema (Gemini)</p>
                                  <p className="text-[10px] text-muted-foreground ml-2">└─ system_monitor (Validation)</p>
                                </div>
                              </div>

                              {/* Agent 2: Mapping */}
                              <div className="relative flex items-start gap-4 pb-4">
                                <div className="relative flex-shrink-0">
                                  <div className={`w-6 h-6 rounded-full border-4 border-background shadow-lg flex items-center justify-center z-10 relative transition-all duration-300 ${
                                    activeAgents.has('system_mapping')
                                      ? 'bg-green-500 animate-pulse'
                                      : 'bg-muted'
                                  }`}>
                                    {activeAgents.has('system_mapping') ? (
                                      <Loader2 className="w-3 h-3 text-white animate-spin" />
                                    ) : (
                                      <span className="text-muted-foreground text-xs font-bold">○</span>
                                    )}
                                  </div>
                                </div>
                                <div className="flex-1 pt-0.5">
                                  <p className={`font-semibold text-sm ${
                                    activeAgents.has('system_mapping')
                                      ? 'text-green-500'
                                      : 'text-muted-foreground'
                                  }`}>Mapping Agent</p>
                                  <p className="text-[10px] text-muted-foreground ml-2">└─ system_mapping (Gemini)</p>
                                  <p className="text-[10px] text-muted-foreground ml-4">└─ calls system_schema</p>
                                </div>
                              </div>

                              {/* Agent 3: Merge Execution */}
                              <div className="relative flex items-start gap-4 pb-4">
                                <div className="relative flex-shrink-0">
                                  <div className={`w-6 h-6 rounded-full border-4 border-background shadow-lg flex items-center justify-center z-10 relative transition-all duration-300 ${
                                    activeAgents.has('system_join')
                                      ? 'bg-green-500 animate-pulse'
                                      : 'bg-muted'
                                  }`}>
                                    {activeAgents.has('system_join') ? (
                                      <Loader2 className="w-3 h-3 text-white animate-spin" />
                                    ) : (
                                      <span className="text-muted-foreground text-xs font-bold">○</span>
                                    )}
                                  </div>
                                </div>
                                <div className="flex-1 pt-0.5">
                                  <p className={`font-semibold text-sm ${
                                    activeAgents.has('system_join')
                                      ? 'text-green-500'
                                      : 'text-muted-foreground'
                                  }`}>Join Agent</p>
                                  <p className="text-[10px] text-muted-foreground ml-2">└─ system_join (SQL)</p>
                                  <p className="text-[10px] text-muted-foreground ml-4">└─ FULL_OUTER JOIN</p>
                                </div>
                              </div>

                              {/* Agent 4: Quality Check */}
                              <div className="relative flex items-start gap-4 pb-4">
                                <div className="relative flex-shrink-0">
                                  <div className={`w-6 h-6 rounded-full border-4 border-background shadow-lg flex items-center justify-center z-10 relative transition-all duration-300 ${
                                    activeAgents.has('system_monitor') || activeAgents.has('system_stats')
                                      ? 'bg-green-500 animate-pulse'
                                      : 'bg-muted'
                                  }`}>
                                    {activeAgents.has('system_monitor') || activeAgents.has('system_stats') ? (
                                      <Loader2 className="w-3 h-3 text-white animate-spin" />
                                    ) : (
                                      <span className="text-muted-foreground text-xs font-bold">○</span>
                                    )}
                                  </div>
                                </div>
                                <div className="flex-1 pt-0.5">
                                  <p className={`font-semibold text-sm ${
                                    activeAgents.has('system_monitor') || activeAgents.has('system_stats')
                                      ? 'text-green-500'
                                      : 'text-muted-foreground'
                                  }`}>Quality Check</p>
                                  <p className="text-[10px] text-muted-foreground ml-2">└─ system_monitor (Validation)</p>
                                  <p className="text-[10px] text-muted-foreground ml-2">└─ system_stats (Analytics)</p>
                                </div>
                              </div>

                              {/* Agent 5: Ingestion (Optional) */}
                              <div className="relative flex items-start gap-4">
                                <div className="relative flex-shrink-0">
                                  <div className={`w-6 h-6 rounded-full border-4 border-background shadow-lg flex items-center justify-center z-10 relative transition-all duration-300 ${
                                    activeAgents.has('system_ingestion')
                                      ? 'bg-green-500 animate-pulse'
                                      : 'bg-muted'
                                  }`}>
                                    {activeAgents.has('system_ingestion') ? (
                                      <Loader2 className="w-3 h-3 text-white animate-spin" />
                                    ) : (
                                      <span className="text-muted-foreground text-xs font-bold">○</span>
                                    )}
                                  </div>
                                </div>
                                <div className="flex-1 pt-0.5">
                                  <p className={`font-semibold text-sm ${
                                    activeAgents.has('system_ingestion')
                                      ? 'text-green-500'
                                      : 'text-muted-foreground'
                                  }`}>Snowflake Ingestion</p>
                                  <p className="text-[10px] text-muted-foreground ml-2">└─ system_ingestion (optional)</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {currentStep !== "upload" && (
                      <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" particleCount={8}>
                        <Card className="p-6">
                          <h3 className="mb-4">Integration Progress</h3>
                          <div className="space-y-3">
                            {/* 1 */}
                            <div
                              className={`flex items-start gap-3 p-3 rounded-lg ${
                                isDone(currentStep)
                                  ? "bg-green-500/10"
                                  : "bg-muted/30"
                              }`}
                            >
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                  isDone(currentStep)
                                    ? "bg-green-500 text-white"
                                    : "bg-muted-foreground/20"
                                }`}
                              >
                                ✓
                              </div>
                              <div>
                                <p>Upload Complete</p>
                                <p className="text-muted-foreground">Files analyzed</p>
                              </div>
                            </div>

                            {/* 2 */}
                            <div
                              className={`flex items-start gap-3 p-3 rounded-lg ${
                                currentStep === "mapping"
                                  ? "bg-primary/10"
                                  : currentStep === "conflicts" || currentStep === "results"
                                  ? "bg-green-500/10"
                                  : "bg-muted/30"
                              }`}
                            >
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                  currentStep === "mapping"
                                    ? "bg-primary text-primary-foreground"
                                    : currentStep === "conflicts" || currentStep === "results"
                                    ? "bg-green-500 text-white"
                                    : "bg-muted-foreground/20"
                                }`}
                              >
                                {currentStep === "conflicts" || currentStep === "results" ? "✓" : "2"}
                              </div>
                              <div>
                                <p>Schema Mapping</p>
                                <p className="text-muted-foreground">{mappings.length} mappings generated</p>
                              </div>
                            </div>

                            {/* 3 */}
                            <div
                              className={`flex items-start gap-3 p-3 rounded-lg ${
                                currentStep === "conflicts"
                                  ? "bg-primary/10"
                                  : currentStep === "results"
                                  ? "bg-green-500/10"
                                  : "bg-muted/30"
                              }`}
                            >
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                  currentStep === "conflicts"
                                    ? "bg-primary text-primary-foreground"
                                    : currentStep === "results"
                                    ? "bg-green-500 text-white"
                                    : "bg-muted-foreground/20"
                                }`}
                              >
                                {currentStep === "results" ? "✓" : "3"}
                              </div>
                              <div>
                                <p>Conflict Resolution</p>
                                <p className="text-muted-foreground">{conflicts.length} conflicts detected</p>
                              </div>
                            </div>

                            {/* 4 */}
                            <div
                              className={`flex items-start gap-3 p-3 rounded-lg ${
                                currentStep === "results" ? "bg-primary/10" : "bg-muted/30"
                              }`}
                            >
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                  currentStep === "results"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted-foreground/20"
                                }`}
                              >
                                4
                              </div>
                              <div>
                                <p>Integration Complete</p>
                                <p className="text-muted-foreground">Data merged &amp; validated</p>
                              </div>
                            </div>
                          </div>
                        </Card>
                      </ParticleCard>
                    )}
                  </div>
                </div>
              </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}




