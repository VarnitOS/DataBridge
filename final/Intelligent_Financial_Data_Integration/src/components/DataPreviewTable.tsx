import { Card } from "./ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Badge } from "./ui/badge";
import { Database } from "lucide-react";

interface DataPreviewTableProps {
  title: string;
  data: Record<string, any>[];
  variant?: 'source' | 'target' | 'merged';
}

export function DataPreviewTable({ title, data, variant = 'merged' }: DataPreviewTableProps) {
  if (data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const variantColors = {
    source: 'bg-blue-500/10 border-blue-500/20',
    target: 'bg-green-500/10 border-green-500/20',
    merged: 'bg-purple-500/10 border-purple-500/20'
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Database className="w-5 h-5 text-primary" />
          <h3>{title}</h3>
        </div>
        <Badge variant="outline">{data.length} rows</Badge>
      </div>
      
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto max-h-80 overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((column) => (
                  <TableHead key={column} className="whitespace-nowrap">
                    <div className={`px-2 py-1 rounded-md inline-block ${variantColors[variant]}`}>
                      {column}
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.slice(0, 10).map((row, index) => (
                <TableRow key={index}>
                  {columns.map((column) => (
                    <TableCell key={column} className="whitespace-nowrap">
                      {row[column]}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </Card>
  );
}
