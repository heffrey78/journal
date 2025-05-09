import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition, RadioGroup } from '@headlessui/react';
import { XMarkIcon, PencilSquareIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { batchAnalysisApi } from '@/lib/api';
import type { BatchAnalysisRequest } from '@/lib/types';

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
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 p-6 text-left align-middle shadow-xl transition-all">
                <Dialog.Title
                  as="h3"
                  className="text-lg font-medium leading-6 text-gray-900 dark:text-white flex justify-between items-center"
                >
                  <span>Analyze {entryIds.length} {entryIds.length === 1 ? 'Entry' : 'Entries'}</span>
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-500"
                    onClick={onClose}
                  >
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  </button>
                </Dialog.Title>

                <div className="mt-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Analyze multiple entries together to identify patterns, themes, and insights.
                  </p>
                </div>

                {error && (
                  <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3 rounded-md">
                    <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
                  </div>
                )}

                <div className="mt-6 space-y-6">
                  {/* Analysis Title */}
                  <div>
                    <label htmlFor="analysis-title" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Analysis Title
                    </label>
                    <div className="mt-1 relative rounded-md shadow-sm">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <PencilSquareIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                      </div>
                      <input
                        type="text"
                        id="analysis-title"
                        className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 sm:text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
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
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Analysis Type</h4>
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
                                  ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                                  : 'border-gray-200 dark:border-gray-700'
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
                                        checked ? 'text-blue-900 dark:text-blue-300' : 'text-gray-900 dark:text-white'
                                      }`}
                                    >
                                      {promptType.name}
                                    </RadioGroup.Label>
                                    <RadioGroup.Description
                                      as="span"
                                      className={`inline ${
                                        checked ? 'text-blue-700 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
                                      }`}
                                    >
                                      <span>{promptType.description}</span>
                                    </RadioGroup.Description>
                                  </div>
                                </div>
                                <div className={`shrink-0 text-white ${checked ? 'text-blue-600' : 'invisible'}`}>
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

                <div className="mt-8 flex justify-end">
                  <button
                    type="button"
                    className="mr-2 inline-flex justify-center rounded-md border border-transparent bg-gray-200 dark:bg-gray-700 px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-2"
                    onClick={onClose}
                    disabled={loading}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:bg-blue-400 disabled:cursor-not-allowed"
                    onClick={handleAnalyze}
                    disabled={loading || !selectedPromptType}
                  >
                    {loading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </>
                    ) : (
                      'Analyze Entries'
                    )}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
