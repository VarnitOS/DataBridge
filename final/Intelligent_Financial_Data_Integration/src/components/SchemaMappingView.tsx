import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { ArrowRight, CheckCircle, AlertCircle, Sparkles } from "lucide-react";
import { Progress } from "./ui/progress";

interface FieldMapping {
  sourceField: string;
  targetField: string;
  confidence: number;
  status: 'confirmed' | 'suggested' | 'manual';
}

interface SchemaMappingViewProps {
  mappings: FieldMapping[];
  onConfirm?: () => void;
}

export function SchemaMappingView({ mappings, onConfirm }: SchemaMappingViewProps) {
  const avgConfidence = mappings.reduce((sum, m) => sum + m.confidence, 0) / mappings.length;

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-primary" />
          <h3>AI-Powered Schema Mapping</h3>
        </div>
        <Badge variant="outline" className="gap-2">
          <span>Avg Confidence:</span>
          <span>{(avgConfidence * 100).toFixed(0)}%</span>
        </Badge>
      </div>

      <div className="space-y-3 mb-6">
        {mappings.map((mapping, index) => (
          <div 
            key={index}
            className="flex items-center gap-4 p-4 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors"
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

            <div className="flex items-center gap-3">
              <div className="w-24">
                <Progress value={mapping.confidence * 100} className="h-2" />
              </div>
              <span className="text-muted-foreground min-w-[3rem] text-right">
                {(mapping.confidence * 100).toFixed(0)}%
              </span>
              {mapping.confidence > 0.8 ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-500" />
              )}
            </div>
          </div>
        ))}
      </div>

      {onConfirm && (
        <Button onClick={onConfirm} className="w-full">
          Confirm Mappings & Merge Data
        </Button>
      )}
    </Card>
  );
}
