'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import MainLayout from '@/components/layout/MainLayout';
import EntryList from '@/components/entries/EntryList';
import { Pagination, Container, ContentPadding } from '@/components/design-system';
import { HorizontalSearchBar } from '@/components/search/HorizontalSearchBar';
import { Button } from '@/components/ui/button';
import { entriesApi, searchApi, tagsApi } from '@/lib/api';
import { JournalEntry } from '@/lib/types';
import { Search, X } from 'lucide-react';

export default function EntriesPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // State for entries
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const entriesPerPage = 10;

  // Search state
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showFavorites, setShowFavorites] = useState(false);
  const [useSemanticSearch, setUseSemanticSearch] = useState(false);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Initialize search state from URL parameters
  useEffect(() => {
    const searchQuery = searchParams.get('search') || '';
    const tagsParam = searchParams.get('tags');
    const fromParam = searchParams.get('from') || '';
    const toParam = searchParams.get('to') || '';
    const favoritesParam = searchParams.get('favorites') === 'true';
    const semanticParam = searchParams.get('semantic') === 'true';

    // Check if any search parameters are present
    const hasSearchParams = searchQuery || tagsParam || fromParam || toParam || favoritesParam;

    if (hasSearchParams) {
      setQuery(searchQuery);
      setSelectedTags(tagsParam ? tagsParam.split(',') : []);
      setStartDate(fromParam);
      setEndDate(toParam);
      setShowFavorites(favoritesParam);
      setUseSemanticSearch(semanticParam);
      setIsSearchMode(true);
      setIsSearchOpen(true);
    }
  }, [searchParams]);

  // Fetch available tags
  useEffect(() => {
    const fetchTags = async () => {
      try {
        const tags = await tagsApi.getTags();
        setAvailableTags(tags);
      } catch (err) {
        console.error('Failed to fetch tags:', err);
      }
    };

    fetchTags();
  }, []);

  // Update URL parameters based on search state
  const updateUrlParams = useCallback((searchState: {
    query?: string;
    tags?: string[];
    startDate?: string;
    endDate?: string;
    favorites?: boolean;
    semantic?: boolean;
  }) => {
    const params = new URLSearchParams();

    if (searchState.query) {
      params.set('search', searchState.query);
    }
    if (searchState.tags && searchState.tags.length > 0) {
      params.set('tags', searchState.tags.join(','));
    }
    if (searchState.startDate) {
      params.set('from', searchState.startDate);
    }
    if (searchState.endDate) {
      params.set('to', searchState.endDate);
    }
    if (searchState.favorites) {
      params.set('favorites', 'true');
    }
    if (searchState.semantic) {
      params.set('semantic', 'true');
    }

    const queryString = params.toString();
    const newUrl = queryString ? `/entries?${queryString}` : '/entries';
    router.replace(newUrl, { scroll: false });
  }, [router]);

  // Fetch entries (browse mode)
  const fetchEntries = useCallback(async () => {
    try {
      setLoading(true);
      const data = await entriesApi.getEntries({
        limit: entriesPerPage,
        offset: currentPage * entriesPerPage
      });
      setEntries(data);
      setHasMore(data.length === entriesPerPage);
    } catch (err) {
      console.error('Failed to fetch entries:', err);
      setError('Failed to load entries. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [currentPage]);

  // Perform search
  const performSearch = useCallback(async () => {
    if (!query.trim() && selectedTags.length === 0 && !startDate && !endDate && !showFavorites) {
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      let data;
      if (query.trim() && selectedTags.length === 0 && !startDate && !endDate && !showFavorites) {
        data = await searchApi.textSearch(query, useSemanticSearch);
      } else {
        data = await searchApi.advancedSearch({
          query: query.trim() || undefined,
          tags: selectedTags.length > 0 ? selectedTags : undefined,
          startDate: startDate || undefined,
          endDate: endDate || undefined,
          favorite: showFavorites || undefined,
          semantic: useSemanticSearch,
        });
      }

      setEntries(data);
      setHasMore(false); // Search results don't use pagination
    } catch (err) {
      console.error('Search failed:', err);
      setError(useSemanticSearch
        ? 'Failed to perform semantic search. Please ensure Ollama is running on your system.'
        : 'Failed to perform search. Please try again.'
      );
      setEntries([]);
    } finally {
      setIsSearching(false);
    }
  }, [query, selectedTags, startDate, endDate, showFavorites, useSemanticSearch]);

  // Effect to fetch data based on current mode
  useEffect(() => {
    if (isSearchMode) {
      performSearch();
    } else {
      fetchEntries();
    }
  }, [isSearchMode, performSearch, fetchEntries]);

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (hasMore) {
      setCurrentPage(currentPage + 1);
    }
  };

  // Search handlers
  const toggleTag = (tag: string) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];
    setSelectedTags(newTags);

    // Update URL and perform search
    updateUrlParams({
      query,
      tags: newTags,
      startDate,
      endDate,
      favorites: showFavorites,
      semantic: useSemanticSearch
    });
  };

  const handleSearch = () => {
    setIsSearchMode(true);
    updateUrlParams({
      query,
      tags: selectedTags,
      startDate,
      endDate,
      favorites: showFavorites,
      semantic: useSemanticSearch
    });
  };

  const toggleSearchMode = () => {
    if (isSearchMode) {
      // Exit search mode - clear all search state and URL params
      setIsSearchMode(false);
      setIsSearchOpen(false);
      setQuery('');
      setSelectedTags([]);
      setStartDate('');
      setEndDate('');
      setShowFavorites(false);
      setUseSemanticSearch(false);
      setCurrentPage(0);
      router.replace('/entries', { scroll: false });
    } else {
      // Enter search mode
      setIsSearchMode(true);
      setIsSearchOpen(true);
    }
  };

  const clearSearch = () => {
    setQuery('');
    setSelectedTags([]);
    setStartDate('');
    setEndDate('');
    setShowFavorites(false);
    setUseSemanticSearch(false);
    setIsSearchMode(false);
    setIsSearchOpen(false);
    setCurrentPage(0);
    router.replace('/entries', { scroll: false });
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        if (!isSearchOpen) {
          setIsSearchOpen(true);
          setIsSearchMode(true);
        }
      } else if (event.key === 'Escape' && isSearchOpen) {
        setIsSearchOpen(false);
        if (!query && selectedTags.length === 0 && !startDate && !endDate && !showFavorites) {
          setIsSearchMode(false);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isSearchOpen, query, selectedTags, startDate, endDate, showFavorites]);

  return (
    <MainLayout>
      <Container maxWidth="6xl" className="mx-auto">
        <ContentPadding size="md">
          {/* Header with search toggle */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {isSearchMode ? 'Search Results' : 'Your Entries'}
              </h1>
              {isSearchMode && (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {entries.length} {entries.length === 1 ? 'result' : 'results'}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {isSearchMode && (
                <Button
                  onClick={clearSearch}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-1"
                >
                  <X className="h-4 w-4" />
                  Clear Search
                </Button>
              )}
              <Button
                onClick={toggleSearchMode}
                variant={isSearchOpen ? "default" : "outline"}
                size="sm"
                className="flex items-center gap-1"
              >
                <Search className="h-4 w-4" />
                {isSearchOpen ? 'Hide Search' : 'Search'}
                <span className="hidden sm:inline ml-1 text-xs opacity-60">
                  (Ctrl+K)
                </span>
              </Button>
            </div>
          </div>

          {/* Collapsible Search Interface */}
          {isSearchOpen && (
            <div className="mb-6 animate-in fade-in slide-in-from-top-2 duration-300">
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-800/50">
                <HorizontalSearchBar
                  query={query}
                  onQueryChange={setQuery}
                  selectedTags={selectedTags}
                  onTagToggle={toggleTag}
                  startDate={startDate}
                  endDate={endDate}
                  onStartDateChange={setStartDate}
                  onEndDateChange={setEndDate}
                  showFavorites={showFavorites}
                  onShowFavoritesChange={setShowFavorites}
                  useSemanticSearch={useSemanticSearch}
                  onUseSemanticSearchChange={setUseSemanticSearch}
                  availableTags={availableTags}
                  onSearch={handleSearch}
                  isSearching={isSearching || loading}
                />
              </div>
            </div>
          )}

          {/* Loading State */}
          {(loading || isSearching) && (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-300 p-4 rounded-md mb-6">
              {error}
            </div>
          )}

          {/* Entries List */}
          {!loading && !isSearching && (
            <>
              <EntryList
                entries={entries}
                showMoveAction={true}
                headerButtons={
                  isSearchMode && entries.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p className="text-lg font-medium mb-2">No results found</p>
                      <p className="text-sm">Try adjusting your search criteria</p>
                    </div>
                  ) : null
                }
              />

              {/* Pagination - only show in browse mode */}
              {!isSearchMode && entries.length > 0 && (
                <Pagination
                  currentPage={currentPage}
                  hasMore={hasMore}
                  onPrevious={handlePreviousPage}
                  onNext={handleNextPage}
                  className="mt-6"
                />
              )}
            </>
          )}
        </ContentPadding>
      </Container>
    </MainLayout>
  );
}
