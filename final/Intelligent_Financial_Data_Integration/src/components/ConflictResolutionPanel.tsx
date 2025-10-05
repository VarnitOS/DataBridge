import { useState } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { AlertTriangle, CheckCircle, Clock, Sparkles } from "lucide-react";

interface DataConflict {
  id: string;
  rowNumber: number;
  field: string;
  sourceValue: string;
  targetValue: string;
  type: 'duplicate' | 'mismatch' | 'format';
  severity: 'high' | 'medium' | 'low';
  aiSuggestion: string;
  resolutionOptions: string[];
}

interface ConflictResolutionPanelProps {
  conflicts: DataConflict[];
  onResolve?: (conflictId: string, resolution: string) => void;
  onResolveAll?: () => void;
}

export function ConflictResolutionPanel({ 
  conflicts, 
  onResolve,
  onResolveAll 
}: ConflictResolutionPanelProps) {
  const [resolvedConflicts, setResolvedConflicts] = useState<Set<string>>(new Set());

  const handleResolve = (conflictId: string, resolution: string) => {
    setResolvedConflicts(prev => new Set([...prev, conflictId]));
    onResolve?.(conflictId, resolution);
  };

  const unresolvedCount = conflicts.length - resolvedConflicts.size;
  const highSeverityCount = conflicts.filter(c => c.severity === 'high' && !resolvedConflicts.has(c.id)).length;

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="mb-2">Data Quality & Conflict Resolution</h2>
          <p className="text-muted-foreground">
            Review and resolve data conflicts detected during merge
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={highSeverityCount > 0 ? 'destructive' : 'outline'} className="gap-1">
            <AlertTriangle className="w-3 h-3" />
            {unresolvedCount} Unresolved
          </Badge>
          <Badge variant="outline" className="gap-1">
            <CheckCircle className="w-3 h-3" />
            {resolvedConflicts.size} Resolved
          </Badge>
        </div>
      </div>

      {unresolvedCount > 0 && (
        <div className="mb-4">
          <Button onClick={onResolveAll} variant="outline" className="w-full">
            <Sparkles className="w-4 h-4 mr-2" />
            Auto-Resolve All with AI Suggestions
          </Button>
        </div>
      )}

      <ScrollArea className="h-[600px] pr-4">
        <div className="space-y-4">
          {conflicts.map((conflict) => {
            const isResolved = resolvedConflicts.has(conflict.id);
            
            return (
              <Card
                key={conflict.id}
                className={`p-4 border-2 ${
                  isResolved
                    ? 'bg-green-500/5 border-green-500/20'
                    : conflict.severity === 'high'
                    ? 'bg-destructive/5 border-destructive/20'
                    : conflict.severity === 'medium'
                    ? 'bg-yellow-500/5 border-yellow-500/20'
                    : 'bg-blue-500/5 border-blue-500/20'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {isResolved ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className={`w-5 h-5 ${
                        conflict.severity === 'high' ? 'text-destructive' :
                        conflict.severity === 'medium' ? 'text-yellow-500' :
                        'text-blue-500'
                      }`} />
                    )}
                    <div>
                      <h4>Row {conflict.rowNumber} - {conflict.field}</h4>
                      <p className="text-muted-foreground">
                        Conflict Type: {conflict.type.charAt(0).toUpperCase() + conflict.type.slice(1)}
                      </p>
                    </div>
                  </div>
                  <Badge 
                    variant={
                      conflict.severity === 'high' ? 'destructive' : 
                      conflict.severity === 'medium' ? 'outline' : 
                      'secondary'
                    }
                  >
                    {conflict.severity.toUpperCase()}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                    <p className="text-muted-foreground mb-1">Bank A Value</p>
                    <p className="text-blue-600 dark:text-blue-400">{conflict.sourceValue}</p>
                  </div>
                  <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                    <p className="text-muted-foreground mb-1">Bank B Value</p>
                    <p className="text-green-600 dark:text-green-400">{conflict.targetValue}</p>
                  </div>
                </div>

                <div className="p-3 bg-primary/5 rounded-lg mb-4">
                  <div className="flex items-start gap-2">
                    <Sparkles className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-muted-foreground">Gemini AI Recommendation:</p>
                      <p>{conflict.aiSuggestion}</p>
                    </div>
                  </div>
                </div>

                {!isResolved && (
                  <div className="flex gap-2">
                    {conflict.resolutionOptions.map((option, idx) => (
                      <Button
                        key={idx}
                        variant={idx === 0 ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleResolve(conflict.id, option)}
                        className="flex-1"
                      >
                        {option}
                      </Button>
                    ))}
                  </div>
                )}

                {isResolved && (
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    <CheckCircle className="w-4 h-4" />
                    <span>Conflict resolved</span>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </ScrollArea>
    </Card>
  );
}
