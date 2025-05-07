'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import MainLayout from '@/components/layout/MainLayout';
import EntryList from '@/components/entries/EntryList';
import Link from 'next/link';
import { organizationApi } from '@/lib/api';
import { JournalEntry } from '@/lib/api';

export default function CalendarDayPage() {
  const params = useParams();
  const dateStr = params.date as string; // Format: YYYY-MM-DD
  const router = useRouter();
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Parse the date from the URL parameter
  const displayDate = new Date(`${dateStr}T00:00:00`);
  const isValidDate = !isNaN(displayDate.getTime());

  useEffect(() => {
    // If date is invalid, redirect to calendar
    if (!isValidDate) {
      router.push('/calendar');
      return;
    }

    const fetchEntriesForDate = async () => {
      try {
        setLoading(true);
        const data = await organizationApi.getEntriesByDate(dateStr);
        setEntries(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch entries for date:', err);
        setError('Failed to load entries for this date. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchEntriesForDate();
  }, [dateStr, isValidDate, router]);

  // Format date as "Month Day, Year" (e.g., "May 5, 2025")
  const formattedDate = isValidDate
    ? displayDate.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      })
    : 'Invalid Date';

  // Navigate to previous day
  const prevDay = () => {
    if (!isValidDate) return;

    const prevDate = new Date(displayDate);
    prevDate.setDate(displayDate.getDate() - 1);

    const prevDateStr = prevDate.toISOString().split('T')[0];
    router.push(`/calendar/${prevDateStr}`);
  };

  // Navigate to next day
  const nextDay = () => {
    if (!isValidDate) return;

    const nextDate = new Date(displayDate);
    nextDate.setDate(displayDate.getDate() + 1);

    const nextDateStr = nextDate.toISOString().split('T')[0];
    router.push(`/calendar/${nextDateStr}`);
  };

  return (
    <MainLayout>
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <Link href="/calendar" className="mr-4">
            <button className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
            </button>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {formattedDate}
          </h1>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={prevDay}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="Previous day"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path>
            </svg>
          </button>
          <button
            onClick={nextDay}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="Next day"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
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
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">
            No entries for {formattedDate}
          </h3>
          <p className="mt-1 text-gray-500 dark:text-gray-400">
            Create a new entry for this date.
          </p>
          <div className="mt-6">
            <Link
              href="/entries/new"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              Create Entry
            </Link>
          </div>
        </div>
      ) : (
        <EntryList entries={entries} />
      )}
    </MainLayout>
  );
}
