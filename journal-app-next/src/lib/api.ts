import axios from 'axios';

// Configure base URL for API requests
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Journal entry type definitions
export interface JournalEntry {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  favorite: boolean;
  images?: string[];
}

// LLM analysis/summary interface
export interface EntrySummary {
  summary: string;
  key_topics: string[];
  mood: string;
  prompt_type?: string;
  created_at?: string;
  id?: string;
}

// API functions for entries
export const entriesApi = {
  // Get all entries
  getEntries: async (): Promise<JournalEntry[]> => {
    const response = await api.get('/entries');
    return response.data;
  },

  // Get a single entry by ID
  getEntry: async (id: string): Promise<JournalEntry> => {
    const response = await api.get(`/entries/${id}`);
    return response.data;
  },

  // Create a new entry
  createEntry: async (entry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'>): Promise<JournalEntry> => {
    const response = await api.post('/entries', entry);
    return response.data;
  },

  // Update an existing entry
  updateEntry: async (id: string, entry: Partial<JournalEntry>): Promise<JournalEntry> => {
    const response = await api.put(`/entries/${id}`, entry);
    return response.data;
  },

  // Delete an entry
  deleteEntry: async (id: string): Promise<void> => {
    await api.delete(`/entries/${id}`);
  },

  // Toggle favorite status
  toggleFavorite: async (id: string, favorite: boolean): Promise<JournalEntry> => {
    const response = await api.put(`/entries/${id}/favorite`, { favorite });
    return response.data;
  },

  // Generate a summary/analysis for an entry
  summarizeEntry: async (id: string, promptType: string = 'default'): Promise<EntrySummary> => {
    const response = await api.post(`/entries/${id}/summarize/custom`, { prompt_type: promptType });
    return response.data;
  },

  // Save a summary as favorite
  saveFavoriteSummary: async (id: string, summary: EntrySummary): Promise<void> => {
    await api.post(`/entries/${id}/summaries/favorite`, summary);
  },

  // Get favorite summaries for an entry
  getFavoriteSummaries: async (id: string): Promise<EntrySummary[]> => {
    const response = await api.get(`/entries/${id}/summaries/favorite`);
    return response.data;
  },
};

// API functions for search
export const searchApi = {
  // Basic text search
  textSearch: async (query: string, useSemanticSearch: boolean = false): Promise<JournalEntry[]> => {
    const url = `/entries/search/?query=${encodeURIComponent(query)}${useSemanticSearch ? '&semantic=true' : ''}`;
    const response = await api.get(url);
    return response.data;
  },

  // Advanced search with filters
  advancedSearch: async (params: {
    query?: string,
    tags?: string[],
    startDate?: string,
    endDate?: string,
    favorite?: boolean,
    semantic?: boolean
  }): Promise<JournalEntry[]> => {
    // Map frontend params to backend API format
    const apiParams = {
      query: params.query || "",
      tags: params.tags,
      date_from: params.startDate,
      date_to: params.endDate,
      favorite: params.favorite,
      semantic: params.semantic || false
    };

    const response = await api.post('/entries/search/', apiParams);
    return response.data;
  },
};

// API functions for tags
export const tagsApi = {
  // Get all tags
  getTags: async (): Promise<string[]> => {
    const response = await api.get('/tags');
    return response.data;
  },
};

// API functions for LLM settings
export const llmApi = {
  // Get LLM configuration
  getLLMConfig: async (): Promise<LLMConfig> => {
    const response = await api.get('/config/llm');
    return response.data;
  },

  // Update LLM configuration
  updateLLMConfig: async (config: LLMConfig): Promise<LLMConfig> => {
    const response = await api.put('/config/llm', config);
    return response.data;
  },

  // Get available Ollama models
  getAvailableModels: async (): Promise<string[]> => {
    try {
      const response = await api.get('/config/available-models');
      return response.data.models;
    } catch (error) {
      console.error('Failed to fetch available models:', error);
      return [];
    }
  },

  // Test LLM connection
  testConnection: async (): Promise<{status: string, message: string}> => {
    try {
      const response = await api.get('/config/llm/test');
      return response.data;
    } catch (error) {
      console.error('LLM connection test failed:', error);
      return { status: 'error', message: 'Failed to connect to LLM service.' };
    }
  }
};

export default { entriesApi, searchApi, tagsApi, llmApi };
