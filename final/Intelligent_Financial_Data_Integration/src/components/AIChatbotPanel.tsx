// src/components/AIChatbotPanel.tsx
import { useState, useRef, useEffect } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Bot, Send, Sparkles, Minimize2, Loader2, AlertCircle } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  citations?: string[];
  isError?: boolean;
}

interface AIChatbotPanelProps {
  context?: {
    currentStep?: string;
    mappings?: any[];
    conflicts?: any[];
  };
}

export function AIChatbotPanel({ context }: AIChatbotPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your EY DataFusion AI assistant powered by Gemini. I can help you understand schema mappings, resolve conflicts, and suggest data normalization strategies. What would you like to know?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isMinimized, setIsMinimized] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationType, setAnimationType] = useState<"minimize" | "restore" | null>(null);
  const [showParticles, setShowParticles] = useState(false);

  // Use a direct DIV viewport instead of shadcn ScrollArea
  const viewportRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const atBottomRef = useRef(true); // track if user is near bottom

  // Track whether user scrolled up; only autoscroll when near bottom
  const handleViewportScroll = () => {
    const el = viewportRef.current;
    if (!el) return;
    const delta = el.scrollHeight - el.scrollTop - el.clientHeight;
    atBottomRef.current = delta < 50; // within 50px of bottom counts as "at bottom"
  };

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;

    if (atBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  const handleMinimize = () => {
    if (isAnimating) return;

    setIsAnimating(true);
    setAnimationType("minimize");
    setShowParticles(true);

    if (chatRef.current) {
      chatRef.current.classList.add("animate-minimize-shrink");
      chatRef.current.classList.add("animate-minimize-glow");
    }

    setTimeout(() => setShowParticles(false), 800);

    setTimeout(() => {
      setIsMinimized(true);
      setIsAnimating(false);
      setAnimationType(null);
      if (chatRef.current) {
        chatRef.current.classList.remove("animate-minimize-shrink", "animate-minimize-glow");
      }
    }, 500);
  };

  const handleRestore = () => {
    if (isAnimating) return;

    setIsAnimating(true);
    setAnimationType("restore");
    setIsMinimized(false);

    if (chatRef.current) chatRef.current.classList.add("animate-minimize-bounce");

    setTimeout(() => {
      setIsAnimating(false);
      setAnimationType(null);
      if (chatRef.current) chatRef.current.classList.remove("animate-minimize-bounce");
    }, 400);
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendToGeminiAPI(userMessage.content, context, messages);

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
        citations: ["Gemini AI", "EY DataFusion Knowledge Base"],
      };

      setMessages((prev) => [...prev, aiResponse]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      setError(err instanceof Error ? err.message : "Unknown error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const sendToGeminiAPI = async (message: string, _context: any, _history: Message[]) => {
    const CHATBOT_URL = "http://localhost:8002/chat";
    const sessionId = `frontend_session_${Date.now()}`;

    const response = await fetch(CHATBOT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return {
      response: data.answer || data.message || "No response from chatbot",
      confidence: data.confidence,
      reasoning: data.reasoning,
    };
  };

  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <Button
          onClick={handleRestore}
          className="chat-minimized-button rounded-full w-16 h-16 shadow-2xl bg-gradient-to-br from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 transition-all duration-300 hover:scale-110 hover:shadow-primary/25 hover:shadow-xl"
          disabled={isAnimating}
        >
          <div className="relative">
            <Bot className="w-7 h-7 animate-pulse" />
            {messages.length > 1 && (
              <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                <span className="text-xs text-white font-bold">
                  {messages.filter((m) => m.role === "user").length}
                </span>
              </div>
            )}
          </div>
        </Button>

        {messages.length > 1 && (
          <div className="absolute -top-2 -left-2 bg-primary text-primary-foreground text-xs px-2 py-1 rounded-full shadow-lg animate-bounce">
            {messages.filter((m) => m.role === "user").length} new
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {showParticles && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="particle" />
          <div className="particle" />
          <div className="particle" />
          <div className="particle" />
        </div>
      )}

      <div
        ref={chatRef}
        className={`w-96 transition-all duration-300 ${
          isAnimating && animationType === "minimize" ? "animate-minimize-shrink" : ""
        } ${isAnimating && animationType === "restore" ? "animate-minimize-bounce" : ""}`}
      >
        {/* 
          IMPORTANT:
          - Use max height tied to viewport so the card never grows off-screen.
          - Card is a flex column; middle pane is the scrollable viewport.
        */}
        <Card className="flex flex-col max-h-[80vh] h-[min(80vh,640px)] shadow-2xl border-2 border-primary/20 hover:border-primary/40 transition-all duration-300 hover:shadow-primary/10 hover:shadow-2xl overflow-hidden">
          {/* Header (non-scrollable) */}
          <div className="p-4 border-b bg-gradient-to-r from-primary/5 to-primary/10 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-primary to-primary/80 rounded-lg shadow-lg">
                <Bot className="w-4 h-4 text-primary-foreground animate-pulse" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">AI Assistant</h3>
                <p className="text-muted-foreground text-sm">Powered by Gemini</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMinimize}
                disabled={isAnimating}
                className="hover:bg-primary/10 hover:text-primary transition-all duration-200 hover:scale-110"
              >
                <Minimize2 className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Scrollable messages viewport */}
          <div
            ref={viewportRef}
            onScroll={handleViewportScroll}
            className="flex-1 min-h-0 overflow-y-auto p-4"
            style={{ WebkitOverflowScrolling: "touch" }} // smoother on iOS
          >
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg p-3 ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : message.isError
                        ? "bg-destructive/10 border border-destructive/20"
                        : "bg-muted"
                    }`}
                  >
                    {message.isError && (
                      <div className="flex items-center gap-2 mb-2 text-destructive">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm font-medium">Error</span>
                      </div>
                    )}
                    <p className="whitespace-pre-wrap">{message.content}</p>

                    {message.citations && message.citations.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-border/50">
                        <div className="flex flex-wrap gap-1">
                          {message.citations.map((citation, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              <Sparkles className="w-3 h-3 mr-1" />
                              {citation}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <p className="text-xs text-muted-foreground mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="max-w-[85%] rounded-lg p-3 bg-muted">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <p className="text-muted-foreground">Gemini is thinking...</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input (non-scrollable) */}
          <div className="p-4 border-t flex-shrink-0">
            <div className="flex gap-2">
              <Input
                placeholder="Ask about mappings, conflicts, or quality..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
              />
              <Button onClick={handleSend} size="sm" disabled={isLoading || !input.trim()}>
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>
            <p className="text-muted-foreground mt-2 text-center">Natural language queries supported</p>
          </div>
        </Card>
      </div>
    </div>
  );
}


