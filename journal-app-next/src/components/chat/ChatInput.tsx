'use client';

import React, { useState, KeyboardEvent } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export default function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex gap-2 items-end">
      <textarea
        className="flex-1 min-h-[60px] p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none bg-card text-card-foreground placeholder:text-muted-foreground"
        placeholder="Ask a question about your journal entries..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
        rows={2}
      />
      <button
        className={`p-3 rounded-lg ${
          isLoading || !message.trim()
            ? 'bg-muted text-muted-foreground cursor-not-allowed'
            : 'bg-primary text-primary-foreground hover:opacity-90'
        }`}
        onClick={handleSubmit}
        disabled={isLoading || !message.trim()}
      >
        {isLoading ? (
          <div className="w-6 h-6 border-t-2 border-b-2 border-current rounded-full animate-spin"></div>
        ) : (
          <PaperAirplaneIcon className="h-6 w-6" />
        )}
      </button>
    </div>
  );
}
