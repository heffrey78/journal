'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowPathIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

import { getChatSession, updateChatSession, deleteChatSession } from '@/api/chat';
import { ChatSession } from '@/types/chat';
import { cn } from '@/lib/utils';

export default function SessionSettingsPage() {
  const { session_id } = useParams();
  const router = useRouter();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    const loadSession = async () => {
      try {
        setLoading(true);
        setError(null);

        if (session_id) {
          const sessionData = await getChatSession(session_id as string);
          setSession(sessionData);
          setTitle(sessionData.title);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [session_id]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setSaving(true);
      setError(null);

      if (!session_id) return;

      await updateChatSession(session_id as string, {
        title
      });

      // Navigate back to the chat session
      router.push(`/chat/${session_id}`);
    } catch (err) {
      setError((err as Error).message);
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      if (!session_id) return;

      await deleteChatSession(session_id as string);

      // Navigate back to the sessions list
      router.push('/chat');
    } catch (err) {
      setError((err as Error).message);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <ArrowPathIcon className="h-8 w-8 animate-spin opacity-50" />
      </div>
    );
  }

  if (error && !session) {
    return (
      <div className="p-8">
        <div className="bg-destructive/20 text-destructive p-4 rounded-md">
          <p>Error: {error}</p>
          <Link href="/chat" className="text-primary underline block mt-4">
            Back to chat sessions
          </Link>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="p-8 text-center">
        <p>Session not found</p>
        <Link href="/chat" className="text-primary underline block mt-4">
          Back to chat sessions
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8">
      <div className="flex items-center gap-2 mb-8">
        <Link
          href={`/chat/${session_id}`}
          className="p-2 hover:bg-muted rounded-md transition-colors"
          title="Back to chat"
        >
          <ArrowLeftIcon className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-bold">Chat Settings</h1>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-destructive/20 text-destructive p-4 rounded-md mb-6">
          <p>Error: {error}</p>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        <div>
          <label htmlFor="title" className="block text-sm font-medium mb-1">
            Chat Title
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className={cn(
              "w-full px-3 py-2 border rounded-md",
              "bg-background",
              "focus:outline-none focus:ring-2 focus:ring-primary"
            )}
            required
          />
        </div>

        <div className="flex justify-between">
          <button
            type="submit"
            disabled={saving || title === session.title}
            className={cn(
              "px-4 py-2 bg-primary text-primary-foreground rounded-md",
              "hover:bg-primary/90 transition-colors",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {saving ? (
              <ArrowPathIcon className="h-5 w-5 animate-spin" />
            ) : (
              'Save Changes'
            )}
          </button>

          <button
            type="button"
            onClick={() => setShowDeleteConfirm(true)}
            className="px-4 py-2 text-destructive hover:bg-destructive/20 rounded-md transition-colors"
          >
            Delete Session
          </button>
        </div>
      </form>

      {/* Delete confirmation modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background p-6 rounded-lg max-w-md">
            <h3 className="text-xl font-semibold mb-4">Delete Session</h3>
            <p>
              Are you sure you want to delete this chat session? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-4 mt-6">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 border rounded-md hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
