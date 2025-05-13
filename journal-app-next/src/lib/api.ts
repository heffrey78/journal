import axios from 'axios';
import type { BatchAnalysis, BatchAnalysisRequest, BatchAnalysisSummary } from './types';

// Configure base URL for API requests
const api = axios.create({
  // Use explicit http://localhost:8000 instead of relying only on environment variables
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  // Add timeout to prevent hanging requests
  timeout: 10000,
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log connection errors with more context
    if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')) {
      console.error('API connection error. Make sure the backend server is running at:',
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
    }
    return Promise.reject(error);
  }
);

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

// Image metadata interface
export interface ImageMetadata {
  id: string;
  filename: string;
  mime_type: string;
  size: number;
  width?: number;
  height?: number;
  entry_id?: string;
  description?: string;
  created_at: string;
  url?: string;
}

// LLM Configuration interface
export interface LLMConfig {
  id?: string;
  model_name: string;
  embedding_model: string;
  temperature: number;
  max_tokens: number;
  max_retries: number;
  retry_delay: number;
  system_prompt: string;
  semantic_search_threshold?: number;
  prompt_types?: Array<{
    id: string;
    name: string;
    prompt: string;
  }>;
  created_at?: string;
  updated_at?: string;
}

// API functions for entries
export const entriesApi = {
  // Get all entries
  getEntries: async (params?: {
    limit?: number;
    offset?: number;
    dateFrom?: string;
    dateTo?: string;
    tag?: string;
  }): Promise<JournalEntry[]> => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.dateFrom) queryParams.append('date_from', params.dateFrom);
    if (params?.dateTo) queryParams.append('date_to', params.dateTo);
    if (params?.tag) queryParams.append('tag', params.tag);

    const queryString = queryParams.toString();
    const url = `/entries/${queryString ? `?${queryString}` : ''}`;
    const response = await api.get(url);
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
    const response = await api.patch(`/entries/${id}`, entry);
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

// API functions for batch analysis
export const batchAnalysisApi = {
  // Create a new batch analysis
  analyzeBatch: async (request: BatchAnalysisRequest): Promise<BatchAnalysis> => {
    const response = await api.post('/batch/analyze', request);
    return response.data;
  },

  // Get all batch analyses with pagination
  getBatchAnalyses: async (
    params?: { limit?: number; offset?: number }
  ): Promise<BatchAnalysis[]> => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const queryString = queryParams.toString();
    const url = `/batch/analyses${queryString ? `?${queryString}` : ''}`;

    const response = await api.get(url);
    return response.data;
  },

  // Get a specific batch analysis by ID
  getBatchAnalysis: async (batchId: string): Promise<BatchAnalysis> => {
    const response = await api.get(`/batch/analyses/${batchId}`);
    return response.data;
  },

  // Delete a batch analysis
  deleteBatchAnalysis: async (batchId: string): Promise<void> => {
    await api.delete(`/batch/analyses/${batchId}`);
  },

  // Get batch analyses for a specific entry
  getEntryBatchAnalyses: async (entryId: string): Promise<BatchAnalysisSummary[]> => {
    const response = await api.get(`/entries/${entryId}/batch-analyses`);
    return response.data;
  },

  // Utility function to get different prompt types for batch analysis
  getAvailablePromptTypes: (): { id: string; name: string; description: string }[] => {
    return [
      {
        id: 'weekly',
        name: 'Weekly Review',
        description: 'Analyze entries from a week to identify patterns, themes, and insights.'
      },
      {
        id: 'monthly',
        name: 'Monthly Review',
        description: 'Analyze monthly entries to identify long-term trends and developments.'
      },
      {
        id: 'topic',
        name: 'Topic Analysis',
        description: 'Analyze entries related to a specific topic or theme.'
      },
      {
        id: 'quarterly',
        name: 'Quarterly Review',
        description: 'Analyze entries from a quarter for major themes and significant changes.'
      },
      {
        id: 'project',
        name: 'Project Analysis',
        description: 'Track project evolution, challenges, solutions, and insights over time.'
      },
    ];
  },
};

// LLM API functions
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

// API functions for images
export const imagesApi = {
  // Upload an image
  uploadImage: async (file: File, entryId?: string, description?: string): Promise<ImageMetadata> => {
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('file', file);

    if (entryId) {
      formData.append('entry_id', entryId);
    }

    if (description) {
      formData.append('description', description);
    }

    // Use custom config for multipart form data
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    };

    const response = await api.post('/images/upload', formData, config);
    return response.data;
  },

  // Get image metadata
  getImageInfo: async (imageId: string): Promise<ImageMetadata> => {
    const response = await api.get(`/images/${imageId}/info`);
    return {
      ...response.data,
      url: `${api.defaults.baseURL}/images/${imageId}`,
    };
  },

  // Get all images for an entry
  getEntryImages: async (entryId: string): Promise<ImageMetadata[]> => {
    const response = await api.get(`/entries/${entryId}/images`);
    // Add URL property to each image for convenience
    return response.data.map((img: ImageMetadata) => ({
      ...img,
      url: `${api.defaults.baseURL}/images/${img.id}`,
    }));
  },

  // Delete an image
  deleteImage: async (imageId: string): Promise<void> => {
    await api.delete(`/images/${imageId}`);
  },

  // Update image metadata
  updateImageMetadata: async (
    imageId: string,
    updates: { description?: string; entry_id?: string }
  ): Promise<ImageMetadata> => {
    const formData = new FormData();

    if (updates.description !== undefined) {
      formData.append('description', updates.description);
    }

    if (updates.entry_id !== undefined) {
      formData.append('entry_id', updates.entry_id);
    }

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    };

    const response = await api.patch(`/images/${imageId}`, formData, config);
    return {
      ...response.data,
      url: `${api.defaults.baseURL}/images/${response.data.id}`,
    };
  },

  // Get orphaned images (not associated with any entry)
  getOrphanedImages: async (): Promise<ImageMetadata[]> => {
    const response = await api.get('/images/?orphaned=true');
    return response.data.map((img: ImageMetadata) => ({
      ...img,
      url: `${api.defaults.baseURL}/images/${img.id}`,
    }));
  },
};

// API functions for journal organization
export const organizationApi = {
  // Get all folders
  getFolders: async (): Promise<string[]> => {
    const response = await api.get('/folders/');
    return response.data;
  },

  // Create a new folder
  createFolder: async (folderName: string): Promise<{status: string; message: string}> => {
    const response = await api.post(`/folders/?folder_name=${encodeURIComponent(folderName)}`);
    return response.data;
  },

  // Get entries in a folder
  getEntriesByFolder: async (
    folder: string,
    params?: {
      limit?: number;
      offset?: number;
      dateFrom?: string;
      dateTo?: string;
    }
  ): Promise<JournalEntry[]> => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.dateFrom) queryParams.append('date_from', params.dateFrom);
    if (params?.dateTo) queryParams.append('date_to', params.dateTo);

    const queryString = queryParams.toString();
    const url = `/folders/${encodeURIComponent(folder)}/entries${queryString ? `?${queryString}` : ''}`;
    const response = await api.get(url);
    return response.data;
  },

  // Get favorite entries
  getFavoriteEntries: async (
    params?: {
      limit?: number;
      offset?: number;
      dateFrom?: string;
      dateTo?: string;
      tag?: string;
    }
  ): Promise<JournalEntry[]> => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.dateFrom) queryParams.append('date_from', params.dateFrom);
    if (params?.dateTo) queryParams.append('date_to', params.dateTo);
    if (params?.tag) queryParams.append('tag', params.tag);

    const queryString = queryParams.toString();
    const url = `/entries/favorites${queryString ? `?${queryString}` : ''}`;
    const response = await api.get(url);
    return response.data;
  },

  // Get entries by date (calendar view)
  getEntriesByDate: async (
    date: string, // Format: YYYY-MM-DD
    params?: {
      limit?: number;
      offset?: number;
    }
  ): Promise<JournalEntry[]> => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const queryString = queryParams.toString();
    const url = `/calendar/${date}${queryString ? `?${queryString}` : ''}`;
    const response = await api.get(url);
    return response.data;
  },

  // Batch update folder for multiple entries
  batchUpdateFolder: async (
    entryIds: string[],
    folder: string | null
  ): Promise<{status: string; message: string; updated_count: number}> => {
    const url = `/batch/update-folder${folder ? `?folder=${encodeURIComponent(folder)}` : ''}`;
    const response = await api.post(url, { entry_ids: entryIds });
    return response.data;
  },

  // Batch toggle favorite status for multiple entries
  batchToggleFavorite: async (
    entryIds: string[],
    favorite: boolean
  ): Promise<{status: string; message: string; updated_count: number}> => {
    const url = `/batch/favorite?favorite=${favorite}`;
    const response = await api.post(url, { entry_ids: entryIds });
    return response.data;
  },
};

export default {
  entriesApi,
  searchApi,
  tagsApi,
  llmApi,
  imagesApi,
  organizationApi,
  batchAnalysisApi
};
