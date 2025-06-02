'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import MainLayout from '@/components/layout/MainLayout';
import EntryList from '@/components/entries/EntryList';
import { organizationApi } from '@/lib/api';
import { JournalEntry } from '@/lib/types';
import { PlusIcon } from '@heroicons/react/24/outline';
import { Button, Pagination, Container, ContentPadding } from '@/components/design-system';

export default function FolderPage() {
  const params = useParams();
  const router = useRouter();
  // Ensure params and folder parameter exist
  const folder = params?.folder ? decodeURIComponent(params.folder as string) : '';
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const entriesPerPage = 10;

  useEffect(() => {
    const fetchEntriesByFolder = async () => {
      // Don't fetch if folder is empty
      if (!folder) {
        setError('Invalid folder name');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await organizationApi.getEntriesByFolder(folder, {
          limit: entriesPerPage,
          offset: currentPage * entriesPerPage
        });
        setEntries(data);
        // If we get fewer results than the requested limit, there are no more entries
        setHasMore(data.length === entriesPerPage);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch entries:', err);
        setError('Failed to load entries for this folder. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchEntriesByFolder();
  }, [folder, currentPage]);

  // Navigate to create entry page with folder pre-selected
  const handleCreateEntry = () => {
    router.push(`/entries/new?folder=${encodeURIComponent(folder)}`);
  };

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (hasMore) {
      setCurrentPage(currentPage + 1);
    }
  };

  return (
    <MainLayout>
      <Container maxWidth="4xl" className="mx-auto">
        <ContentPadding size="md">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              <span className="text-gray-500 dark:text-gray-400">Folder: </span>
              {folder}
            </h1>

            {/* Create Entry Button - always visible */}
            <Button onClick={handleCreateEntry} className="flex items-center gap-2">
              <PlusIcon className="h-4 w-4" aria-hidden="true" />
              New Entry
            </Button>
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 my-4">
              <p className="text-red-800 dark:text-red-300">{error}</p>
            </div>
          ) : entries.length === 0 ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
              </svg>
              <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">No entries in this folder</h3>
              <p className="mt-1 text-gray-500 dark:text-gray-400">
                Create a new entry in this folder or move existing entries here.
              </p>
              <div className="mt-6">
                <Button onClick={handleCreateEntry} className="flex items-center gap-2">
                  <PlusIcon className="h-4 w-4" aria-hidden="true" />
                  Create Entry
                </Button>
              </div>
            </div>
          ) : (
            <>
              <EntryList entries={entries} showMoveAction={true} currentFolder={folder} />

              {/* Pagination Controls */}
              <Pagination
                currentPage={currentPage}
                hasMore={hasMore}
                onPrevious={handlePreviousPage}
                onNext={handleNextPage}
                className="mt-6"
              />
            </>
          )}
        </ContentPadding>
      </Container>
    </MainLayout>
  );
}
