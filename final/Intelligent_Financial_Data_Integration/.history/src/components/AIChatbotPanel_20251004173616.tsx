import { useState, useRef, useEffect } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { Bot, Send, Sparkles, X, Minimize2, Maximize2, Loader2, AlertCircle } from "lucide-react";

interface Message {
  id: string;
  role: 'user' | 'assistant';
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
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your EY DataFusion AI assistant powered by Gemini. I can help you understand schema mappings, resolve conflicts, and suggest data normalization strategies. What would you like to know?",
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isMinimized, setIsMinimized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationType, setAnimationType] = useState<'minimize' | 'restore' | null>(null);
  const [showParticles, setShowParticles] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleMinimize = () => {
    if (isAnimating) return;
    
    setIsAnimating(true);
    setAnimationType('minimize');
    
    // Add the minimize animation class
    if (chatRef.current) {
      chatRef.current.classList.add('animate-minimize-shrink');
      chatRef.current.classList.add('animate-minimize-glow');
    }
    
    // Wait for animation to complete, then minimize
    setTimeout(() => {
      setIsMinimized(true);
      setIsAnimating(false);
      setAnimationType(null);
      
      // Clean up animation classes
      if (chatRef.current) {
        chatRef.current.classList.remove('animate-minimize-shrink', 'animate-minimize-glow');
      }
    }, 500);
  };

  const handleRestore = () => {
    if (isAnimating) return;
    
    setIsAnimating(true);
    setAnimationType('restore');
    setIsMinimized(false);
    
    // Add the restore animation class
    if (chatRef.current) {
      chatRef.current.classList.add('animate-minimize-bounce');
    }
    
    // Clean up animation classes after completion
    setTimeout(() => {
      setIsAnimating(false);
      setAnimationType(null);
      
      if (chatRef.current) {
        chatRef.current.classList.remove('animate-minimize-bounce');
      }
    }, 400);
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendToGeminiAPI(input, context, messages);
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        citations: ['Gemini AI', 'EY DataFusion Knowledge Base']
      };

      setMessages(prev => [...prev, aiResponse]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
        timestamp: new Date(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsLoading(false);
    }

    setInput('');
  };

  const sendToGeminiAPI = async (message: string, context: any, history: Message[]) => {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001';
    
    const response = await fetch(`${API_BASE_URL}/api/chatbot`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        context: {
          currentStep: context?.currentStep,
          mappings: context?.mappings,
          conflicts: context?.conflicts,
          timestamp: new Date().toISOString()
        },
        history: history.slice(-10).map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      }),
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  };

  const generateAIResponse = (query: string, ctx?: any): Message => {
    const lowerQuery = query.toLowerCase();
    let content = '';
    let citations: string[] = [];

    if (lowerQuery.includes('merge') || lowerQuery.includes('explain')) {
      content = "This merge operation combines data from two banking systems by mapping similar fields. The AI has identified high-confidence matches (>80%) based on field name similarity, data type compatibility, and industry-standard naming conventions. Fields like 'account_num' → 'account_number' show 95% confidence due to semantic similarity.";
      citations = ['Schema Analysis Engine', 'Gemini AI v2.0'];
    } else if (lowerQuery.includes('normalize') || lowerQuery.includes('schema')) {
      content = "For optimal normalization, I recommend:\n\n1. Standardize field names using snake_case (customer_id, account_number)\n2. Consolidate date formats to ISO 8601 (YYYY-MM-DD)\n3. Use consistent data types: VARCHAR(50) for IDs, DECIMAL(15,2) for currency\n4. Create a unified customer_master table with normalized attributes\n\nThis will reduce redundancy by ~40% and improve query performance.";
      citations = ['Data Normalization Standards', 'EY Best Practices Guide'];
    } else if (lowerQuery.includes('conflict')) {
      content = "I've detected 3 potential conflicts in the current dataset:\n\n1. Duplicate customer IDs with different addresses (12 records)\n2. Date format inconsistencies between systems\n3. Currency field precision mismatch\n\nRecommendation: Use the most recent record based on last_modified timestamp for duplicates. Would you like me to apply this resolution automatically?";
      citations = ['Conflict Detection Algorithm', 'Deduplication Engine'];
    } else if (lowerQuery.includes('quality') || lowerQuery.includes('score')) {
      content = "Current data quality score is 96/100. Breakdown:\n\n✓ Completeness: 98% (minimal null values)\n✓ Accuracy: 95% (validated against reference data)\n✓ Consistency: 94% (standardized formats)\n⚠ Uniqueness: 92% (12 duplicate records found)\n\nThe main issue is duplicate customer records. I recommend enabling auto-deduplication with 'keep latest' strategy.";
      citations = ['Data Quality Framework', 'ISO 8000 Standards'];
    } else {
      content = "I can help you with:\n\n• Explaining merge operations and mappings\n• Suggesting schema normalization strategies\n• Resolving data conflicts and duplicates\n• Analyzing data quality scores\n• Recommending best practices for data integration\n\nWhat specific area would you like assistance with?";
      citations = ['EY DataFusion Knowledge Base'];
    }

    return {
      id: Date.now().toString(),
      role: 'assistant',
      content,
      timestamp: new Date(),
      citations,
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
                  {messages.filter(m => m.role === 'user').length}
                </span>
              </div>
            )}
          </div>
        </Button>
        
        {/* Floating notification */}
        {messages.length > 1 && (
          <div className="absolute -top-2 -left-2 bg-primary text-primary-foreground text-xs px-2 py-1 rounded-full shadow-lg animate-bounce">
            {messages.filter(m => m.role === 'user').length} new
          </div>
        )}
      </div>
    );
  }

  return (
    <div 
      ref={chatRef}
      className={`fixed bottom-6 right-6 z-50 w-96 transition-all duration-300 ${
        isAnimating && animationType === 'minimize' ? 'animate-minimize-shrink' : ''
      } ${isAnimating && animationType === 'restore' ? 'animate-minimize-bounce' : ''}`}
    >
      <Card className="shadow-2xl border-2 border-primary/20 hover:border-primary/40 transition-all duration-300 hover:shadow-primary/10 hover:shadow-2xl">
        <div className="p-4 border-b bg-gradient-to-r from-primary/5 to-primary/10 flex items-center justify-between">
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

        <ScrollArea className="h-96 p-4" ref={scrollRef}>
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : message.isError
                      ? 'bg-destructive/10 border border-destructive/20'
                      : 'bg-muted'
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
        </ScrollArea>

        <div className="p-4 border-t">
          <div className="flex gap-2">
            <Input
              placeholder="Ask about mappings, conflicts, or quality..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            />
            <Button onClick={handleSend} size="sm" disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
          <p className="text-muted-foreground mt-2 text-center">
            Natural language queries supported
          </p>
        </div>
      </Card>
    </div>
  );
}
