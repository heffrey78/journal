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
};

// API functions for search
export const searchApi = {
  // Basic text search
  textSearch: async (query: string): Promise<JournalEntry[]> => {
    const response = await api.get(`/search?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  // Advanced search with filters
  advancedSearch: async (params: {
    query?: string,
    tags?: string[],
    startDate?: string,
    endDate?: string,
    favorite?: boolean
  }): Promise<JournalEntry[]> => {
    const response = await api.post('/search/advanced', params);
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

export default { entriesApi, searchApi, tagsApi };
