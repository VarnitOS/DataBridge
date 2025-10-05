import { useState } from "react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { ArrowRight, CheckCircle, AlertCircle, Edit2, X } from "lucide-react";
import { Progress } from "./ui/progress";

interface FieldMapping {
  sourceField: string;
  targetField: string;
  confidence: number;
  status: 'confirmed' | 'suggested' | 'manual';
}

interface VisualSchemaMappingViewProps {
  mappings: FieldMapping[];
  sourceFields: string[];
  targetFields: string[];
  onMappingChange?: (mappings: FieldMapping[]) => void;
  onConfirm?: () => void;
}

export function VisualSchemaMappingView({ 
  mappings, 
  sourceFields, 
  targetFields,
  onMappingChange,
  onConfirm 
}: VisualSchemaMappingViewProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [localMappings, setLocalMappings] = useState(mappings);

  const avgConfidence = localMappings.reduce((sum, m) => sum + m.confidence, 0) / localMappings.length;

  const handleRemoveMapping = (index: number) => {
    const updated = localMappings.filter((_, i) => i !== index);
    setLocalMappings(updated);
    onMappingChange?.(updated);
  };

  const handleOverrideMapping = (index: number) => {
    const updated = [...localMappings];
    updated[index] = { ...updated[index], status: 'manual' };
    setLocalMappings(updated);
    onMappingChange?.(updated);
    setEditingIndex(null);
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="mb-2">Visual Schema Mapping</h2>
          <p className="text-muted-foreground">
            AI-suggested mappings with visual connections
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="gap-2">
            <span>Avg Confidence:</span>
            <span>{(avgConfidence * 100).toFixed(0)}%</span>
          </Badge>
          <Badge variant="outline">
            {localMappings.filter(m => m.status === 'confirmed').length} Confirmed
          </Badge>
          <Badge variant="outline">
            {localMappings.filter(m => m.status === 'manual').length} Manual
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-[1fr,auto,1fr] gap-6 mb-6">
        {/* Source Schema Column */}
        <div className="space-y-2">
          <div className="p-3 bg-blue-500/10 rounded-lg border-2 border-blue-500/30 mb-4">
            <h3 className="text-blue-600 dark:text-blue-400">Source Schema (Bank A)</h3>
          </div>
          <div className="space-y-2">
            {sourceFields.map((field, index) => (
              <div
                key={field}
                className="p-3 bg-blue-500/5 rounded-lg border border-blue-500/20 hover:bg-blue-500/10 transition-colors"
              >
                <p className="text-blue-600 dark:text-blue-400">{field}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Mapping Connections */}
        <div className="flex flex-col justify-center space-y-2 min-w-[200px]">
          {localMappings.map((mapping, index) => {
            const isAI = mapping.status === 'confirmed' || mapping.status === 'suggested';
            const isHighConfidence = mapping.confidence > 0.8;

            return (
              <div
                key={index}
                className="flex items-center gap-2 p-2 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors group"
              >
                <div className="flex-1 flex items-center justify-center gap-2">
                  {isHighConfidence ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-yellow-500" />
                  )}
                  <div className="flex-1">
                    <Progress value={mapping.confidence * 100} className="h-1.5" />
                  </div>
                  <span className="text-xs text-muted-foreground min-w-[3rem] text-right">
                    {(mapping.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {isAI && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditingIndex(editingIndex === index ? null : index)}
                    >
                      <Edit2 className="w-3 h-3" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveMapping(index)}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Target Schema Column */}
        <div className="space-y-2">
          <div className="p-3 bg-green-500/10 rounded-lg border-2 border-green-500/30 mb-4">
            <h3 className="text-green-600 dark:text-green-400">Target Schema (Bank B)</h3>
          </div>
          <div className="space-y-2">
            {targetFields.map((field, index) => (
              <div
                key={field}
                className="p-3 bg-green-500/5 rounded-lg border border-green-500/20 hover:bg-green-500/10 transition-colors"
              >
                <p className="text-green-600 dark:text-green-400">{field}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mapping Details */}
      <div className="space-y-2 mb-6">
        {localMappings.map((mapping, index) => (
          <div
            key={index}
            className={`flex items-center gap-4 p-4 rounded-lg border-2 transition-all ${
              mapping.status === 'confirmed'
                ? 'bg-green-500/5 border-green-500/20'
                : mapping.status === 'suggested'
                ? 'bg-yellow-500/5 border-yellow-500/20'
                : 'bg-purple-500/5 border-purple-500/20'
            }`}
          >
            <div className="flex-1 flex items-center gap-3">
              <div className="px-3 py-1.5 bg-blue-500/10 rounded-md border border-blue-500/20">
                <p className="text-blue-600 dark:text-blue-400">{mapping.sourceField}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <div className="px-3 py-1.5 bg-green-500/10 rounded-md border border-green-500/20">
                <p className="text-green-600 dark:text-green-400">{mapping.targetField}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge 
                variant={mapping.status === 'confirmed' ? 'default' : 'outline'}
                className={
                  mapping.status === 'confirmed'
                    ? 'bg-green-500 text-white'
                    : mapping.status === 'manual'
                    ? 'bg-purple-500 text-white'
                    : ''
                }
              >
                {mapping.status === 'confirmed' && 'AI Confirmed'}
                {mapping.status === 'suggested' && 'AI Suggested'}
                {mapping.status === 'manual' && 'Manual Override'}
              </Badge>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-muted/30 rounded-lg p-4 mb-6">
        <h4 className="mb-2">Gemini AI Insights</h4>
        <p className="text-muted-foreground">
          • Detected {localMappings.length} field correlations across schemas
          <br />
          • {localMappings.filter(m => m.confidence > 0.9).length} high-confidence matches (&gt;90%)
          <br />
          • Recommended normalization: Standardize all ID fields to "_id" suffix for consistency
          <br />
          • No critical data type mismatches detected
        </p>
      </div>

      {onConfirm && (
        <Button onClick={onConfirm} className="w-full">
          Confirm Mappings & Continue to Merge
        </Button>
      )}
    </Card>
  );
}
