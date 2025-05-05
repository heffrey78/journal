'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import MainLayout from '@/components/layout/MainLayout';
import MarkdownEditor from '@/components/markdown/MarkdownEditor';
import Button from '@/components/ui/Button';
import { entriesApi } from '@/lib/api';
import { CreateJournalEntryInput } from '@/lib/types';

export default function NewEntryPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdEntryId, setCreatedEntryId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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
      };

      const createdEntry = await entriesApi.createEntry(newEntry);
      setCreatedEntryId(createdEntry.id);

      // Optional: wait a brief moment before redirecting
      setTimeout(() => {
        router.push(`/entries/${createdEntry.id}`);
      }, 1000);
    } catch (err) {
      console.error('Failed to create entry:', err);
      setError('Failed to create entry. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <MainLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">New Journal Entry</h1>
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

      <form onSubmit={handleSubmit} className="space-y-6">
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
              placeholder="Write your journal entry here..."
              autofocus
              entryId={createdEntryId || undefined}
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
    </MainLayout>
  );
}
