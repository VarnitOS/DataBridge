// src/App.tsx
import { useState, useEffect, useRef } from "react";
import { ParticleCard, GlobalSpotlight } from "./components/Magic/MagicBento";
import LiquidEther from "./components/backgrounds/LiquidEther";
import { MainNavigation } from "./components/MainNavigation";
import { FileUploadZone } from "./components/FileUploadZone";
import { HardwareStatusIndicator } from "./components/HardwareStatusIndicator";
import { VisualSchemaMappingView } from "./components/VisualSchemaMappingView";
import { MonitoringDashboard } from "./components/MonitoringDashboard";
import { DataPreviewTable } from "./components/DataPreviewTable";
import { ConflictResolutionPanel } from "./components/ConflictResolutionPanel";
import { ProjectManagementPanel } from "./components/ProjectManagementPanel";
import { CollaborationPanel } from "./components/CollaborationPanel";
import { UserProfilePanel } from "./components/UserProfilePanel";
import { ReportGenerator } from "./components/ReportGenerator";
import { AIChatbotPanel } from "./components/AIChatbotPanel";
import { Button } from "./components/ui/button";
import { Card } from "./components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Alert, AlertDescription } from "./components/ui/alert";
import { parseCSV, getFieldNames, generateMockBankData } from "./utils/csvParser";
import { generateAIMappings, mergeDatasets } from "./utils/aiMappingSimulator";
import { mockConflicts } from "./utils/mockData";
import { Sparkles, Info, AlertTriangle } from "lucide-react";
import { Progress } from "./components/ui/progress";
import { Badge } from "./components/ui/badge";

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
  const [customTabs, setCustomTabs] = useState<Array<{id: string, label: string}>>([]);
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [sourceData, setSourceData] = useState<Record<string, any>[]>([]);
  const [targetData, setTargetData] = useState<Record<string, any>[]>([]);
  const [mappings, setMappings] = useState<FieldMapping[]>([]);
  const [mergedData, setMergedData] = useState<Record<string, any>[]>([]);
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [processingProgress, setProcessingProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState<Step>("upload");
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [conflicts] = useState(mockConflicts);
  const [showProfile, setShowProfile] = useState(false);

  // Step 5: global spotlight wrapper
  const bentoRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDarkMode);
  }, [isDarkMode]);

  const handleAnalyze = async () => {
    if (!sourceFile || !targetFile) return;
    setStatus("processing");
    setCurrentStep("mapping");
    setProcessingProgress(0);

    const steps = [
      { progress: 20, delay: 500 },
      { progress: 40, delay: 800 },
      { progress: 60, delay: 600 },
      { progress: 80, delay: 700 },
      { progress: 100, delay: 500 }
    ];

    try {
      const sourceParsed = await parseCSV(sourceFile);
      const targetParsed = await parseCSV(targetFile);

      for (const step of steps) {
        await new Promise((r) => setTimeout(r, step.delay));
        setProcessingProgress(step.progress);
      }

      setSourceData(sourceParsed);
      setTargetData(targetParsed);

      const sourceFields = getFieldNames(sourceParsed);
      const targetFields = getFieldNames(targetParsed);
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
          <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20" style={{ position: "relative" }}>
            <MainNavigation
              currentView="profile"
              onViewChange={(view) => {
                setShowProfile(false);
                setCurrentView(view);
              }}
              onProfileClick={() => setShowProfile(true)}
            />

            <div className="container mx-auto px-6 py-8 max-w-4xl">
              <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" enableTilt enableMagnetism particleCount={10}>
                <Card className="p-6">
                  <UserProfilePanel onThemeToggle={() => setIsDarkMode(!isDarkMode)} isDarkMode={isDarkMode} />
                </Card>
              </ParticleCard>
            </div>

            <AIChatbotPanel context={{ currentStep, mappings, conflicts }} />
          </div>
        ) : (
          /* ======== OTHER VIEWS (default) ======== */
          <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20" style={{ position: "relative" }}>
            <MainNavigation currentView={currentView} onViewChange={setCurrentView} onProfileClick={() => setShowProfile(true)} />

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
                      <h1 className="text-3xl font-bold text-white mb-2">Add Title</h1>
                      <p className="text-white/60">Click to edit this title</p>
                    </div>

                    {/* Comment Box */}
                    <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700/50 p-4">
                      <textarea
                        placeholder="Add a comment..."
                        className="w-full bg-transparent text-white placeholder-gray-400 resize-none outline-none min-h-[120px] text-lg"
                        style={{
                          fontFamily: 'inherit',
                          lineHeight: '1.5'
                        }}
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

              {/* Integration */}
              {currentView === "integration" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Main column */}
                  <div className="lg:col-span-2 space-y-6">
                    {/* Step 1 */}
                    {currentStep === "upload" && (
                      <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" particleCount={12} enableTilt enableMagnetism clickEffect>
                        <Card className="p-6">
                          <div className="flex items-center justify-between mb-6">
                            <h2>Step 1: Upload Bank Datasets</h2>
                            <Button variant="outline" size="sm" onClick={handleUseMockData}>
                              Load Demo Data
                            </Button>
                          </div>
                          <Alert className="mb-6">
                            <Info className="h-4 w-4" />
                            <AlertDescription>
                              Upload CSV files from both merging banks. Our AI will automatically analyze and map the schemas.
                            </AlertDescription>
                          </Alert>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                            <FileUploadZone label="Bank A Dataset" file={sourceFile} onFileSelect={setSourceFile} disabled={status === "processing"} />
                            <FileUploadZone label="Bank B Dataset" file={targetFile} onFileSelect={setTargetFile} disabled={status === "processing"} />
                          </div>
                          <Button onClick={handleAnalyze} disabled={!sourceFile || !targetFile || status === "processing"} className="w-full">
                            <Sparkles className="w-4 h-4 mr-2" />
                            Analyze &amp; Generate AI Mappings
                          </Button>
                          {status === "processing" && currentStep === "upload" && (
                            <div className="mt-4">
                              <Progress value={processingProgress} className="mb-2" />
                              <p className="text-center text-muted-foreground">Processing files... {processingProgress}%</p>
                            </div>
                          )}
                        </Card>
                      </ParticleCard>
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
                          <AlertDescription>Review and resolve data conflicts before finalizing the merge</AlertDescription>
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

                  {/* Sidebar */}
                  <div className="space-y-6">
                    <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" particleCount={8} enableTilt>
                      <Card className="p-6">
                        <HardwareStatusIndicator status={status} />
                      </Card>
                    </ParticleCard>

                    {currentStep !== "upload" && (
                      <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" particleCount={8}>
                        <Card className="p-6">
                          <h3 className="mb-4">Integration Progress</h3>
                          <div className="space-y-3">
                            {/* 1 */}
                            <div
                              className={`flex items-start gap-3 p-3 rounded-lg ${
                                currentStep === "upload" ? "bg-primary/10" : isDone(currentStep) ? "bg-green-500/10" : "bg-muted/30"
                              }`}
                            >
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                  currentStep === "upload" ? "bg-primary text-primary-foreground" : isDone(currentStep) ? "bg-green-500 text-white" : "bg-muted-foreground/20"
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
                                currentStep === "mapping" ? "bg-primary/10" : currentStep === "conflicts" || currentStep === "results" ? "bg-green-500/10" : "bg-muted/30"
                              }`}
                            >
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                  currentStep === "mapping" ? "bg-primary text-primary-foreground" : currentStep === "conflicts" || currentStep === "results" ? "bg-green-500 text-white" : "bg-muted-foreground/20"
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
                                currentStep === "conflicts" ? "bg-primary/10" : currentStep === "results" ? "bg-green-500/10" : "bg-muted/30"
                              }`}
                            >
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                  currentStep === "conflicts" ? "bg-primary text-primary-foreground" : currentStep === "results" ? "bg-green-500 text-white" : "bg-muted-foreground/20"
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
                            <div className={`flex items-start gap-3 p-3 rounded-lg ${currentStep === "results" ? "bg-primary/10" : "bg-muted/30"}`}>
                              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${currentStep === "results" ? "bg-primary text-primary-foreground" : "bg-muted-foreground/20"}`}>
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

                    <ParticleCard className="card card--border-glow" glowColor="132, 0, 255" particleCount={6}>
                      <Card className="p-6 bg-gradient-to-br from-primary/5 to-primary/10">
                        <h3 className="mb-3">Enterprise Features</h3>
                        <ul className="space-y-2 text-muted-foreground">
                          <li className="flex items-start gap-2">
                            <Sparkles className="w-4 h-4 mt-0.5 text-primary flex-shrink-0" />
                            <span>AI-powered schema mapping</span>
                          </li>
                          <li className="flex items-start gap-2">
                            <AlertTriangle className="w-4 h-4 mt-0.5 text-primary flex-shrink-0" />
                            <span>Intelligent conflict resolution</span>
                          </li>
                          <li className="flex items-start gap-2">
                            <Info className="w-4 h-4 mt-0.5 text-primary flex-shrink-0" />
                            <span>Team collaboration tools</span>
                          </li>
                          <li className="flex items-start gap-2">
                            <Info className="w-4 h-4 mt-0.5 text-primary flex-shrink-0" />
                            <span>Automated reporting</span>
                          </li>
                        </ul>
                      </Card>
                    </ParticleCard>
                  </div>
                </div>
              )}
            </div>

            <AIChatbotPanel context={{ currentStep, mappings, conflicts }} />
          </div>
        )}
      </div>
    </>
  );
}
