'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ChatInterface, ChatSessionsSidebar } from '@/components/chat';
import { getChatSession } from '@/api/chat';
import { ChatSession } from '@/types/chat';
import { ArrowPathIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

export default function ChatSessionPage() {
  const { session_id } = useParams();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    const loadSession = async () => {
      try {
        setLoading(true);
        setError(null);

        if (session_id) {
          const sessionData = await getChatSession(session_id as string);
          setSession(sessionData);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [session_id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <ArrowPathIcon className="h-8 w-8 animate-spin opacity-50" />
      </div>
    );
  }

  if (error) {
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
  }  return (
    <div className="flex flex-col h-full">
      <div className="border-b pb-2 pt-1 px-2 flex justify-between items-center bg-background/90 sticky top-0 z-10">
        <h1 className="text-xl font-semibold truncate">{session.title}</h1>
        <div className="flex items-center gap-2">
          <Link
            href="/chat"
            className={cn(
              "px-3 py-1 text-sm rounded-md",
              "hover:bg-muted transition-colors"
            )}
          >
            All Sessions
          </Link>

          <Link
            href={`/chat/${session_id}/settings`}
            className={cn(
              "p-1.5 rounded-md",
              "hover:bg-muted transition-colors"
            )}
            title="Session Settings"
          >
            <Cog6ToothIcon className="h-5 w-5" />
          </Link>
        </div>
      </div>

      <div className="flex flex-grow overflow-hidden">
        {/* Chat Sessions Sidebar */}
        <ChatSessionsSidebar
          currentSessionId={session_id as string}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />

        {/* Chat Interface */}
        <div className="flex-grow overflow-hidden">
          <ChatInterface sessionId={session_id as string} />
        </div>
      </div>
    </div>
  );
}
