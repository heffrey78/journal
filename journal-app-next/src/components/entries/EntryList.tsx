import React from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import Card from '@/components/ui/Card';
import { JournalEntry } from '@/lib/types';

interface EntryListProps {
  entries: JournalEntry[];
  showExcerpt?: boolean;
}

const EntryList: React.FC<EntryListProps> = ({ entries, showExcerpt = true }) => {
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

  if (entries.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 dark:text-gray-400">No entries found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {entries.map((entry) => (
        <Link href={`/entries/${entry.id}`} key={entry.id}>
          <Card clickable className="hover:border-blue-300 transition-colors">
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
              <div className="mt-2 text-gray-600 dark:text-gray-300">
                {getExcerpt(entry.content)}
              </div>
            )}
            {entry.tags && entry.tags.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {entry.tags.map((tag) => (
                  <span
                    key={tag}
                    className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs px-2 py-1 rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </Card>
        </Link>
      ))}
    </div>
  );
};

export default EntryList;
