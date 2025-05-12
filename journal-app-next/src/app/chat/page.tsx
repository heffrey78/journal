'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ArrowPathIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline';

import { fetchChatSessions, deleteChatSession, createChatSession } from '@/api/chat';
import { ChatSession } from '@/types/chat';
import { cn } from '@/lib/utils';

// Formatting utility for date
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date);
};

export default function ChatSessionsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState('last_accessed');
  const [sortOrder, setSortOrder] = useState('desc');
  const [isCreating, setIsCreating] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  const ITEMS_PER_PAGE = 10;

  // Load sessions
  const loadSessions = async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await fetchChatSessions(
        page,
        ITEMS_PER_PAGE,
        sortBy,
        sortOrder
      );

      setSessions(result.sessions);

      // Calculate total pages
      const total = result.total || result.sessions.length;
      setTotalPages(Math.ceil(total / ITEMS_PER_PAGE));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Initial load and when pagination/sorting changes
  useEffect(() => {
    loadSessions();
  }, [page, sortBy, sortOrder]);

  // Handle creating a new session
  const handleCreateSession = async () => {
    try {
      setIsCreating(true);
      const session = await createChatSession({
        title: `Chat on ${new Date().toLocaleDateString()}`
      });

      router.push(`/chat/${session.id}`);
    } catch (err) {
      setError((err as Error).message);
      setIsCreating(false);
    }
  };

  // Handle deleting a session
  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteChatSession(sessionId);
      loadSessions();
      setShowDeleteConfirm(null);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  // Handle sorting change
  const handleSortChange = (field: string) => {
    if (sortBy === field) {
      // Toggle order if field is the same
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortOrder('desc'); // Default to descending when field changes
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Chat Sessions</h1>
        <button
          onClick={handleCreateSession}
          disabled={isCreating}
          className={cn(
            "flex items-center gap-2 px-4 py-2",
            "bg-primary text-primary-foreground",
            "rounded-md hover:bg-primary/90 transition-colors",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          {isCreating ? (
            <ArrowPathIcon className="h-5 w-5 animate-spin" />
          ) : (
            <PlusIcon className="h-5 w-5" />
          )}
          <span>New Chat</span>
        </button>
      </div>

      {/* Sorting and filtering options */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex gap-4">
          <button
            onClick={() => handleSortChange('last_accessed')}
            className={cn(
              "text-sm px-2 py-1 rounded",
              sortBy === 'last_accessed' && "font-semibold underline"
            )}
          >
            Last accessed {sortBy === 'last_accessed' && (sortOrder === 'desc' ? '▼' : '▲')}
          </button>
          <button
            onClick={() => handleSortChange('created_at')}
            className={cn(
              "text-sm px-2 py-1 rounded",
              sortBy === 'created_at' && "font-semibold underline"
            )}
          >
            Created {sortBy === 'created_at' && (sortOrder === 'desc' ? '▼' : '▲')}
          </button>
          <button
            onClick={() => handleSortChange('title')}
            className={cn(
              "text-sm px-2 py-1 rounded",
              sortBy === 'title' && "font-semibold underline"
            )}
          >
            Title {sortBy === 'title' && (sortOrder === 'desc' ? '▼' : '▲')}
          </button>
        </div>

        <div>
          <button
            onClick={loadSessions}
            className="text-sm px-2 py-1 hover:bg-muted rounded"
            title="Refresh sessions"
          >
            <ArrowPathIcon className={cn(
              "h-5 w-5",
              loading && "animate-spin"
            )} />
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-destructive/20 text-destructive p-4 rounded-md mb-4">
          <p>Error: {error}</p>
          <button
            onClick={loadSessions}
            className="text-sm underline mt-2"
          >
            Try again
          </button>
        </div>
      )}

      {/* Sessions list */}
      <div className="space-y-4 mb-8">
        {loading && !sessions.length ? (
          <div className="p-8 text-center">
            <ArrowPathIcon className="h-8 w-8 mx-auto animate-spin opacity-50" />
            <p className="mt-2 text-muted-foreground">Loading sessions...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="bg-muted/30 p-8 rounded-md text-center">
            <p className="text-muted-foreground">No chat sessions found.</p>
            <button
              onClick={handleCreateSession}
              className="text-primary mt-2 flex items-center gap-2 mx-auto"
            >
              <PlusIcon className="h-4 w-4" />
              <span>Start a new chat</span>
            </button>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={cn(
                "border rounded-lg p-4",
                "hover:border-primary transition-colors",
                "flex flex-col sm:flex-row justify-between gap-4"
              )}
            >
              <div className="flex-1">
                <Link
                  href={`/chat/${session.id}`}
                  className="block group"
                >
                  <h3 className="text-xl font-semibold group-hover:text-primary transition-colors">
                    {session.title}
                    <ArrowTopRightOnSquareIcon className="inline ml-1 h-4 w-4 opacity-0 group-hover:opacity-60" />
                  </h3>

                  <div className="flex flex-wrap gap-4 mt-1 text-sm text-muted-foreground">
                    <span>
                      Last accessed: {formatDate(session.last_accessed)}
                    </span>
                    <span>
                      Created: {formatDate(session.created_at)}
                    </span>
                  </div>

                  <div className="mt-3">
                    <span className="text-sm bg-muted rounded-full px-2 py-1 mr-2">
                      {session.entry_count} references
                    </span>
                  </div>
                </Link>
              </div>

              <div className="flex items-center gap-2 sm:flex-col">
                <Link
                  href={`/chat/${session.id}/settings`}
                  className="text-muted-foreground hover:text-foreground p-1.5 rounded-md hover:bg-muted transition-colors"
                  title="Edit session settings"
                >
                  <PencilIcon className="h-5 w-5" />
                </Link>

                <button
                  onClick={() => setShowDeleteConfirm(session.id)}
                  className="text-destructive hover:text-destructive p-1.5 rounded-md hover:bg-destructive/20 transition-colors"
                  title="Delete session"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>

                {/* Delete confirmation */}
                {showDeleteConfirm === session.id && (
                  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-background p-6 rounded-lg max-w-md">
                      <h3 className="text-xl font-semibold mb-4">Delete Session</h3>
                      <p>
                        Are you sure you want to delete this chat session? This cannot be undone.
                      </p>
                      <div className="flex justify-end gap-4 mt-6">
                        <button
                          onClick={() => setShowDeleteConfirm(null)}
                          className="px-4 py-2 border rounded-md hover:bg-muted transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleDeleteSession(session.id)}
                          className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            className={cn(
              "p-2 rounded-md",
              page === 1 ? "opacity-50 cursor-not-allowed" : "hover:bg-muted"
            )}
          >
            ◁
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
            <button
              key={pageNum}
              onClick={() => setPage(pageNum)}
              className={cn(
                "p-2 rounded-md min-w-8 text-center",
                page === pageNum
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              )}
            >
              {pageNum}
            </button>
          ))}

          <button
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
            className={cn(
              "p-2 rounded-md",
              page === totalPages ? "opacity-50 cursor-not-allowed" : "hover:bg-muted"
            )}
          >
            ▷
          </button>
        </div>
      )}
    </div>
  );
}
