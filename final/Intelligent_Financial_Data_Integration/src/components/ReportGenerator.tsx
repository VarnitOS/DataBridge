import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Download, FileText, BarChart3, Table } from "lucide-react";

interface ReportGeneratorProps {
  projectName: string;
  recordsProcessed: number;
  conflictsResolved: number;
  dataQualityScore: number;
  mappings: any[];
}

export function ReportGenerator({
  projectName,
  recordsProcessed,
  conflictsResolved,
  dataQualityScore,
  mappings
}: ReportGeneratorProps) {
  const handleExportPDF = () => {
    console.log('Exporting PDF report...');
  };

  const handleExportExcel = () => {
    console.log('Exporting Excel report...');
  };

  const handleExportPowerBI = () => {
    console.log('Exporting to Power BI...');
  };

  const handleExportTableau = () => {
    console.log('Exporting to Tableau...');
  };

  return (
    <Card className="p-6">
      <h2 className="mb-6">Integration Report</h2>

      <div className="space-y-6">
        {/* Report Preview */}
        <div className="border rounded-lg p-6 bg-muted/20">
          <div className="mb-6">
            <h3 className="mb-2">Executive Summary</h3>
            <p className="text-muted-foreground">
              Data Integration Report for {projectName}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-4 bg-background rounded-lg border">
              <p className="text-muted-foreground mb-1">Records Processed</p>
              <h3>{recordsProcessed.toLocaleString()}</h3>
            </div>
            <div className="p-4 bg-background rounded-lg border">
              <p className="text-muted-foreground mb-1">Data Quality Score</p>
              <h3>{dataQualityScore}%</h3>
            </div>
            <div className="p-4 bg-background rounded-lg border">
              <p className="text-muted-foreground mb-1">Conflicts Resolved</p>
              <h3>{conflictsResolved}</h3>
            </div>
            <div className="p-4 bg-background rounded-lg border">
              <p className="text-muted-foreground mb-1">Field Mappings</p>
              <h3>{mappings.length}</h3>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <h4 className="mb-2">Schema Mappings</h4>
              <div className="space-y-2">
                {mappings.slice(0, 3).map((mapping, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-2 bg-background rounded border text-sm">
                    <Badge variant="outline" className="text-xs">
                      {(mapping.confidence * 100).toFixed(0)}%
                    </Badge>
                    <span className="text-blue-600 dark:text-blue-400">{mapping.sourceField}</span>
                    <span>→</span>
                    <span className="text-green-600 dark:text-green-400">{mapping.targetField}</span>
                  </div>
                ))}
                {mappings.length > 3 && (
                  <p className="text-muted-foreground text-sm">
                    + {mappings.length - 3} more mappings
                  </p>
                )}
              </div>
            </div>

            <div>
              <h4 className="mb-2">Gemini AI Insights</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>• High confidence mapping accuracy (avg. {((mappings.reduce((sum, m) => sum + m.confidence, 0) / mappings.length) * 100).toFixed(0)}%)</li>
                <li>• No critical data type mismatches detected</li>
                <li>• Recommended normalization applied for date formats</li>
                <li>• Duplicate detection rate: 0.5%</li>
              </ul>
            </div>

            <div>
              <h4 className="mb-2">Validation Checks</h4>
              <div className="space-y-2">
                {[
                  { check: 'Data Completeness', status: 'Passed', score: 98 },
                  { check: 'Format Consistency', status: 'Passed', score: 95 },
                  { check: 'Referential Integrity', status: 'Passed', score: 97 },
                  { check: 'Duplicate Detection', status: 'Warning', score: 92 },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-background rounded border text-sm">
                    <span>{item.check}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">{item.score}%</span>
                      <Badge variant={item.status === 'Passed' ? 'default' : 'outline'}>
                        {item.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Export Options */}
        <div>
          <h3 className="mb-4">Export Options</h3>
          <div className="grid grid-cols-2 gap-3">
            <Button onClick={handleExportPDF} variant="outline" className="justify-start">
              <FileText className="w-4 h-4 mr-2" />
              Download PDF
            </Button>
            <Button onClick={handleExportExcel} variant="outline" className="justify-start">
              <Table className="w-4 h-4 mr-2" />
              Export to Excel
            </Button>
            <Button onClick={handleExportPowerBI} variant="outline" className="justify-start">
              <BarChart3 className="w-4 h-4 mr-2" />
              Send to Power BI
            </Button>
            <Button onClick={handleExportTableau} variant="outline" className="justify-start">
              <BarChart3 className="w-4 h-4 mr-2" />
              Send to Tableau
            </Button>
          </div>
        </div>

        <div className="bg-primary/5 rounded-lg p-4">
          <p className="text-muted-foreground">
            Reports include: Schema mappings, conflict resolutions, Gemini AI explanations, 
            validation checks, and compliance documentation.
          </p>
        </div>
      </div>
    </Card>
  );
}
