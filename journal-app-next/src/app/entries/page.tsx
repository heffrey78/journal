'use client';

import { useState, useEffect } from 'react';
import MainLayout from '@/components/layout/MainLayout';
import EntryList from '@/components/entries/EntryList';
import { Pagination, Container, ContentPadding } from '@/components/design-system';
import { entriesApi } from '@/lib/api';
import { JournalEntry } from '@/lib/types';

export default function EntriesPage() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const entriesPerPage = 10;

  useEffect(() => {
    const fetchEntries = async () => {
      try {
        setLoading(true);
        const data = await entriesApi.getEntries({
          limit: entriesPerPage,
          offset: currentPage * entriesPerPage
        });
        setEntries(data);
        // If we get fewer results than the requested limit, there are no more entries
        setHasMore(data.length === entriesPerPage);
      } catch (err) {
        console.error('Failed to fetch entries:', err);
        setError('Failed to load entries. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchEntries();
  }, [currentPage]);

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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Your Entries</h1>
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-300 p-4 rounded-md">
              {error}
            </div>
          ) : (
            <>
              <EntryList entries={entries} />

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
