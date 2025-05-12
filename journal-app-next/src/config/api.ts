/**
 * API configuration settings
 */

// Backend API base URL - prefer environment variable if set, otherwise use 127.0.0.1 (explicit IPv4)
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// Chat-related endpoints
export const CHAT_API = {
  SESSIONS: `${API_BASE_URL}/chat/sessions`,
  SESSION: (sessionId: string) => `${API_BASE_URL}/chat/sessions/${sessionId}`,
  MESSAGES: (sessionId: string) => `${API_BASE_URL}/chat/sessions/${sessionId}/messages`,
  MESSAGE: (sessionId: string, messageId: string) => `${API_BASE_URL}/chat/sessions/${sessionId}/messages/${messageId}`,
  STREAM: `${API_BASE_URL}/chat/stream`
};
