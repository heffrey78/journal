'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
// import { useRouter } from 'next/navigation'; // Import kept for future use - Removed as unused
import {
  PlusIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowPathIcon,
  ChatBubbleOvalLeftEllipsisIcon
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { fetchChatSessions, getChatSessionStats } from '@/api/chat';
import { ChatSession, ChatSessionStats } from '@/types/chat';

interface ChatSessionsSidebarProps {
  currentSessionId?: string;
  isOpen?: boolean;
  onToggle?: () => void;
}

export const ChatSessionsSidebar: React.FC<ChatSessionsSidebarProps> = ({
  currentSessionId,
  isOpen = true,
  onToggle
}) => {
  const [recentSessions, setRecentSessions] = useState<ChatSession[]>([]);
  const [sessionStats, setSessionStats] = useState<Record<string, ChatSessionStats>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load recent sessions
  useEffect(() => {
    const loadSessions = async () => {
      try {
        setLoading(true);
        setError(null);

        const result = await fetchChatSessions(1, 10, 'last_accessed', 'desc');

        // Filter out the current session to avoid duplication
        const filteredSessions = result.sessions.filter(
          session => session.id !== currentSessionId
        );

        // Get the 5 most recent sessions for quick access
        const recentSessionsList = filteredSessions.slice(0, 5);
        setRecentSessions(recentSessionsList);

        // Fetch session statistics for recent sessions
        const stats: Record<string, ChatSessionStats> = {};
        await Promise.all(
          recentSessionsList.map(async (session) => {
            try {
              const sessionStats = await getChatSessionStats(session.id);
              stats[session.id] = sessionStats;
            } catch (error) {
              console.error(`Failed to fetch stats for session ${session.id}:`, error);
            }
          })
        );

        setSessionStats(stats);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen) {
      loadSessions();
    }
  }, [isOpen, currentSessionId]);

  // Format abbreviated session titles
  const abbreviateTitle = (title: string, maxLength: number = 16) => {
    if (title.length <= maxLength) return title;
    return title.substring(0, maxLength - 3) + '...';
  };

  return (
    <div className={cn(
      'h-full',
      'border-r',
      'transition-all duration-300 ease-in-out',
      isOpen ? 'w-[240px] min-w-[240px]' : 'w-[40px] min-w-[40px]',
    )}>
      <div className="flex flex-col h-full">
        {/* Sidebar header with toggle */}
        <div className={cn(
          'p-2 border-b flex items-center',
          isOpen ? 'justify-between' : 'justify-center'
        )}>
          {isOpen && (
            <h3 className="font-semibold text-sm">Chat Sessions</h3>
          )}
          <button
            onClick={onToggle}
            className="p-1.5 rounded-md hover:bg-muted transition-colors"
            title={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {isOpen ? (
              <ChevronLeftIcon className="h-4 w-4" />
            ) : (
              <ChevronRightIcon className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* New chat button - always visible */}
        <Link
          href="/chat/new"
          className={cn(
            'p-2 m-1',
            'flex items-center gap-2',
            'bg-primary/10 hover:bg-primary/20',
            'text-primary font-medium rounded-md',
            'transition-colors justify-center',
            !isOpen && 'p-1.5'
          )}
          title="New chat"
        >
          <PlusIcon className="h-4 w-4" />
          {isOpen && <span className="text-sm">New chat</span>}
        </Link>

        {/* Loading state - always visible */}
        {loading && (
          <div className="flex justify-center p-2">
            <ArrowPathIcon className="h-5 w-5 animate-spin opacity-50" />
          </div>
        )}

        {/* Only show error when sidebar is open */}
        {error && isOpen && (
          <div className="p-2 text-sm text-destructive">
            <p>Failed to load sessions</p>
          </div>
        )}

        {/* Collapsed view for sessions */}
        {!isOpen && !loading && (
          <div className="overflow-y-auto flex-grow">
            {recentSessions.map(session => (
              <Link
                key={session.id}
                href={`/chat/${session.id}`}
                className={cn(
                  'flex justify-center py-2',
                  'hover:bg-muted',
                  'transition-colors',
                  session.id === currentSessionId && 'bg-muted'
                )}
                title={session.title}
              >
                <ChatBubbleOvalLeftEllipsisIcon
                  className={cn(
                    "h-5 w-5",
                    session.id === currentSessionId ? "text-primary" : "text-muted-foreground"
                  )}
                />
              </Link>
            ))}
          </div>
        )}

        {/* Only show expanded content when sidebar is open */}
        {isOpen && (
          <>
            {/* Content is already shown above */}

            {/* Session list */}
            <div className="flex-grow overflow-y-auto p-2">
              <div className="space-y-1">
                {recentSessions.length > 0 ? (
                  recentSessions.map(session => (
                    <Link
                      key={session.id}
                      href={`/chat/${session.id}`}
                      className={cn(
                        'block py-1.5 px-2 rounded-md',
                        'text-sm',
                        'hover:bg-muted',
                        'transition-colors',
                        'flex flex-col',
                        session.id === currentSessionId && 'bg-muted font-medium'
                      )}
                      title={session.title}
                    >
                      <span className="truncate font-medium">{abbreviateTitle(session.title)}</span>

                      {sessionStats[session.id] && (
                        <>
                          {sessionStats[session.id].last_message_preview && (
                            <div className="text-xs text-muted-foreground mt-1 truncate">
                              {abbreviateTitle(sessionStats[session.id].last_message_preview, 28)}
                            </div>
                          )}
                          <div className="flex justify-between text-xs text-muted-foreground mt-1">
                            <span>{sessionStats[session.id].message_count} msgs</span>
                            {sessionStats[session.id].reference_count > 0 && (
                              <span>{sessionStats[session.id].reference_count} refs</span>
                            )}
                          </div>
                        </>
                      )}

                      <div className="text-xs text-muted-foreground mt-1">
                        {new Date(session.updated_at).toLocaleDateString()}
                      </div>
                    </Link>
                  ))
                ) : !loading && (
                  <div className="text-xs text-muted-foreground p-2 text-center">
                    No recent sessions
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Footer - always visible */}
        <div className="border-t border-border p-2">
          <Link
            href="/chat"
            className={cn(
              'flex justify-center items-center py-1 rounded-md hover:bg-muted transition-colors',
              isOpen ? 'text-xs text-muted-foreground' : 'p-1.5'
            )}
            title="View all sessions"
          >
            {isOpen ? 'View all sessions' : (
              <ChatBubbleOvalLeftEllipsisIcon className="h-4 w-4 text-muted-foreground" />
            )}
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ChatSessionsSidebar;
