'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import MainLayout from '@/components/layout/MainLayout';
import MarkdownEditor from '@/components/markdown/MarkdownEditor';
import MarkdownRenderer from '@/components/markdown/MarkdownRenderer';
import EntryAnalysis from '@/components/entries/EntryAnalysis'; // Import the EntryAnalysis component
import Button from '@/components/ui/Button';
import { entriesApi } from '@/lib/api';
import { JournalEntry } from '@/lib/types';
import { format } from 'date-fns';

interface EntryDetailPageProps {
  params: {
    id: string;
  };
}

export default function EntryDetailPage({ params }: EntryDetailPageProps) {
  const router = useRouter();
  const { id } = params;

  const [entry, setEntry] = useState<JournalEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Edit form states
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchEntry = async () => {
      try {
        setLoading(true);
        const data = await entriesApi.getEntry(id);
        setEntry(data);

        // Initialize edit form with entry data
        setTitle(data.title);
        setContent(data.content);
        setTags(data.tags.join(', '));
      } catch (err) {
        console.error('Failed to fetch entry:', err);
        setError('Failed to load entry. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchEntry();
    }
  }, [id]);

  const handleSave = async () => {
    if (!entry) return;

    setIsSaving(true);
    try {
      const tagsArray = tags
        .split(',')
        .map(tag => tag.trim())
        .filter(Boolean);

      const updatedEntry = await entriesApi.updateEntry(id, {
        title: title || 'Untitled Entry',
        content,
        tags: tagsArray,
      });

      setEntry(updatedEntry);
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to update entry:', err);
      setError('Failed to save changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleFavorite = async () => {
    if (!entry) return;

    try {
      const updatedEntry = await entriesApi.toggleFavorite(id, !entry.favorite);
      setEntry(updatedEntry);
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this entry? This action cannot be undone.')) {
      return;
    }

    try {
      await entriesApi.deleteEntry(id);
      router.push('/entries');
    } catch (err) {
      console.error('Failed to delete entry:', err);
      setError('Failed to delete entry. Please try again.');
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </MainLayout>
    );
  }

  if (error || !entry) {
    return (
      <MainLayout>
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-300 p-4 rounded-md">
          {error || 'Entry not found'}
        </div>
        <div className="mt-4">
          <Button onClick={() => router.push('/entries')}>
            Back to Entries
          </Button>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {!isEditing ? (
          <>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white break-words">
              {entry.title || 'Untitled Entry'}
            </h1>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                Edit
              </Button>
              <Button
                variant={entry.favorite ? 'primary' : 'outline'}
                onClick={handleToggleFavorite}
                className={entry.favorite ? 'bg-yellow-500 hover:bg-yellow-600' : ''}
              >
                {entry.favorite ? 'Favorited' : 'Favorite'}
              </Button>
              <Button variant="danger" onClick={handleDelete}>
                Delete
              </Button>
            </div>
          </>
        ) : (
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Edit Entry
          </h1>
        )}
      </div>

      {!isEditing ? (
        <>
          <div className="flex items-center gap-x-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
            <span>Created: {format(new Date(entry.created_at), 'MMM d, yyyy h:mm a')}</span>
            {entry.created_at !== entry.updated_at && (
              <span>• Updated: {format(new Date(entry.updated_at), 'MMM d, yyyy h:mm a')}</span>
            )}
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
            <MarkdownRenderer content={entry.content} />
          </div>

          {entry.tags && entry.tags.length > 0 && (
            <div className="mt-4 mb-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Tags</h2>
              <div className="flex flex-wrap gap-2">
                {entry.tags.map(tag => (
                  <span
                    key={tag}
                    className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-1 rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Add the EntryAnalysis component */}
          <EntryAnalysis entryId={id} />

          <div className="mt-6">
            <Button onClick={() => router.push('/entries')}>
              Back to Entries
            </Button>
          </div>
        </>
      ) : (
        <form className="space-y-6">
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
              <MarkdownEditor
                value={content}
                onChange={setContent}
              />
            </div>
          </div>

          <div>
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

          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsEditing(false)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleSave}
              isLoading={isSaving}
              disabled={!content.trim()}
            >
              Save Changes
            </Button>
          </div>
        </form>
      )}
    </MainLayout>
  );
}
