'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { MagnifyingGlassIcon, XMarkIcon, AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { useDebounce } from '@/hooks/useDebounce';

interface ChatSearchBarProps {
  onSearch: (query: string, filters?: SearchFilters) => void;
  onClear: () => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
}

export interface SearchFilters {
  dateFrom?: string;
  dateTo?: string;
  sortBy?: 'relevance' | 'date' | 'title';
}

export const ChatSearchBar: React.FC<ChatSearchBarProps> = ({
  onSearch,
  onClear,
  isLoading = false,
  placeholder = "Search chat sessions and messages...",
  className
}) => {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    sortBy: 'relevance'
  });
  // Debounce search input to avoid excessive API calls
  const debouncedQuery = useDebounce(query, 300);

  // Trigger search when debounced query changes
  useEffect(() => {
    if (debouncedQuery.trim()) {
      onSearch(debouncedQuery, filters);
    } else {
      onClear();
    }
  }, [debouncedQuery]); // eslint-disable-line react-hooks/exhaustive-deps

  // Trigger search when filters change, but only if we have a query
  useEffect(() => {
    if (debouncedQuery.trim()) {
      onSearch(debouncedQuery, filters);
    }
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleQueryChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  }, []);

  const handleClearSearch = useCallback(() => {
    setQuery('');
    onClear();
  }, [onClear]);

  const handleFilterChange = useCallback((newFilters: Partial<SearchFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      handleClearSearch();
    }
  }, [handleClearSearch]);

  return (
    <div className={cn("space-y-3", className)}>
      {/* Main search input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className={cn(
            "h-4 w-4 text-muted-foreground",
            isLoading && "animate-pulse"
          )} />
        </div>

        <input
          type="text"
          value={query}
          onChange={handleQueryChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={cn(
            "block w-full pl-10 pr-12 py-2",
            "text-sm border border-border rounded-md",
            "bg-background placeholder-muted-foreground",
            "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
            "transition-colors"
          )}
        />

        <div className="absolute inset-y-0 right-0 flex items-center space-x-1 pr-2">
          {/* Filters toggle button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "p-1.5 rounded-md transition-colors",
              "hover:bg-muted",
              showFilters && "bg-muted text-primary"
            )}
            title="Search filters"
          >
            <AdjustmentsHorizontalIcon className="h-4 w-4" />
          </button>

          {/* Clear button */}
          {query && (
            <button
              onClick={handleClearSearch}
              className="p-1.5 rounded-md hover:bg-muted transition-colors"
              title="Clear search"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="p-4 border border-border rounded-md bg-muted/30 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Search Filters</h3>
            <button
              onClick={() => setShowFilters(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Date range filters */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Date From</label>
              <input
                type="date"
                value={filters.dateFrom || ''}
                onChange={(e) => handleFilterChange({ dateFrom: e.target.value || undefined })}
                className="w-full px-2 py-1 text-sm border border-border rounded bg-background"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Date To</label>
              <input
                type="date"
                value={filters.dateTo || ''}
                onChange={(e) => handleFilterChange({ dateTo: e.target.value || undefined })}
                className="w-full px-2 py-1 text-sm border border-border rounded bg-background"
              />
            </div>

            {/* Sort by filter */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Sort By</label>
              <select
                value={filters.sortBy || 'relevance'}
                onChange={(e) => handleFilterChange({ sortBy: e.target.value as SearchFilters['sortBy'] })}
                className="w-full px-2 py-1 text-sm border border-border rounded bg-background"
              >
                <option value="relevance">Relevance</option>
                <option value="date">Date</option>
                <option value="title">Title</option>
              </select>
            </div>
          </div>

          {/* Clear filters button */}
          <div className="flex justify-end">
            <button
              onClick={() => handleFilterChange({ dateFrom: undefined, dateTo: undefined, sortBy: 'relevance' })}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Clear Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatSearchBar;
