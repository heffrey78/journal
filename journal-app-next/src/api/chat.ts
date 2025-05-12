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
  ChatListResponse
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

  const sessions = await response.json();

  // TODO: Add total count from headers or response when backend supports it
  return {
    sessions,
    total: sessions.length // This is a placeholder until backend provides total count
  };
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
