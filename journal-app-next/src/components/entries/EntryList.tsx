import React, { useState } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import Card from '@/components/ui/Card';
import { JournalEntry, BatchAnalysisRequest, BatchAnalysis } from '@/lib/types';
import { organizationApi, batchAnalysisApi } from '@/lib/api';
import { useCompatRouter } from '@/lib/routerUtils';
import MoveEntriesDialog from '@/components/dialogs/MoveEntriesDialog';
import BatchAnalysisDialog from '@/components/dialogs/BatchAnalysisDialog';
import { FolderIcon, ArrowsRightLeftIcon, CheckCircleIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import MarkdownRenderer from '@/components/markdown/MarkdownRenderer';

interface EntryListProps {
  entries: JournalEntry[];
  showExcerpt?: boolean;
  showMoveAction?: boolean;
  showAnalysisAction?: boolean;  // New prop for batch analysis
  currentFolder?: string;
  onAnalysisComplete?: (analysis: BatchAnalysis) => void;  // Optional callback when analysis completes
}

const EntryList: React.FC<EntryListProps> = ({
  entries,
  showExcerpt = true,
  showMoveAction = false,
  showAnalysisAction = true,  // Enable by default
  currentFolder,
  onAnalysisComplete
}) => {
  const router = useCompatRouter();
  const [selectedEntries, setSelectedEntries] = useState<string[]>([]);
  const [selectionMode, setSelectionMode] = useState(false);
  const [isMoveDialogOpen, setIsMoveDialogOpen] = useState(false);
  const [isAnalysisDialogOpen, setIsAnalysisDialogOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const getExcerpt = (content: string, maxLength: number = 150) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + '...';
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return format(date, 'MMM d, yyyy h:mm a');
    } catch (e) {
      return dateString;
    }
  };

  // Toggle selection mode
  const toggleSelectionMode = () => {
    if (selectionMode) {
      // Exit selection mode
      setSelectionMode(false);
      setSelectedEntries([]);
    } else {
      // Enter selection mode
      setSelectionMode(true);
    }
  };

  // Toggle entry selection
  const toggleEntrySelection = (entryId: string) => {
    if (selectedEntries.includes(entryId)) {
      setSelectedEntries(selectedEntries.filter(id => id !== entryId));
    } else {
      setSelectedEntries([...selectedEntries, entryId]);
    }
  };

  // Toggle selection of all entries
  const toggleSelectAll = () => {
    if (selectedEntries.length === entries.length) {
      // Deselect all
      setSelectedEntries([]);
    } else {
      // Select all
      setSelectedEntries(entries.map(entry => entry.id));
    }
  };

  // Open move dialog
  const openMoveDialog = () => {
    if (selectedEntries.length > 0) {
      setIsMoveDialogOpen(true);
    }
  };

  // Open batch analysis dialog
  const openAnalysisDialog = () => {
    if (selectedEntries.length > 0) {
      setIsAnalysisDialogOpen(true);
    }
  };

  // Handle move entries
  const handleMoveEntries = async (destinationFolder: string | null) => {
    if (selectedEntries.length === 0) return;

    try {
      setIsProcessing(true);
      // Call API to move entries
      const result = await organizationApi.batchUpdateFolder(selectedEntries, destinationFolder);

      // Show success message
      setStatusMessage({
        text: `Successfully moved ${result.updated_count} entries to ${destinationFolder || 'root level'}`,
        type: 'success'
      });

      // Clear selection and exit selection mode
      setSelectedEntries([]);
      setSelectionMode(false);

      // Auto-hide status message after 3 seconds
      setTimeout(() => {
        setStatusMessage(null);
      }, 3000);

      // Force refresh the current folder after moving entries
      // This would normally be handled through a refresh function passed from the parent
      // But for this implementation, we'll just reload the page
      if (window) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Failed to move entries:', error);
      setStatusMessage({
        text: 'Failed to move entries. Please try again.',
        type: 'error'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle batch analysis
  const handleAnalyzeEntries = async (request: BatchAnalysisRequest) => {
    if (selectedEntries.length === 0) return;

    try {
      setIsProcessing(true);

      // Call API to analyze entries
      const analysis = await batchAnalysisApi.analyzeBatch(request);

      // Show success message
      setStatusMessage({
        text: `Successfully analyzed ${selectedEntries.length} entries`,
        type: 'success'
      });

      // Clear selection and exit selection mode
      setSelectedEntries([]);
      setSelectionMode(false);

      // Auto-hide status message after 3 seconds
      setTimeout(() => {
        setStatusMessage(null);
      }, 3000);

      // If callback provided, call it with the analysis result
      if (onAnalysisComplete) {
        onAnalysisComplete(analysis);
      } else {
        // Navigate to the analysis result page
        router.push(`/analyses/${analysis.id}`);
      }

      return analysis;
    } catch (error) {
      console.error('Failed to analyze entries:', error);
      setStatusMessage({
        text: 'Failed to analyze entries. Please try again.',
        type: 'error'
      });
      throw error;
    } finally {
      setIsProcessing(false);
    }
  };

  if (entries.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 dark:text-gray-400">No entries found.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Action Bar */}
      {(showMoveAction || showAnalysisAction) && (
        <div className="mb-4 flex flex-wrap justify-between items-center gap-2">
          {selectionMode ? (
            <>
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleSelectAll}
                  className="text-sm flex items-center px-3 py-1.5 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {selectedEntries.length === entries.length ? 'Deselect All' : 'Select All'}
                </button>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {selectedEntries.length} selected
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {showAnalysisAction && (
                  <button
                    onClick={openAnalysisDialog}
                    disabled={selectedEntries.length < 2 || isProcessing}
                    className={`flex items-center space-x-1 px-3 py-1.5 text-sm rounded ${
                      selectedEntries.length >= 2
                        ? 'bg-purple-600 text-white hover:bg-purple-700'
                        : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <ChartBarIcon className="h-4 w-4" />
                    <span>Analyze {selectedEntries.length > 0 ? `(${selectedEntries.length})` : ''}</span>
                  </button>
                )}

                {showMoveAction && (
                  <button
                    onClick={openMoveDialog}
                    disabled={selectedEntries.length === 0 || isProcessing}
                    className={`flex items-center space-x-1 px-3 py-1.5 text-sm rounded ${
                      selectedEntries.length > 0
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <FolderIcon className="h-4 w-4" />
                    <span>Move {selectedEntries.length > 0 ? `(${selectedEntries.length})` : ''}</span>
                  </button>
                )}

                <button
                  onClick={toggleSelectionMode}
                  className="flex items-center space-x-1 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <span>Cancel</span>
                </button>
              </div>
            </>
          ) : (
            <div className="ml-auto flex space-x-2">
              {showAnalysisAction && (
                <button
                  onClick={toggleSelectionMode}
                  className="flex items-center space-x-1 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <ChartBarIcon className="h-4 w-4 mr-1" />
                  <span>Analyze Entries</span>
                </button>
              )}

              {showMoveAction && (
                <button
                  onClick={toggleSelectionMode}
                  className="flex items-center space-x-1 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <ArrowsRightLeftIcon className="h-4 w-4 mr-1" />
                  <span>Move Entries</span>
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Status message */}
      {statusMessage && (
        <div className={`mb-4 p-3 rounded-md ${
          statusMessage.type === 'success'
            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-300'
            : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300'
        }`}>
          {statusMessage.text}
        </div>
      )}

      {/* Entry List */}
      <div className="space-y-4">
        {entries.map((entry) => (
          <div key={entry.id} className="relative">
            {selectionMode && (
              <div
                className={`absolute top-0 left-0 w-full h-full z-10 flex items-center justify-end pr-4 bg-black bg-opacity-0 ${
                  selectedEntries.includes(entry.id)
                    ? 'border-2 border-blue-500 rounded-lg'
                    : ''
                }`}
                onClick={() => toggleEntrySelection(entry.id)}
              >
                <div className={`absolute top-3 right-3 h-6 w-6 rounded-full ${
                  selectedEntries.includes(entry.id)
                    ? 'bg-blue-500 text-white'
                    : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-500'
                } flex items-center justify-center`}>
                  {selectedEntries.includes(entry.id) && (
                    <CheckCircleIcon className="h-5 w-5" />
                  )}
                </div>
              </div>
            )}

            <Link
              href={selectionMode ? '#' : `/entries/${entry.id}`}
              onClick={selectionMode ? (e) => {
                e.preventDefault();
                toggleEntrySelection(entry.id);
              } : undefined}
            >
              <Card clickable={!selectionMode} className="hover:border-blue-300 transition-colors">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {entry.title || 'Untitled Entry'}
                  </h3>
                  {entry.favorite && (
                    <span className="text-yellow-500">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {formatDate(entry.created_at)}
                </div>
                {showExcerpt && (
                  <div className="mt-2 text-gray-600 dark:text-gray-300 excerpt-container">
                    <MarkdownRenderer
                      content={getExcerpt(entry.content)}
                      className="excerpt-markdown"
                    />
                  </div>
                )}
                <div className="mt-3 flex flex-wrap gap-2">
                  {entry.folder && (
                    <span className="flex items-center bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-xs px-2 py-1 rounded-full">
                      <FolderIcon className="h-3 w-3 mr-1" />
                      {entry.folder}
                    </span>
                  )}
                  {entry.tags && entry.tags.length > 0 && entry.tags.map((tag) => (
                    <span
                      key={tag}
                      className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs px-2 py-1 rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </Card>
            </Link>
          </div>
        ))}
      </div>

      {/* Move dialog */}
      <MoveEntriesDialog
        isOpen={isMoveDialogOpen}
        onClose={() => setIsMoveDialogOpen(false)}
        onMove={handleMoveEntries}
        entryCount={selectedEntries.length}
        currentFolder={currentFolder}
      />

      {/* Batch Analysis dialog */}
      <BatchAnalysisDialog
        isOpen={isAnalysisDialogOpen}
        onClose={() => setIsAnalysisDialogOpen(false)}
        onAnalyze={handleAnalyzeEntries}
        entryIds={selectedEntries}
      />
    </div>
  );
};

export default EntryList;
