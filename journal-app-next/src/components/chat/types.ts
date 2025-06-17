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

// Interface for tool usage information
export interface ToolUsage {
  tool_name: string;
  success: boolean;
  execution_time_ms?: number;
  result_count?: number;
  confidence?: number;
  query?: string;
  error?: string;
  // Result data for enhanced display
  results?: ToolResult[];
}

// Interface for individual tool results
export interface ToolResult {
  // Journal search results
  id?: string;
  title?: string;
  content_preview?: string;
  date?: string;
  tags?: string[];
  relevance?: number;
  source?: string;

  // Web search results
  url?: string;
  snippet?: string;
  published?: string;
  source?: string;
  source_domain?: string;
}

// Interface for a chat message
export interface Message {
  id: string;
  content: string;
  role: MessageRole;
  timestamp: Date;
  references?: EntryReference[];
  has_references?: boolean;
  tools_used?: ToolUsage[];
  metadata?: Record<string, unknown>;
}
