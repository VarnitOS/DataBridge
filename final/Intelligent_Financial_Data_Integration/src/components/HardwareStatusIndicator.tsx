import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Cpu, Activity } from "lucide-react";

interface HardwareStatusIndicatorProps {
  status: 'idle' | 'processing' | 'success' | 'error';
}

export function HardwareStatusIndicator({ status }: HardwareStatusIndicatorProps) {
  const statusConfig = {
    idle: {
      color: 'bg-gray-400',
      label: 'Idle',
      glow: 'shadow-gray-400/50',
      text: 'System ready'
    },
    processing: {
      color: 'bg-blue-500',
      label: 'Processing',
      glow: 'shadow-blue-500/50',
      text: 'AI mapping in progress'
    },
    success: {
      color: 'bg-green-500',
      label: 'Success',
      glow: 'shadow-green-500/50',
      text: 'Data merged successfully'
    },
    error: {
      color: 'bg-red-500',
      label: 'Error',
      glow: 'shadow-red-500/50',
      text: 'Integration failed'
    }
  };

  const config = statusConfig[status];

  return (
    <Card className="p-6 bg-gradient-to-br from-card to-muted/20">
      <div className="flex items-center gap-3 mb-4">
        <Cpu className="w-5 h-5 text-primary" />
        <h3>Hardware Status Monitor</h3>
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-background/50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-4 h-4 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 via-green-500 via-blue-500 to-purple-500 animate-rainbow-pulse"></div>
              <div className="absolute inset-0 w-4 h-4 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 via-green-500 via-blue-500 to-purple-500 blur-sm animate-rainbow-pulse"></div>
            </div>
            <span>LED Indicator 1</span>
          </div>
          <Badge variant="outline">{config.label}</Badge>
        </div>

        <div className="flex items-center justify-between p-4 bg-background/50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-4 h-4 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 via-green-500 via-blue-500 to-purple-500 animate-rainbow-pulse"></div>
              <div className="absolute inset-0 w-4 h-4 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 via-green-500 via-blue-500 to-purple-500 blur-sm animate-rainbow-pulse"></div>
            </div>
            <span>LED Indicator 2</span>
          </div>
          <Badge variant="outline">{config.label}</Badge>
        </div>

        <div className="flex items-center gap-2 p-3 bg-primary/5 rounded-lg mt-4">
          <Activity className="w-4 h-4 text-primary" />
          <p className="text-muted-foreground">{config.text}</p>
        </div>
      </div>
    </Card>
  );
}
