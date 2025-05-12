/**
 * Types for chat functionality
 */

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  last_accessed: string;
  context_summary?: string;
  temporal_filter?: string;
  entry_count: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  metadata?: Record<string, any>;
  token_count?: number;
}

export interface EntryReference {
  message_id: string;
  entry_id: string;
  similarity_score: number;
  chunk_index?: number;
  entry_title?: string;
  entry_snippet?: string;
}

export interface ChatSessionStats {
  message_count: number;
  user_message_count: number;
  assistant_message_count: number;
  reference_count: number;
  last_message_preview: string;
}

export interface CreateSessionRequest {
  title?: string;
  temporal_filter?: string;
}

export interface UpdateSessionRequest {
  title?: string;
  context_summary?: string;
  temporal_filter?: string;
}

export interface ChatListResponse {
  sessions: ChatSession[];
  total: number;
}
