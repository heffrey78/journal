import React from 'react';
import { ChatInterface } from '@/components/chat';

export default function ChatPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Chat with your Journal</h1>
      <ChatInterface />
    </div>
  );
}
