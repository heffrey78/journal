/**
 * Types for chat functionality
 */

export interface Persona {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  icon: string;
  is_default: boolean;
  created_at: string;
  updated_at?: string;
}

export interface PersonaCreate {
  name: string;
  description: string;
  system_prompt: string;
  icon?: string;
}

export interface PersonaUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  icon?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  last_accessed: string;
  context_summary?: string;
  temporal_filter?: string;
  entry_count: number;
  persona_id?: string;
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
  persona_id?: string;
}

export interface UpdateSessionRequest {
  title?: string;
  context_summary?: string;
  temporal_filter?: string;
  persona_id?: string;
}

export interface ChatListResponse {
  sessions: ChatSession[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}
