import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { X, Plus, Palette, Settings } from 'lucide-react';

interface AddTabDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAddTab: (tabData: CustomTab) => void;
}

export interface CustomTab {
  id: string;
  label: string;
  description?: string;
  color: string;
  icon?: string;
  createdAt: Date;
}

const predefinedColors = [
  '#3B82F6', // Blue
  '#10B981', // Green
  '#F59E0B', // Yellow
  '#EF4444', // Red
  '#8B5CF6', // Purple
  '#06B6D4', // Cyan
  '#F97316', // Orange
  '#84CC16', // Lime
];

export function AddTabDialog({ isOpen, onClose, onAddTab }: AddTabDialogProps) {
  const [label, setLabel] = useState('');
  const [description, setDescription] = useState('');
  const [selectedColor, setSelectedColor] = useState(predefinedColors[0]);
  const [customColor, setCustomColor] = useState('');
  const [useCustomColor, setUseCustomColor] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!label.trim()) return;

    const newTab: CustomTab = {
      id: `custom-${Date.now()}`,
      label: label.trim(),
      description: description.trim() || undefined,
      color: useCustomColor ? customColor : selectedColor,
      createdAt: new Date(),
    };

    onAddTab(newTab);
    setLabel('');
    setDescription('');
    setSelectedColor(predefinedColors[0]);
    setCustomColor('');
    setUseCustomColor(false);
    onClose();
  };

  const handleClose = () => {
    setLabel('');
    setDescription('');
    setSelectedColor(predefinedColors[0]);
    setCustomColor('');
    setUseCustomColor(false);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="w-5 h-5" />
            Add New Tab
          </DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="tab-label">Tab Name</Label>
            <Input
              id="tab-label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Enter tab name..."
              required
              maxLength={20}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="tab-description">Description (Optional)</Label>
            <Textarea
              id="tab-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter tab description..."
              maxLength={100}
              rows={2}
            />
          </div>

          <div className="space-y-3">
            <Label className="flex items-center gap-2">
              <Palette className="w-4 h-4" />
              Tab Color
            </Label>
            
            <div className="grid grid-cols-4 gap-2">
              {predefinedColors.map((color) => (
                <button
                  key={color}
                  type="button"
                  className={`w-8 h-8 rounded-full border-2 transition-all ${
                    selectedColor === color && !useCustomColor
                      ? 'border-white scale-110'
                      : 'border-gray-300 hover:scale-105'
                  }`}
                  style={{ backgroundColor: color }}
                  onClick={() => {
                    setSelectedColor(color);
                    setUseCustomColor(false);
                  }}
                />
              ))}
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="custom-color"
                checked={useCustomColor}
                onChange={(e) => setUseCustomColor(e.target.checked)}
                className="rounded"
              />
              <Label htmlFor="custom-color" className="text-sm">
                Use custom color
              </Label>
            </div>

            {useCustomColor && (
              <div className="flex items-center gap-2">
                <Input
                  type="color"
                  value={customColor}
                  onChange={(e) => setCustomColor(e.target.value)}
                  className="w-12 h-8 p-1"
                />
                <Input
                  type="text"
                  value={customColor}
                  onChange={(e) => setCustomColor(e.target.value)}
                  placeholder="#000000"
                  className="flex-1"
                />
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={!label.trim()}>
              <Plus className="w-4 h-4 mr-2" />
              Add Tab
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
