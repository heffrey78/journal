'use client';

import { useState, useEffect } from 'react';
import MainLayout from '@/components/layout/MainLayout';
import EntryList from '@/components/entries/EntryList';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { searchApi, tagsApi } from '@/lib/api';
import { JournalEntry } from '@/lib/types';
import Container from '@/components/layout/Container';
import ContentPadding from '@/components/layout/ContentPadding';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showFavorites, setShowFavorites] = useState(false);
  const [useSemanticSearch, setUseSemanticSearch] = useState(false); // New state for semantic search
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  const [results, setResults] = useState<JournalEntry[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchType, setSearchType] = useState<'basic' | 'semantic' | 'filtered'>('basic'); // Track search type for UI

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

  const handleBasicSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const data = await searchApi.textSearch(query, useSemanticSearch);
      setResults(data);
      setHasSearched(true);
      setSearchType(useSemanticSearch ? 'semantic' : 'basic');
    } catch (err) {
      console.error('Search failed:', err);
      setError('Failed to perform search. Please try again.');
      if (useSemanticSearch) {
        setError('Failed to perform semantic search. Please ensure Ollama is running on your system.');
      }
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAdvancedSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    setIsSearching(true);
    setError(null);

    try {
      const data = await searchApi.advancedSearch({
        query: query.trim() || undefined,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        favorite: showFavorites || undefined,
        semantic: useSemanticSearch,
      });

      setResults(data);
      setHasSearched(true);
      setSearchType(useSemanticSearch ? 'semantic' : 'filtered');
    } catch (err) {
      console.error('Advanced search failed:', err);
      setError('Failed to perform search. Please try again.');
      if (useSemanticSearch) {
        setError('Failed to perform semantic search. Please ensure Ollama is running on your system.');
      }
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const toggleTag = (tag: string) => {
    setSelectedTags((prevTags) =>
      prevTags.includes(tag)
        ? prevTags.filter(t => t !== tag)
        : [...prevTags, tag]
    );
  };

  return (
    <MainLayout>
      <Container maxWidth="4xl" className="mx-auto">
        <ContentPadding size="md">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Search Journal Entries</h1>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Search Form */}
            <div className="lg:col-span-1">
              <Card className="mb-6 overflow-hidden">
                <div className="p-6">
                  <form onSubmit={handleBasicSearch} className="mb-8">
                    <div className="mb-4">
                      <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Quick Search
                      </label>
                      <div className="flex">
                        <input
                          type="text"
                          id="search"
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder="Search entries..."
                          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-l-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <Button
                          type="submit"
                          disabled={!query.trim() || isSearching}
                          isLoading={isSearching}
                          className="rounded-l-none"
                        >
                          Search
                        </Button>
                      </div>

                      {/* Semantic search checkbox */}
                      <div className="mt-3">
                        <label className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={useSemanticSearch}
                            onChange={(e) => setUseSemanticSearch(e.target.checked)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span>Use semantic search (powered by Ollama)</span>
                        </label>
                      </div>
                    </div>
                  </form>

                  <div>
                    <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-6">Advanced Search</h2>
                    <form onSubmit={handleAdvancedSearch} className="space-y-6">
                      {availableTags.length > 0 && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                            Filter by Tags
                          </label>
                          <div className="flex flex-wrap gap-2">
                            {availableTags.map(tag => (
                              <button
                                key={tag}
                                type="button"
                                onClick={() => toggleTag(tag)}
                                className={`text-sm px-3 py-1 rounded-full ${
                                  selectedTags.includes(tag)
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                }`}
                              >
                                {tag}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                          Date Range
                        </label>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label htmlFor="start-date" className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                              From
                            </label>
                            <input
                              type="date"
                              id="start-date"
                              value={startDate}
                              onChange={(e) => setStartDate(e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                          <div>
                            <label htmlFor="end-date" className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                              To
                            </label>
                            <input
                              type="date"
                              id="end-date"
                              value={endDate}
                              onChange={(e) => setEndDate(e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center py-2">
                        <input
                          type="checkbox"
                          id="favorites"
                          checked={showFavorites}
                          onChange={(e) => setShowFavorites(e.target.checked)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="favorites" className="ml-3 block text-sm text-gray-700 dark:text-gray-300">
                          Show only favorites
                        </label>
                      </div>

                      <Button
                        type="submit"
                        isLoading={isSearching}
                        className="w-full mt-4"
                      >
                        Search with Filters
                      </Button>
                    </form>
                  </div>
                </div>
              </Card>
            </div>

            {/* Search Results */}
            <div className="lg:col-span-2">
              {error && (
                <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-300 p-6 rounded-md mb-6">
                  {error}
                </div>
              )}

              {isSearching ? (
                <div className="flex justify-center py-12">
                  <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              ) : hasSearched ? (
                <>
                  <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-white">
                    {searchType === 'semantic' && (
                      <span className="text-blue-500 dark:text-blue-400 mr-2">[Semantic]</span>
                    )}
                    {results.length} {results.length === 1 ? 'result' : 'results'} found
                  </h2>
                  <EntryList entries={results} />

                  {searchType === 'semantic' && results.length > 0 && (
                    <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                      <p className="text-sm">
                        <strong>Semantic search:</strong> Results are ranked by relevance to your query using AI-powered embeddings.
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-16 text-gray-500 dark:text-gray-400">
                  <p>Enter a search query to find journal entries</p>
                </div>
              )}
            </div>
          </div>
        </ContentPadding>
      </Container>
    </MainLayout>
  );
}
