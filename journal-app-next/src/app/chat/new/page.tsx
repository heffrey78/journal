'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createChatSessionWithMessage, getDefaultPersona } from '@/api/chat';
import { Container } from '@/components/layout';
import { ChatInterface } from '@/components/chat';
import { Persona } from '@/types/chat';

export default function NewChatPage() {
  const router = useRouter();
  const [defaultPersona, setDefaultPersona] = useState<Persona | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDefaultPersona() {
      try {
        const persona = await getDefaultPersona();
        setDefaultPersona(persona);
      } catch (err) {
        console.error('Error loading default persona:', err);
        setError('Failed to load default persona');
      } finally {
        setIsLoading(false);
      }
    }

    loadDefaultPersona();
  }, []);

  const handleFirstMessage = async (content: string, selectedPersonaId?: string) => {
    try {
      setIsLoading(true);

      // Generate default title with current date/time
      const defaultTitle = `Chat on ${new Date().toLocaleDateString()}`;

      // Use the selected persona ID if provided, otherwise use default
      const personaId = selectedPersonaId || defaultPersona?.id;

      // Create session with first message atomically
      const result = await createChatSessionWithMessage({
        message_content: content,
        session_title: defaultTitle,
        persona_id: personaId
      });

      // Navigate to the new session with the created session ID
      router.push(`/chat/${result.session_id}`);
    } catch (err) {
      console.error('Error creating new chat session:', err);
      setError('Failed to create chat session');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !defaultPersona) {
    return (
      <Container className="py-8 max-w-6xl">
        <div className="space-y-6 text-center">
          <h2 className="text-xl font-semibold">Loading Chat Interface</h2>
          <p className="text-muted-foreground">
            Setting up your chat environment...
          </p>
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="py-8 max-w-6xl">
        <div className="space-y-6 text-center">
          <h2 className="text-xl font-semibold text-destructive">Error</h2>
          <p className="text-muted-foreground">{error}</p>
          <button
            onClick={() => router.push('/chat')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Go Back to Chat List
          </button>
        </div>
      </Container>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-grow overflow-hidden">
        {/* Chat Interface - render it the same way as existing chat */}
        <div className="flex-grow overflow-hidden">
          <ChatInterface
            sessionId="new" // Use a placeholder to enable all controls
            onFirstMessage={handleFirstMessage}
            isCreatingSession={isLoading}
            defaultPersona={defaultPersona}
          />
        </div>
      </div>
    </div>
  );
}
