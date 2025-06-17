'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  ArrowPathIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline';

import { fetchChatSessions, deleteChatSession, searchChatSessions, ChatSearchFilters, ChatSearchResult } from '@/api/chat';
import { ChatSession } from '@/types/chat';
import { cn } from '@/lib/utils';
import { Pagination } from '@/components/design-system/Pagination';
import { ChatSearchBar, ChatSearchResults } from '@/components/chat';

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
  const searchParams = useSearchParams();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState('last_accessed');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<ChatSearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [totalSearchResults, setTotalSearchResults] = useState(0);
  const [isSearchMode, setIsSearchMode] = useState(false);

  const ITEMS_PER_PAGE = 10;

  // Initialize state from URL parameters
  useEffect(() => {
    const urlPage = searchParams.get('page');
    const urlSortBy = searchParams.get('sort_by');
    const urlSortOrder = searchParams.get('sort_order');

    if (urlPage) {
      const pageNum = parseInt(urlPage, 10);
      if (pageNum > 0) {
        setPage(pageNum);
      }
    }
    if (urlSortBy) {
      setSortBy(urlSortBy);
    }
    if (urlSortOrder && (urlSortOrder === 'asc' || urlSortOrder === 'desc')) {
      setSortOrder(urlSortOrder);
    }
  }, [searchParams]);

  // Update URL when pagination/sorting changes
  const updateURL = (newPage: number, newSortBy: string, newSortOrder: string) => {
    const params = new URLSearchParams();
    params.set('page', newPage.toString());
    params.set('sort_by', newSortBy);
    params.set('sort_order', newSortOrder);
    router.replace(`/chat?${params.toString()}`, { scroll: false });
  };

  // Load sessions
  const loadSessions = useCallback(async () => {
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
      setTotalPages(Math.ceil(result.total / ITEMS_PER_PAGE));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [page, sortBy, sortOrder]);

  // Initial load and when pagination/sorting changes
  useEffect(() => {
    if (!isSearchMode) {
      loadSessions();
    }
  }, [page, sortBy, sortOrder, loadSessions, isSearchMode]);

  // Handle creating a new session - redirect to persona selection
  const handleCreateSession = () => {
    router.push('/chat/new');
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
    let newSortOrder = 'desc';
    if (sortBy === field) {
      // Toggle order if field is the same
      newSortOrder = sortOrder === 'desc' ? 'asc' : 'desc';
    }

    setSortBy(field);
    setSortOrder(newSortOrder);
    setPage(1); // Reset to first page when sorting changes
    updateURL(1, field, newSortOrder);
  };

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    updateURL(newPage, sortBy, sortOrder);
  };

  // Handle search
  const handleSearch = useCallback(async (query: string, filters?: ChatSearchFilters) => {
    if (!query.trim() || searchLoading) {
      return;
    }

    setSearchQuery(query);
    setSearchLoading(true);
    setSearchError(null);
    setIsSearchMode(true);

    try {
      const results = await searchChatSessions(query, {
        limit: ITEMS_PER_PAGE,
        offset: (page - 1) * ITEMS_PER_PAGE,
        filters
      });

      setSearchResults(results.results);
      setTotalSearchResults(results.total);
      setTotalPages(Math.ceil(results.total / ITEMS_PER_PAGE));
    } catch (err) {
      setSearchError((err as Error).message);
      setSearchResults([]);
      setTotalSearchResults(0);
    } finally {
      setSearchLoading(false);
    }
  }, [page, searchLoading]);

  // Handle clear search
  const handleClearSearch = useCallback(() => {
    setSearchQuery('');
    setSearchResults([]);
    setSearchError(null);
    setTotalSearchResults(0);
    setIsSearchMode(false);
    setPage(1);
    // Don't reload sessions here to prevent re-render loop
    // Sessions will be loaded by the useEffect when page changes
  }, []);

  // Handle search retry
  const handleSearchRetry = useCallback(() => {
    if (searchQuery) {
      handleSearch(searchQuery);
    }
  }, [searchQuery, handleSearch]);

  return (
    <div className="w-full max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Chat Sessions</h1>
        <button
          onClick={handleCreateSession}
          className={cn(
            "flex items-center gap-2 px-4 py-2",
            "bg-primary text-primary-foreground",
            "rounded-md hover:bg-primary/90 transition-colors"
          )}
        >
          <PlusIcon className="h-5 w-5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Search bar */}
      <div className="mb-6">
        <ChatSearchBar
          onSearch={handleSearch}
          onClear={handleClearSearch}
          isLoading={searchLoading}
          placeholder="Search chat sessions and messages..."
        />
      </div>

      {/* Sorting and filtering options - only show when not in search mode */}
      {!isSearchMode && (
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
      )}

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

      {/* Content area - sessions list or search results */}
      <div className="space-y-4 mb-8">
        {isSearchMode ? (
          /* Search results */
          <ChatSearchResults
            results={searchResults}
            query={searchQuery}
            isLoading={searchLoading}
            error={searchError}
            onRetry={handleSearchRetry}
            totalResults={totalSearchResults}
          />
        ) : (
          /* Regular sessions list */
          <>
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
          </>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={page - 1} // Convert from 1-based to 0-based
          totalPages={totalPages}
          onPrevious={() => handlePageChange(page - 1)}
          onNext={() => handlePageChange(page + 1)}
          onFirst={() => handlePageChange(1)}
          onLast={() => handlePageChange(totalPages)}
          showFirstLast={totalPages > 5}
          showPageNumbers={true}
        />
      )}
    </div>
  );
}
