// Journal entry interfaces
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

export interface CreateJournalEntryInput {
  title: string;
  content: string;
  tags?: string[];
  images?: string[];
}

export interface UpdateJournalEntryInput {
  title?: string;
  content?: string;
  tags?: string[];
  favorite?: boolean;
  images?: string[];
}

// Search interfaces
export interface SearchQuery {
  q?: string;
  tags?: string[];
  start_date?: string;
  end_date?: string;
  favorite?: boolean;
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
