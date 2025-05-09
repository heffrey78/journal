import { useState, useEffect } from 'react';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction
} from '@/components/ui/alert-dialog';
import { RadioGroup } from '@headlessui/react';
import { XMarkIcon, PencilSquareIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { batchAnalysisApi } from '@/lib/api';
import type { BatchAnalysisRequest } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';

interface BatchAnalysisDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAnalyze: (request: BatchAnalysisRequest) => Promise<void>;
  entryIds: string[];
  title?: string;
}

type PromptType = {
  id: string;
  name: string;
  description: string;
};

export default function BatchAnalysisDialog({
  isOpen,
  onClose,
  onAnalyze,
  entryIds,
  title: initialTitle
}: BatchAnalysisDialogProps) {
  const [title, setTitle] = useState(initialTitle || '');
  const [promptTypes, setPromptTypes] = useState<PromptType[]>([]);
  const [selectedPromptType, setSelectedPromptType] = useState<string>('weekly');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset state when dialog opens
  useEffect(() => {
    if (isOpen) {
      setTitle(initialTitle || '');
      setSelectedPromptType('weekly');
      setError(null);

      // Get available prompt types
      setPromptTypes(batchAnalysisApi.getAvailablePromptTypes());
    }
  }, [isOpen, initialTitle]);

  // Generate default title if not provided
  useEffect(() => {
    if (!title && isOpen) {
      // Get prompt type name
      const promptType = promptTypes.find(pt => pt.id === selectedPromptType)?.name || 'Analysis';

      // Generate default title based on entry count and prompt type
      const defaultTitle = entryIds.length === 1
        ? `Entry Analysis`
        : `${promptType} of ${entryIds.length} Entries`;

      setTitle(defaultTitle);
    }
  }, [title, isOpen, entryIds.length, selectedPromptType, promptTypes]);

  // Handle analysis request
  const handleAnalyze = async () => {
    if (!entryIds.length) {
      setError('No entries selected for analysis.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Prepare request
      const request: BatchAnalysisRequest = {
        entry_ids: entryIds,
        title: title,
        prompt_type: selectedPromptType
      };

      await onAnalyze(request);
      onClose();
    } catch (err) {
      console.error('Failed to analyze entries:', err);
      setError('Failed to analyze entries. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <div className="flex justify-between items-center">
            <AlertDialogTitle>
              Analyze {entryIds.length} {entryIds.length === 1 ? 'Entry' : 'Entries'}
            </AlertDialogTitle>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={onClose}
            >
              <XMarkIcon className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
          <AlertDialogDescription>
            Analyze multiple entries together to identify patterns, themes, and insights.
          </AlertDialogDescription>
        </AlertDialogHeader>

        {error && (
          <Alert variant="destructive" className="mt-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="mt-6 space-y-6">
          {/* Analysis Title */}
          <div>
            <label htmlFor="analysis-title" className="block text-sm font-medium text-muted-foreground">
              Analysis Title
            </label>
            <div className="mt-1 relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <PencilSquareIcon className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
              </div>
              <Input
                type="text"
                id="analysis-title"
                className="pl-10"
                placeholder="Analysis Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          {/* Analysis Type */}
          <div>
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-foreground">Analysis Type</h4>
            </div>

            <RadioGroup value={selectedPromptType} onChange={setSelectedPromptType} className="mt-2">
              <RadioGroup.Label className="sr-only">Choose an analysis type</RadioGroup.Label>
              <div className="space-y-2">
                {promptTypes.map((promptType) => (
                  <RadioGroup.Option
                    key={promptType.id}
                    value={promptType.id}
                    className={({ checked }) =>
                      `${
                        checked
                          ? 'bg-primary/10 border-primary/20'
                          : 'border-input bg-background'
                      }
                      relative flex cursor-pointer rounded-lg border p-4 focus:outline-none`
                    }
                    disabled={loading}
                  >
                    {({ active, checked }) => (
                      <div className="flex w-full items-center justify-between">
                        <div className="flex items-center">
                          <div className="text-sm">
                            <RadioGroup.Label
                              as="p"
                              className={`font-medium ${
                                checked ? 'text-primary' : 'text-foreground'
                              }`}
                            >
                              {promptType.name}
                            </RadioGroup.Label>
                            <RadioGroup.Description
                              as="span"
                              className={`inline ${
                                checked ? 'text-primary/70' : 'text-muted-foreground'
                              }`}
                            >
                              <span>{promptType.description}</span>
                            </RadioGroup.Description>
                          </div>
                        </div>
                        <div className={`shrink-0 text-primary ${checked ? '' : 'invisible'}`}>
                          <DocumentTextIcon className="h-5 w-5" />
                        </div>
                      </div>
                    )}
                  </RadioGroup.Option>
                ))}
              </div>
            </RadioGroup>
          </div>
        </div>

        <AlertDialogFooter className="mt-6">
          <AlertDialogCancel asChild>
            <Button variant="outline" disabled={loading} onClick={onClose}>
              Cancel
            </Button>
          </AlertDialogCancel>
          <AlertDialogAction asChild>
            <Button
              onClick={handleAnalyze}
              disabled={loading || !selectedPromptType}
              isLoading={loading}
            >
              Analyze Entries
            </Button>
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
