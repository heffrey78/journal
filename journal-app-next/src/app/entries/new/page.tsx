'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import MainLayout from '@/components/layout/MainLayout';
import AdvancedMarkdownEditor from '@/components/markdown/AdvancedMarkdownEditor';
import { Button } from '@/components/ui/button';
import { entriesApi, organizationApi } from '@/lib/api';
import { CreateJournalEntryInput } from '@/lib/types';
import { FolderIcon } from '@heroicons/react/24/outline';
import Container from '@/components/layout/Container';
import ContentPadding from '@/components/layout/ContentPadding';

export default function NewEntryPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const folderParam = searchParams.get('folder');

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [folder, setFolder] = useState<string | null>(folderParam);
  const [availableFolders, setAvailableFolders] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdEntryId, setCreatedEntryId] = useState<string | null>(null);
  const [showFolderSelector, setShowFolderSelector] = useState(false);

  // Fetch available folders when component mounts
  useEffect(() => {
    const fetchFolders = async () => {
      try {
        const folders = await organizationApi.getFolders();
        setAvailableFolders(folders);
      } catch (err) {
        console.error('Failed to fetch folders:', err);
        // Don't set error state here, as this is not critical
      }
    };

    fetchFolders();
  }, []);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const tagsArray = tags
        .split(',')
        .map((tag) => tag.trim())
        .filter((tag) => tag);

      const newEntry: CreateJournalEntryInput = {
        title: title || 'Untitled Entry',
        content,
        tags: tagsArray.length > 0 ? tagsArray : undefined,
        folder: folder || undefined, // Include folder if selected
      };

      const createdEntry = await entriesApi.createEntry(newEntry);
      setCreatedEntryId(createdEntry.id);

      // Optional: wait a brief moment before redirecting
      setTimeout(() => {
        if (folder) {
          // If created from a folder, redirect back to that folder
          router.push(`/folders/${encodeURIComponent(folder)}`);
        } else {
          // Otherwise go to the new entry
          router.push(`/entries/${createdEntry.id}`);
        }
      }, 1000);
    } catch (err) {
      console.error('Failed to create entry:', err);
      setError('Failed to create entry. Please try again.');
      setIsSubmitting(false);
    }
  };

  const toggleFolderSelector = () => {
    setShowFolderSelector(!showFolderSelector);
  };

  const selectFolder = (selectedFolder: string | null) => {
    setFolder(selectedFolder);
    setShowFolderSelector(false);
  };

  return (
    <MainLayout>
      <Container maxWidth="4xl" className="mx-auto">
        <ContentPadding size="md">
          <div className="mb-6 flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">New Journal Entry</h1>

            {folder && (
              <div className="flex items-center px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full text-sm">
                <FolderIcon className="h-4 w-4 mr-1.5" />
                <span>In folder: {folder}</span>
              </div>
            )}
          </div>

          {error && (
            <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-300 p-4 rounded-md mb-6">
              {error}
            </div>
          )}

          {createdEntryId && (
            <div className="bg-green-100 dark:bg-green-900/20 border border-green-200 dark:border-green-900/30 text-green-700 dark:text-green-300 p-4 rounded-md mb-6">
              Entry created successfully! Redirecting...
            </div>
          )}

          <form 
            onSubmit={(e) => {
              e.preventDefault(); // Prevent default form submission
              handleSubmit();
            }} 
            className="space-y-6"
          >
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Title
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Entry title (optional)"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Content
              </label>
              <div className="prose-wrapper">
                <AdvancedMarkdownEditor
                  value={content}
                  onChange={setContent}
                  placeholder="Write your journal entry here..."
                  autofocus
                  entryId={createdEntryId ?? undefined}
                  height="600px"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-4">
              <div className="flex-1">
                <label htmlFor="tags" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tags (comma separated)
                </label>
                <input
                  type="text"
                  id="tags"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="e.g. personal, work, ideas"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex-1 relative">
                <label htmlFor="folder" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Folder
                </label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={toggleFolderSelector}
                    className="w-full flex justify-between items-center px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-left text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <div className="flex items-center">
                      <FolderIcon className="h-4 w-4 text-gray-400 mr-2" />
                      <span>{folder || 'Select folder (optional)'}</span>
                    </div>
                    <svg
                      className={`h-5 w-5 text-gray-400 transform ${showFolderSelector ? 'rotate-180' : ''}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {showFolderSelector && (
                    <div className="absolute z-10 mt-1 w-full max-h-60 overflow-auto bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700">
                      <div
                        className="px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-200 dark:border-gray-700"
                        onClick={() => selectFolder(null)}
                      >
                        <span className="italic text-gray-500 dark:text-gray-400">No folder</span>
                      </div>

                      {availableFolders.map((f) => (
                        <div
                          key={f}
                          className="px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer flex items-center"
                          onClick={() => selectFolder(f)}
                        >
                          <FolderIcon className="h-4 w-4 text-gray-400 mr-2" />
                          <span>{f}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                isLoading={isSubmitting}
                disabled={!content.trim() || !!createdEntryId}
              >
                Save Entry
              </Button>
            </div>
          </form>
        </ContentPadding>
      </Container>
    </MainLayout>
  );
}
