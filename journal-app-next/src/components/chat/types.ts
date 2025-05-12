/**
 * Shared types for chat components
 */

// Type for the role of a chat message
export type MessageRole = 'user' | 'assistant';

// Interface for a journal entry reference
export interface EntryReference {
  message_id: string;
  entry_id: string;
  similarity_score: number;
  chunk_index?: number;
  entry_title?: string;
  entry_snippet?: string;
  // Keep compatibility with frontend formatting needs
  title?: string;
  date?: string;
  preview?: string;
  tags?: string[];
  relevance_score?: number;
}

// Interface for a chat message
export interface Message {
  id: string;
  content: string;
  role: MessageRole;
  timestamp: Date;
  references?: EntryReference[];
  has_references?: boolean;
}
