'use client';

import { useState, useEffect } from 'react';
import MainLayout from '@/components/layout/MainLayout';
import { organizationApi } from '@/lib/api';
import { JournalEntry } from '@/lib/api';
import Link from 'next/link';
import Container from '@/components/layout/Container';
import ContentPadding from '@/components/layout/ContentPadding';

// Calendar implementation using a grid layout
export default function CalendarPage() {
  const [date, setDate] = useState(new Date());
  const [entries, setEntries] = useState<{[key: string]: JournalEntry[]}>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get days in month
  const getDaysInMonth = (year: number, month: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  // Get first day of month (0 = Sunday, 1 = Monday, etc)
  const getFirstDayOfMonth = (year: number, month: number) => {
    return new Date(year, month, 1).getDay();
  };

  // Format date as YYYY-MM-DD for API
  const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Display format for month and year
  const monthYearDisplay = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  // Previous month
  const prevMonth = () => {
    const newDate = new Date(date);
    newDate.setMonth(date.getMonth() - 1);
    setDate(newDate);
  };

  // Next month
  const nextMonth = () => {
    const newDate = new Date(date);
    newDate.setMonth(date.getMonth() + 1);
    setDate(newDate);
  };

  useEffect(() => {
    // Fetch entries for the current month
    const fetchEntriesForMonth = async () => {
      try {
        setLoading(true);
        setError(null);

        const year = date.getFullYear();
        const month = date.getMonth();
        const daysInMonth = getDaysInMonth(year, month);

        // Fetch entries for each day in the month
        const entriesByDate: {[key: string]: JournalEntry[]} = {};
        const fetchPromises = [];

        for (let day = 1; day <= daysInMonth; day++) {
          const currentDate = new Date(year, month, day);
          const dateStr = formatDate(currentDate);

          fetchPromises.push(
            organizationApi.getEntriesByDate(dateStr).then(entries => {
              if (entries.length > 0) {
                entriesByDate[dateStr] = entries;
              }
            }).catch(error => {
              console.error(`Error fetching entries for ${dateStr}:`, error);
            })
          );
        }

        // Wait for all fetches to complete
        await Promise.all(fetchPromises);
        setEntries(entriesByDate);

      } catch (err) {
        console.error('Failed to fetch entries for calendar:', err);
        setError('Failed to load calendar entries. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchEntriesForMonth();
  }, [date]);

  // Generate calendar grid
  const generateCalendar = () => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);

    const days = [];

    // Add empty cells for days before the first of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-32 border border-gray-200 dark:border-gray-700"></div>);
    }

    // Add cells for each day in the month
    for (let day = 1; day <= daysInMonth; day++) {
      const currentDate = new Date(year, month, day);
      const dateStr = formatDate(currentDate);
      const hasEntries = entries[dateStr] && entries[dateStr].length > 0;
      const isToday = new Date().toDateString() === currentDate.toDateString();

      days.push(
        <div
          key={day}
          className={`h-32 border border-gray-200 dark:border-gray-700 p-2 ${
            isToday ? 'bg-blue-50 dark:bg-blue-900/20' : ''
          }`}
        >
          <div className="flex justify-between items-center mb-1">
            <span className={`text-sm font-medium ${isToday ? 'text-blue-600 dark:text-blue-400' : ''}`}>
              {day}
            </span>
            {hasEntries && (
              <Link
                href={`/calendar/${dateStr}`}
                className="text-xs px-1.5 py-0.5 bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 rounded"
              >
                {entries[dateStr].length}
              </Link>
            )}
          </div>

          {hasEntries && (
            <div className="overflow-y-auto max-h-24">
              {entries[dateStr].slice(0, 2).map(entry => (
                <Link
                  key={entry.id}
                  href={`/entries/${entry.id}`}
                  className="block text-xs truncate hover:text-blue-600 dark:hover:text-blue-400 py-0.5"
                >
                  {entry.title}
                </Link>
              ))}
              {entries[dateStr].length > 2 && (
                <Link
                  href={`/calendar/${dateStr}`}
                  className="block text-xs text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 mt-1"
                >
                  +{entries[dateStr].length - 2} more
                </Link>
              )}
            </div>
          )}
        </div>
      );
    }

    return days;
  };

  return (
    <MainLayout>
      <Container maxWidth="4xl" className="mx-auto">
        <ContentPadding size="md">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Calendar View</h1>
          </div>

          <div className="mb-6 flex justify-between items-center">
            <button
              onClick={prevMonth}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path>
              </svg>
            </button>
            <h2 className="text-xl font-semibold">{monthYearDisplay(date)}</h2>
            <button
              onClick={nextMonth}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 my-4">
              <p className="text-red-800 dark:text-red-300">{error}</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-7 gap-0">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} className="py-2 text-center border-b border-gray-200 dark:border-gray-700 font-medium">
                    {day}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-0">
                {generateCalendar()}
              </div>
            </>
          )}
        </ContentPadding>
      </Container>
    </MainLayout>
  );
}
