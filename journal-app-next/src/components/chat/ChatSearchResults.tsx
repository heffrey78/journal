'use client';

import React from 'react';
import Link from 'next/link';
import {
  ChatBubbleOvalLeftEllipsisIcon,
  ArrowTopRightOnSquareIcon,
  ClockIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { ChatSession, ChatMessage } from '@/types/chat';

export interface ChatSearchResult {
  session: ChatSession;
  match_type: 'session_title' | 'message_content' | 'context_summary';
  relevance_score: number;
  matched_messages: ChatMessage[];
  highlighted_snippets: string[];
}

export interface MessageSearchResult {
  message: ChatMessage;
  highlighted_content: string;
  relevance_score: number;
  context_before?: string;
  context_after?: string;
}

interface ChatSearchResultsProps {
  results: ChatSearchResult[];
  query: string;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  totalResults?: number;
  className?: string;
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

const formatRelativeTime = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

  if (diffInHours < 1) return 'Just now';
  if (diffInHours < 24) return `${diffInHours}h ago`;
  if (diffInHours < 48) return 'Yesterday';
  if (diffInHours < 24 * 7) return `${Math.floor(diffInHours / 24)}d ago`;
  return formatDate(dateString);
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

export const ChatSearchResults: React.FC<ChatSearchResultsProps> = ({
  results,
  query,
  isLoading = false,
  error = null,
  onRetry,
  totalResults,
  className
}) => {
  if (isLoading) {
    return (
      <div className={cn("space-y-4", className)}>
        {[1, 2, 3].map(i => (
          <div key={i} className="border rounded-lg p-4 animate-pulse">
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 bg-muted rounded-lg" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/2" />
                <div className="h-3 bg-muted rounded w-2/3" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("text-center py-8", className)}>
        <div className="text-destructive mb-4">
          <DocumentTextIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Error searching chat sessions</p>
          <p className="text-xs text-muted-foreground mt-1">{error}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-sm text-primary hover:text-primary/80 underline"
          >
            Try again
          </button>
        )}
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className={cn("text-center py-8", className)}>
        <ChatBubbleOvalLeftEllipsisIcon className="h-12 w-12 mx-auto mb-4 opacity-30" />
        <p className="text-muted-foreground">
          {query ? `No chat sessions found for &quot;${query}&quot;` : 'No search results'}
        </p>
        <p className="text-xs text-muted-foreground mt-2">
          Try adjusting your search terms or filters
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Results summary */}
      {totalResults !== undefined && (
        <div className="text-sm text-muted-foreground mb-4">
          {totalResults === 0 ? 'No results' :
           totalResults === 1 ? '1 result' :
           `${totalResults} results`}
          {query && ` for "${query}"`}
        </div>
      )}

      {/* Search results */}
      {results.map((result) => (
        <div
          key={result.session.id}
          className={cn(
            "border rounded-lg p-4 hover:border-primary transition-colors",
            "bg-background"
          )}
        >
          <Link href={`/chat/${result.session.id}`} className="block group">
            <div className="flex items-start space-x-3">
              {/* Session icon */}
              <div className="flex-shrink-0 mt-1">
                <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                  <ChatBubbleOvalLeftEllipsisIcon className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>

              {/* Session content */}
              <div className="flex-1 min-w-0">
                {/* Session title */}
                <h3 className="font-semibold text-lg group-hover:text-primary transition-colors flex items-center">
                  {highlightText(result.session.title || 'Untitled Chat', query)}
                  <ArrowTopRightOnSquareIcon className="ml-2 h-4 w-4 opacity-0 group-hover:opacity-60 transition-opacity" />
                </h3>

                {/* Match type indicator */}
                <div className="flex items-center space-x-2 mt-1 mb-2">
                  <span className={cn(
                    "text-xs px-2 py-0.5 rounded-full",
                    result.match_type === 'session_title' && "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
                    result.match_type === 'message_content' && "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
                    result.match_type === 'context_summary' && "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                  )}>
                    {result.match_type === 'session_title' && 'Title match'}
                    {result.match_type === 'message_content' && 'Content match'}
                    {result.match_type === 'context_summary' && 'Summary match'}
                  </span>

                  {result.relevance_score > 0 && (
                    <span className="text-xs text-muted-foreground">
                      {Math.round(result.relevance_score * 100)}% relevance
                    </span>
                  )}
                </div>

                {/* Highlighted snippets */}
                {result.highlighted_snippets && result.highlighted_snippets.length > 0 && (
                  <div className="space-y-1 mb-3">
                    {result.highlighted_snippets.slice(0, 2).map((snippet, index) => (
                      <p key={index} className="text-sm text-muted-foreground italic">
                        &quot;...{highlightText(snippet, query)}...&quot;
                      </p>
                    ))}
                  </div>
                )}

                {/* Session metadata */}
                <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                  <span className="flex items-center space-x-1">
                    <ClockIcon className="h-3 w-3" />
                    <span>{formatRelativeTime(result.session.last_accessed)}</span>
                  </span>

                  {result.session.entry_count > 0 && (
                    <span className="flex items-center space-x-1">
                      <DocumentTextIcon className="h-3 w-3" />
                      <span>{result.session.entry_count} references</span>
                    </span>
                  )}

                  {result.matched_messages && result.matched_messages.length > 0 && (
                    <span>{result.matched_messages.length} message{result.matched_messages.length !== 1 ? 's' : ''}</span>
                  )}
                </div>

                {/* Preview of matched messages */}
                {result.matched_messages && result.matched_messages.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {result.matched_messages.slice(0, 2).map((message) => (
                      <div key={message.id} className="text-sm bg-muted/30 rounded p-2">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className={cn(
                            "text-xs font-medium",
                            message.role === 'user' ? 'text-blue-600 dark:text-blue-400' : 'text-green-600 dark:text-green-400'
                          )}>
                            {message.role === 'user' ? 'You' : 'Assistant'}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(message.created_at?.toString() || new Date().toISOString())}
                          </span>
                        </div>
                        <p className="text-muted-foreground line-clamp-2">
                          {highlightText(message.content.substring(0, 150) + (message.content.length > 150 ? '...' : ''), query)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Link>
        </div>
      ))}
    </div>
  );
};

export default ChatSearchResults;
