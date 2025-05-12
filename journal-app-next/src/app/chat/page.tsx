import React from 'react';
import { ChatInterface } from '@/components/chat';
import MainLayout from '@/components/layout/MainLayout';

export default function ChatPage() {
  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Chat with your Journal</h1>
        <ChatInterface />
      </div>
    </MainLayout>
  );
}
