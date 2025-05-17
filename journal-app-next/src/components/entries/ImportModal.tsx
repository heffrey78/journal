'use client';

import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import {
  AlertDialog as Dialog,
  AlertDialogContent as DialogContent,
  AlertDialogDescription as DialogDescription,
  AlertDialogFooter as DialogFooter,
  AlertDialogHeader as DialogHeader,
  AlertDialogTitle as DialogTitle,
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { entriesApi } from '@/lib/api';
import { ImportResult } from '@/lib/types';
import { Folder, FileUp, AlertCircle, Check } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete?: () => void;
}

export function ImportModal({ isOpen, onClose, onImportComplete }: ImportModalProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [folder, setFolder] = useState<string>('');
  const [customTitle, setCustomTitle] = useState<string>('');
  const [useFileDates, setUseFileDates] = useState<boolean>(true);
  const [isImporting, setIsImporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [importResults, setImportResults] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      // Convert FileList to array
      const filesArray = Array.from(e.target.files);
      setFiles(prevFiles => [...prevFiles, ...filesArray]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const filesArray = Array.from(e.dataTransfer.files);
      setFiles(prevFiles => [...prevFiles, ...filesArray]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const clearForm = () => {
    setFiles([]);
    setTags([]);
    setFolder('');
    setCustomTitle('');
    setUseFileDates(true);
    setImportResults(null);
    setError(null);
    setProgress(0);
  };

  const handleClose = () => {
    clearForm();
    onClose();
  };

  const startImport = async () => {
    if (files.length === 0) {
      setError('Please select at least one file to import');
      return;
    }

    try {
      setIsImporting(true);
      setError(null);
      setProgress(0);

      // Start progress animation
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          const increment = Math.random() * 10;
          const newValue = prev + increment;
          // Cap at 90% until we get the actual result
          return newValue >= 90 ? 90 : newValue;
        });
      }, 300);

      // Perform the import
      const result = await entriesApi.importFiles(files, {
        tags: tags.length > 0 ? tags : undefined,
        folder: folder.trim() || undefined,
        useFileDates: useFileDates,
        customTitle: customTitle.trim() || undefined
      });

      // Import complete
      clearInterval(progressInterval);
      setProgress(100);
      setImportResults(result);

      // Show message in the UI instead of toast
      console.log('Import Complete', `Successfully imported ${result.successful} of ${result.total} files.`);

      // Trigger callback
      if (onImportComplete) {
        onImportComplete();
      }

    } catch (err) {
      const progressInterval = window.setInterval(() => {});
      clearInterval(progressInterval - 1);
      setProgress(0);

      if (err instanceof Error) {
        setError(`Import failed: ${err.message}`);
      } else {
        setError('Import failed due to an unknown error');
      }

      // Show error message in the UI instead of toast
      console.error('Import Failed', 'There was an error importing your files.');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Import Documents</DialogTitle>
          <DialogDescription>
            Import documents as journal entries. Supported formats include text and markdown files.
          </DialogDescription>
        </DialogHeader>

        {!importResults ? (
          <>
            {/* File Selection Area */}
            <div
              className="border-2 border-dashed rounded-md p-4 text-center cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-900"
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                multiple
                className="hidden"
              />
              <FileUp className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                Click to select files or drag and drop
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                You can select multiple files
              </p>
            </div>

            {/* Selected Files List */}
            {files.length > 0 && (
              <div className="mt-2">
                <span className="text-sm font-medium">Selected Files ({files.length})</span>
                <div className="mt-1 max-h-32 overflow-auto">
                  {files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between py-1">
                      <span className="text-sm truncate">{file.name}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeFile(index);
                        }}
                      >
                        &times;
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tags Input */}
            <div className="mt-4">
              <span className="text-sm font-medium">Tags (optional)</span>
              <Input
                type="text"
                placeholder="Add tags separated by commas"
                value={tags.join(", ")}
                onChange={(e) => setTags(e.target.value.split(",").map(tag => tag.trim()).filter(Boolean))}
                className="mt-1"
              />
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {tags.map((tag, index) => (
                    <div key={index} className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded-md text-sm flex items-center gap-1">
                      {tag}
                      <button
                        type="button"
                        onClick={() => setTags(tags.filter((_, i) => i !== index))}
                        className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                      >
                        &times;
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Folder Input */}
            <div className="mt-4">
              <span className="text-sm font-medium">Folder (optional)</span>
              <div className="flex mt-1">
                <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 dark:bg-gray-800 dark:border-gray-700 text-gray-500 sm:text-sm">
                  <Folder className="h-4 w-4" />
                </span>
                <Input
                  id="folder"
                  type="text"
                  placeholder="e.g., projects/work"
                  value={folder}
                  onChange={(e) => setFolder(e.target.value)}
                  className="rounded-l-none"
                />
              </div>
            </div>

            {/* Custom Title Input */}
            <div className="mt-4">
              <span className="text-sm font-medium">Title (optional)</span>
              <Input
                id="customTitle"
                type="text"
                placeholder="Custom title for journal entries"
                value={customTitle}
                onChange={(e) => setCustomTitle(e.target.value)}
                className="mt-1"
              />
              {files.length > 1 && customTitle && (
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  For multiple files, each entry will be titled: {customTitle} - YYYY/MM/DD
                </p>
              )}
            </div>

            {/* Use File Dates Option */}
            <div className="mt-4 flex items-center">
              <input
                type="checkbox"
                id="useFileDates"
                checked={useFileDates}
                onChange={(e) => setUseFileDates(e.target.checked)}
                className="mr-2 h-4 w-4"
              />
              <label htmlFor="useFileDates" className="text-sm">
                Use file creation dates for journal entries
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Progress Bar */}
            {isImporting && (
              <div className="mt-4">
                <span className="text-sm font-medium">Importing...</span>
                <div className="w-full bg-gray-200 rounded-full h-2.5 mt-1">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>
            )}

            <DialogFooter className="mt-4">
              <Button variant="outline" onClick={handleClose} disabled={isImporting}>
                Cancel
              </Button>
              <Button onClick={startImport} disabled={isImporting || files.length === 0}>
                {isImporting ? 'Importing...' : 'Import'}
              </Button>
            </DialogFooter>
          </>
        ) : (
          /* Import Results */
          <div className="py-4">
            <div className="flex items-center justify-center mb-4">
              <div className="rounded-full bg-green-100 dark:bg-green-900 p-3">
                <Check className="h-6 w-6 text-green-600 dark:text-green-300" />
              </div>
            </div>

            <h3 className="text-center text-lg font-medium">Import Complete</h3>
            <p className="text-center text-gray-500 dark:text-gray-400 mt-1">
              Successfully imported {importResults.successful} of {importResults.total} files.
            </p>

            {importResults.failed > 0 && (
              <div className="mt-4">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {importResults.failed} file(s) failed to import
                  </AlertDescription>
                </Alert>

                <div className="mt-2 max-h-40 overflow-auto border rounded-md p-2">
                  {importResults.failures.map((failure: { filename: string; error: string }, index: number) => (
                    <div key={index} className="text-sm py-1">
                      <span className="font-medium">{failure.filename}: </span>
                      <span className="text-red-600 dark:text-red-400">{failure.error}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-6 flex justify-center">
              <Button onClick={handleClose}>Done</Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
