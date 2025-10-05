import { Card } from "./ui/card";
import { Activity, Database, CheckCircle, Clock } from "lucide-react";
import { Progress } from "./ui/progress";

interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  change?: string;
  progress?: number;
}

function MetricCard({ title, value, icon, change, progress }: MetricCardProps) {
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="p-2 bg-primary/10 rounded-lg">
          {icon}
        </div>
        {change && (
          <span className="text-green-600 dark:text-green-400">{change}</span>
        )}
      </div>
      <p className="text-muted-foreground mb-1">{title}</p>
      <h2 className="mb-3">{value}</h2>
      {progress !== undefined && (
        <Progress value={progress} className="h-1.5" />
      )}
    </Card>
  );
}

interface MonitoringDashboardProps {
  recordsProcessed: number;
  totalRecords: number;
  processingTime: string;
  dataQualityScore: number;
}

export function MonitoringDashboard({
  recordsProcessed,
  totalRecords,
  processingTime,
  dataQualityScore
}: MonitoringDashboardProps) {
  const completionRate = (recordsProcessed / totalRecords) * 100;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Records Processed"
        value={`${recordsProcessed.toLocaleString()} / ${totalRecords.toLocaleString()}`}
        icon={<Database className="w-5 h-5 text-primary" />}
        progress={completionRate}
      />
      
      <MetricCard
        title="Processing Time"
        value={processingTime}
        icon={<Clock className="w-5 h-5 text-primary" />}
        change="-12%"
      />
      
      <MetricCard
        title="Data Quality Score"
        value={`${dataQualityScore}%`}
        icon={<CheckCircle className="w-5 h-5 text-primary" />}
        progress={dataQualityScore}
      />
      
      <MetricCard
        title="System Performance"
        value="Optimal"
        icon={<Activity className="w-5 h-5 text-primary" />}
        change="+5%"
      />
    </div>
  );
}
