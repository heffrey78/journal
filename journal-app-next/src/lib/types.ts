// Journal entry interfaces
export interface JournalEntry {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  favorite: boolean;
  folder?: string;
  images?: string[];
}

export interface CreateJournalEntryInput {
  title: string;
  content: string;
  tags?: string[];
  images?: string[];
  folder?: string;
}

export interface UpdateJournalEntryInput {
  title?: string;
  content?: string;
  tags?: string[];
  favorite?: boolean;
  images?: string[];
}

// Import interfaces
export interface ImportResult {
  total: number;
  successful: number;
  failed: number;
  entries: {
    id: string;
    filename: string;
    title: string;
  }[];
  failures: {
    filename: string;
    error: string;
  }[];
}

// Batch analysis interfaces
export interface BatchAnalysis {
  id: string;
  title: string;
  entry_ids: string[];
  date_range: string;
  created_at: string;
  summary: string;
  key_themes: string[];
  mood_trends: Record<string, number>;
  notable_insights: string[];
  prompt_type: string;
}

export interface BatchAnalysisRequest {
  entry_ids: string[];
  title?: string;
  prompt_type: string;
}

export interface BatchAnalysisSummary {
  id: string;
  title: string;
  created_at: string;
  prompt_type: string;
  entry_count: number;
}

// Search interfaces
export interface SearchQuery {
  q?: string;
  tags?: string[];
  start_date?: string;
  end_date?: string;
  favorite?: boolean;
}

// Theme interfaces
export type ColorTheme = 'light' | 'dark' | 'system';
export type FontFamily = 'Geist Sans' | 'Geist Mono' | 'serif';

export interface ThemePreferences {
  colorTheme: ColorTheme;
  fontFamily: FontFamily;
  fontSize: number;
  lineHeight: number;
  complimentaryColors?: {
    header?: string;
    sidebar?: string;
    footer?: string;
  };
}

// Settings interface
export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  fontFamily: string;
  fontSize: number;
  lineHeight: number;
  showWordCount: boolean;
  autoSaveInterval: number; // in seconds
}

// Analysis prompt type interface
export interface PromptType {
  id: string;
  name: string;
  prompt: string;
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
  prompt_types?: PromptType[];
}
