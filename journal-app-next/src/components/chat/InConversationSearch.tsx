'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { useDebounce } from '@/hooks/useDebounce';
import { MessageSearchResult } from './ChatSearchResults';

interface InConversationSearchProps {
  sessionId: string;
  isOpen: boolean;
  onClose: () => void;
  onMessageFound: (messageId: string) => void;
  className?: string;
}

const formatTime = (dateString: string) => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    month: 'short',
    day: 'numeric',
  }).format(date);
};

const highlightText = (text: string, query: string) => {
  if (!query.trim()) return text;

  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, index) => (
    regex.test(part) ? (
      <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-0.5 rounded">
        {part}
      </mark>
    ) : part
  ));
};

export const InConversationSearch: React.FC<InConversationSearchProps> = ({
  sessionId,
  isOpen,
  onClose,
  onMessageFound,
  className
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MessageSearchResult[]>([]);
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounce search input
  const debouncedQuery = useDebounce(query, 300);

  // Perform search when debounced query changes
  useEffect(() => {
    const performSearch = async () => {
      if (!debouncedQuery.trim() || !sessionId) {
        setResults([]);
        setCurrentIndex(-1);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
        const response = await fetch(
          `${API_BASE_URL}/chat/sessions/${sessionId}/search?q=${encodeURIComponent(debouncedQuery)}&limit=50`
        );

        if (!response.ok) {
          throw new Error('Failed to search messages');
        }

        const searchResults: MessageSearchResult[] = await response.json();
        setResults(searchResults);
        setCurrentIndex(searchResults.length > 0 ? 0 : -1);

        // Navigate to first result if available
        if (searchResults.length > 0) {
          onMessageFound(searchResults[0].message.id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed');
        setResults([]);
        setCurrentIndex(-1);
      } finally {
        setIsLoading(false);
      }
    };

    performSearch();
  }, [debouncedQuery, sessionId, onMessageFound]);

  const handleQueryChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  }, []);

  const handleClear = useCallback(() => {
    setQuery('');
    setResults([]);
    setCurrentIndex(-1);
  }, []);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      onClose();
      return;
    }

    if (event.key === 'Enter') {
      event.preventDefault();
      if (event.shiftKey) {
        // Shift+Enter: previous result
        navigateToPrevious();
      } else {
        // Enter: next result
        navigateToNext();
      }
    }
  }, [onClose]);

  const navigateToNext = useCallback(() => {
    if (results.length === 0) return;
    const nextIndex = (currentIndex + 1) % results.length;
    setCurrentIndex(nextIndex);
    onMessageFound(results[nextIndex].message.id);
  }, [results, currentIndex, onMessageFound]);

  const navigateToPrevious = useCallback(() => {
    if (results.length === 0) return;
    const prevIndex = currentIndex <= 0 ? results.length - 1 : currentIndex - 1;
    setCurrentIndex(prevIndex);
    onMessageFound(results[prevIndex].message.id);
  }, [results, currentIndex, onMessageFound]);

  const handleResultClick = useCallback((index: number) => {
    setCurrentIndex(index);
    onMessageFound(results[index].message.id);
  }, [results, onMessageFound]);

  if (!isOpen) {
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />

      {/* Search modal */}
      <div className={cn(
        "fixed top-4 right-4 w-80 bg-white dark:bg-gray-900 border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-2xl z-50",
        "flex flex-col max-h-96",
        className
      )}>
      {/* Search header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium">Search in conversation</h3>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground p-1 rounded-md hover:bg-muted"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        </div>

        {/* Search input */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            {isLoading ? (
              <ArrowPathIcon className="h-4 w-4 text-muted-foreground animate-spin" />
            ) : (
              <MagnifyingGlassIcon className="h-4 w-4 text-muted-foreground" />
            )}
          </div>

          <input
            type="text"
            value={query}
            onChange={handleQueryChange}
            onKeyDown={handleKeyDown}
            placeholder="Search messages..."
            className={cn(
              "block w-full pl-10 pr-8 py-2",
              "text-sm border border-border rounded-md",
              "bg-background placeholder-muted-foreground",
              "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            )}
            autoFocus
          />

          {query && (
            <button
              onClick={handleClear}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <XMarkIcon className="h-4 w-4 text-muted-foreground hover:text-foreground" />
            </button>
          )}
        </div>

        {/* Results summary and navigation */}
        {results.length > 0 && (
          <div className="flex items-center justify-between mt-3">
            <span className="text-xs text-muted-foreground">
              {currentIndex + 1} of {results.length} results
            </span>
            <div className="flex items-center space-x-1">
              <button
                onClick={navigateToPrevious}
                disabled={results.length === 0}
                className="p-1 rounded-md hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
                title="Previous result (Shift+Enter)"
              >
                <ChevronUpIcon className="h-4 w-4" />
              </button>
              <button
                onClick={navigateToNext}
                disabled={results.length === 0}
                className="p-1 rounded-md hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
                title="Next result (Enter)"
              >
                <ChevronDownIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {error && (
          <p className="text-xs text-destructive mt-2">{error}</p>
        )}
      </div>

      {/* Results list */}
      {results.length > 0 && (
        <div className="flex-1 overflow-y-auto">
          {results.map((result, index) => (
            <button
              key={result.message.id}
              onClick={() => handleResultClick(index)}
              className={cn(
                "w-full p-3 text-left hover:bg-muted transition-colors border-b border-border last:border-b-0",
                currentIndex === index && "bg-primary/10 border-primary"
              )}
            >
              <div className="flex items-center space-x-2 mb-2">
                <span className={cn(
                  "text-xs font-medium",
                  result.message.role === 'user' ? 'text-blue-600 dark:text-blue-400' : 'text-green-600 dark:text-green-400'
                )}>
                  {result.message.role === 'user' ? 'You' : 'Assistant'}
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatTime(result.message.created_at?.toString() || new Date().toISOString())}
                </span>
                {result.relevance_score > 0 && (
                  <span className="text-xs text-muted-foreground">
                    {Math.round(result.relevance_score * 100)}%
                  </span>
                )}
              </div>

              <div className="text-sm text-muted-foreground line-clamp-3">
                {query ? (
                  <div dangerouslySetInnerHTML={{
                    __html: result.highlighted_content || highlightText(result.message.content, query)
                  }} />
                ) : (
                  result.message.content.substring(0, 150) + (result.message.content.length > 150 ? '...' : '')
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No results message */}
      {query && !isLoading && results.length === 0 && !error && (
        <div className="p-4 text-center text-sm text-muted-foreground">
          No messages found for &quot;{query}&quot;
        </div>
      )}

      {/* Help text */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800">
        <p className="text-xs text-gray-600 dark:text-gray-300">
          Press <kbd className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs">Enter</kbd> for next,
          <kbd className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs ml-1">Shift+Enter</kbd> for previous,
          <kbd className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs ml-1">Esc</kbd> to close
        </p>
      </div>
      </div>
    </>
  );
};

export default InConversationSearch;
