/**
 * API client for chat functionality
 */
import {
  ChatSession,
  ChatMessage,
  EntryReference,
  ChatSessionStats,
  CreateSessionRequest,
  UpdateSessionRequest,
  ChatListResponse,
  Persona,
  PersonaCreate,
  PersonaUpdate
} from '@/types/chat';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

/**
 * Fetch the list of chat sessions with pagination and sorting options
 */
export async function fetchChatSessions(
  page: number = 1,
  limit: number = 10,
  sortBy: string = 'updated_at',
  sortOrder: string = 'desc'
): Promise<ChatListResponse> {
  const offset = (page - 1) * limit;
  const url = new URL(`${API_BASE_URL}/chat/sessions`);

  url.searchParams.append('limit', limit.toString());
  url.searchParams.append('offset', offset.toString());
  url.searchParams.append('sort_by', sortBy);
  url.searchParams.append('sort_order', sortOrder);

  const response = await fetch(url.toString());

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to fetch chat sessions: ${error}`);
  }

  const paginatedResponse = await response.json();

  return paginatedResponse;
}

/**
 * Create a new chat session
 */
export async function createChatSession(
  data: CreateSessionRequest = {}
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to create chat session: ${error}`);
  }

  return await response.json();
}

/**
 * Delete a chat session
 */
export async function deleteChatSession(sessionId: string): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to delete chat session: ${error}`);
  }

  return true;
}

/**
 * Get a specific chat session
 */
export async function getChatSession(sessionId: string): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get chat session: ${error}`);
  }

  return await response.json();
}

/**
 * Update a chat session
 */
export async function updateChatSession(
  sessionId: string,
  data: UpdateSessionRequest
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to update chat session: ${error}`);
  }

  return await response.json();
}

/**
 * Get statistics for a chat session
 */
export async function getChatSessionStats(
  sessionId: string
): Promise<ChatSessionStats> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/stats`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get chat session stats: ${error}`);
  }

  return await response.json();
}

/**
 * Get messages for a chat session
 */
export async function getChatMessages(sessionId: string): Promise<ChatMessage[]> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get chat messages: ${error}`);
  }

  return await response.json();
}

/**
 * Get references for a message
 */
export async function getMessageReferences(
  messageId: string
): Promise<EntryReference[]> {
  const response = await fetch(`${API_BASE_URL}/chat/messages/${messageId}/references`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get message references: ${error}`);
  }

  return await response.json();
}

/**
 * Update a chat message
 */
export async function updateChatMessage(
  sessionId: string,
  messageId: string,
  content: string
): Promise<ChatMessage> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages/${messageId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to update chat message: ${error}`);
  }

  return await response.json();
}

/**
 * Delete a chat message
 */
export async function deleteChatMessage(
  sessionId: string,
  messageId: string
): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages/${messageId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to delete chat message: ${error}`);
  }

  return true;
}

/**
 * Delete a range of messages
 */
export async function deleteChatMessagesRange(
  sessionId: string,
  startIndex: number,
  endIndex: number
): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ start_index: startIndex, end_index: endIndex }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to delete message range: ${error}`);
  }

  return true;
}

// Persona API functions

/**
 * Fetch all personas
 */
export async function fetchPersonas(includeDefault: boolean = true): Promise<Persona[]> {
  const url = new URL(`${API_BASE_URL}/api/personas`);
  url.searchParams.append('include_default', includeDefault.toString());

  const response = await fetch(url.toString());

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to fetch personas: ${error}`);
  }

  return await response.json();
}

/**
 * Get a specific persona by ID
 */
export async function getPersona(personaId: string): Promise<Persona> {
  const response = await fetch(`${API_BASE_URL}/api/personas/${personaId}`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get persona: ${error}`);
  }

  return await response.json();
}

/**
 * Get the default persona
 */
export async function getDefaultPersona(): Promise<Persona> {
  const response = await fetch(`${API_BASE_URL}/api/personas/default`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get default persona: ${error}`);
  }

  return await response.json();
}

/**
 * Create a new persona
 */
export async function createPersona(data: PersonaCreate): Promise<Persona> {
  const response = await fetch(`${API_BASE_URL}/api/personas`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to create persona: ${error}`);
  }

  return await response.json();
}

/**
 * Update an existing persona
 */
export async function updatePersona(
  personaId: string,
  data: PersonaUpdate
): Promise<Persona> {
  const response = await fetch(`${API_BASE_URL}/api/personas/${personaId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to update persona: ${error}`);
  }

  return await response.json();
}

/**
 * Delete a persona
 */
export async function deletePersona(personaId: string): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}/api/personas/${personaId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to delete persona: ${error}`);
  }

  return true;
}

/**
 * Update chat session persona
 */
export async function updateChatSessionPersona(
  sessionId: string,
  personaId: string
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ persona_id: personaId }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to update chat session persona: ${error}`);
  }

  return await response.json();
}

/**
 * Create a chat session with the first message atomically (lazy creation)
 */
export async function createChatSessionWithMessage(data: {
  message_content: string;
  session_title?: string;
  temporal_filter?: string;
  model_name?: string;
  persona_id?: string;
}): Promise<{ message: any; references: any[]; session_id: string; session_title: string }> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/lazy-create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to create chat session with message: ${error}`);
  }

  const result = await response.json();
  return {
    message: result.message,
    references: result.references,
    session_id: result.message.metadata?.session_id,
    session_title: result.message.metadata?.session_title
  };
}

/**
 * Clean up empty chat sessions
 */
export async function cleanupEmptySessions(): Promise<{ deleted_count: number }> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/cleanup-empty`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to cleanup empty sessions: ${error}`);
  }

  return await response.json();
}

// Search API functions

export interface ChatSearchFilters {
  dateFrom?: string;
  dateTo?: string;
  sortBy?: 'relevance' | 'date' | 'title';
}

export interface ChatSearchResult {
  session: ChatSession;
  match_type: 'session_title' | 'message_content' | 'context_summary';
  relevance_score: number;
  matched_messages: ChatMessage[];
  highlighted_snippets: string[];
}

export interface MessageSearchResult {
  message: ChatMessage;
  highlighted_content: string;
  relevance_score: number;
  context_before?: string;
  context_after?: string;
}

export interface PaginatedSearchResults {
  results: ChatSearchResult[];
  total: number;
  limit: number;
  offset: number;
  query: string;
  has_next: boolean;
  has_previous: boolean;
}

/**
 * Search chat sessions and messages
 */
export async function searchChatSessions(
  query: string,
  options: {
    limit?: number;
    offset?: number;
    filters?: ChatSearchFilters;
  } = {}
): Promise<PaginatedSearchResults> {
  const { limit = 20, offset = 0, filters = {} } = options;

  const url = new URL(`${API_BASE_URL}/chat/search`);
  url.searchParams.append('q', query);
  url.searchParams.append('limit', limit.toString());
  url.searchParams.append('offset', offset.toString());

  if (filters.sortBy) {
    url.searchParams.append('sort_by', filters.sortBy);
  }
  if (filters.dateFrom) {
    url.searchParams.append('date_from', filters.dateFrom);
  }
  if (filters.dateTo) {
    url.searchParams.append('date_to', filters.dateTo);
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to search chat sessions: ${error}`);
  }

  return await response.json();
}

/**
 * Search within a specific chat session's messages
 */
export async function searchMessagesInSession(
  sessionId: string,
  query: string,
  limit: number = 50
): Promise<MessageSearchResult[]> {
  const url = new URL(`${API_BASE_URL}/chat/sessions/${sessionId}/search`);
  url.searchParams.append('q', query);
  url.searchParams.append('limit', limit.toString());

  const response = await fetch(url.toString());

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to search messages in session: ${error}`);
  }

  return await response.json();
}
