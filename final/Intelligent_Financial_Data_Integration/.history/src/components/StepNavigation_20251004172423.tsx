import React from 'react';
import { Button } from './ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface StepNavigationProps {
  currentStep: string;
  onPrevious: () => void;
  onNext: () => void;
  canGoNext: boolean;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export function StepNavigation({ 
  currentStep, 
  onPrevious, 
  onNext, 
  canGoNext, 
  isFirstStep, 
  isLastStep 
}: StepNavigationProps) {
  return (
    <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-700/30">
      <Button
        variant="outline"
        onClick={onPrevious}
        disabled={isFirstStep}
        className="flex items-center gap-2"
      >
        <ChevronLeft className="w-4 h-4" />
        Back
      </Button>
      
      <div className="text-sm text-muted-foreground">
        Step {getStepNumber(currentStep)} of 4
      </div>
      
      <Button
        onClick={onNext}
        disabled={!canGoNext}
        className="flex items-center gap-2"
      >
        {isLastStep ? 'Complete' : 'Next'}
        {!isLastStep && <ChevronRight className="w-4 h-4" />}
      </Button>
    </div>
  );
}

function getStepNumber(step: string): number {
  const stepMap: Record<string, number> = {
    'upload': 1,
    'mapping': 2,
    'conflicts': 3,
    'results': 4
  };
  return stepMap[step] || 1;
}
