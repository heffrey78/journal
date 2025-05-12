'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { createChatSession } from '@/api/chat';

export default function NewChatPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const createNewSession = async () => {
      try {
        // Generate default title with current date/time
        const defaultTitle = `Chat on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;

        // Create the session
        const session = await createChatSession({
          title: defaultTitle
        });

        // Navigate to the new session
        router.push(`/chat/${session.id}`);
      } catch (err) {
        setError((err as Error).message);
      }
    };

    createNewSession();
  }, [router]);

  return (
    <div className="flex flex-col items-center justify-center h-full">
      {error ? (
        <div className="bg-destructive/20 text-destructive p-4 rounded-md">
          <p>Error creating new chat session: {error}</p>
          <button
            onClick={() => router.push('/chat')}
            className="text-primary underline block mt-4"
          >
            Back to chat sessions
          </button>
        </div>
      ) : (
        <>
          <ArrowPathIcon className="h-8 w-8 animate-spin opacity-50" />
          <p className="mt-4 text-muted-foreground">Creating new chat session...</p>
        </>
      )}
    </div>
  );
}
