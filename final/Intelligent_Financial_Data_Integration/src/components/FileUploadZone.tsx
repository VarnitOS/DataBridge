import { Upload, FileSpreadsheet, X } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";

interface FileUploadZoneProps {
  label: string;
  file: File | null;
  onFileSelect: (file: File | null) => void;
  disabled?: boolean;
  compact?: boolean;
}

export function FileUploadZone({ label, file, onFileSelect, disabled, compact = false }: FileUploadZoneProps) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      onFileSelect(selectedFile);
    }
  };

  const handleRemove = () => {
    onFileSelect(null);
  };

  if (compact) {
    return (
      <div className="space-y-0.5">
        <label className="block text-[9px] text-muted-foreground font-medium">{label}</label>
        <Card className="p-1.5 border border-dashed h-12">
          {!file ? (
            <label className="cursor-pointer block h-full">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
                disabled={disabled}
              />
              <div className="flex items-center gap-1 h-full">
                <div className="p-0.5 bg-primary/10 rounded flex-shrink-0">
                  <Upload className="w-2.5 h-2.5 text-primary" />
                </div>
                <div className="text-left flex-1">
                  <p className="text-[9px] text-foreground leading-tight">Drop/click</p>
                  <p className="text-[8px] text-muted-foreground leading-tight">CSV</p>
                </div>
              </div>
            </label>
          ) : (
            <div className="flex items-center justify-between gap-1 h-full">
              <div className="flex items-center gap-1 flex-1 min-w-0">
                <div className="p-0.5 bg-primary/10 rounded flex-shrink-0">
                  <FileSpreadsheet className="w-2.5 h-2.5 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[9px] text-foreground truncate leading-tight">{file.name}</p>
                  <p className="text-[8px] text-muted-foreground leading-tight">{(file.size / 1024).toFixed(1)}KB</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRemove}
                disabled={disabled}
                className="h-4 w-4 p-0 flex-shrink-0"
              >
                <X className="w-2 h-2" />
              </Button>
            </div>
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <label className="block text-muted-foreground">{label}</label>
      <Card className="p-6 border-2 border-dashed">
        {!file ? (
          <label className="cursor-pointer block">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
              disabled={disabled}
            />
            <div className="flex flex-col items-center gap-3 py-4">
              <div className="p-3 bg-primary/10 rounded-full">
                <Upload className="w-6 h-6 text-primary" />
              </div>
              <div className="text-center">
                <p className="text-foreground">Drop CSV file here or click to browse</p>
                <p className="text-muted-foreground mt-1">Supports .csv files only</p>
              </div>
            </div>
          </label>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <FileSpreadsheet className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-foreground">{file.name}</p>
                <p className="text-muted-foreground">{(file.size / 1024).toFixed(2)} KB</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemove}
              disabled={disabled}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
