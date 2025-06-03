'use client';

import { useState } from 'react';
import { Search, Filter, X, Calendar, Tag, Star, Zap, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { CompactTagSelector } from './CompactTagSelector';
import { CompactDateRange } from './CompactDateRange';

interface HorizontalSearchBarProps {
  query: string;
  onQueryChange: (query: string) => void;
  selectedTags: string[];
  onTagToggle: (tag: string) => void;
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  showFavorites: boolean;
  onShowFavoritesChange: (show: boolean) => void;
  useSemanticSearch: boolean;
  onUseSemanticSearchChange: (use: boolean) => void;
  availableTags: string[];
  onSearch: () => void;
  isSearching?: boolean;
  className?: string;
}

export function HorizontalSearchBar({
  query,
  onQueryChange,
  selectedTags,
  onTagToggle,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  showFavorites,
  onShowFavoritesChange,
  useSemanticSearch,
  onUseSemanticSearchChange,
  availableTags,
  onSearch,
  isSearching = false,
  className,
}: HorizontalSearchBarProps) {
  const [showFilters, setShowFilters] = useState(false);

  const hasActiveFilters = selectedTags.length > 0 || startDate || endDate || showFavorites;
  const activeFilterCount = selectedTags.length + (startDate || endDate ? 1 : 0) + (showFavorites ? 1 : 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch();
  };

  const clearAll = () => {
    onQueryChange('');
    selectedTags.forEach(tag => onTagToggle(tag));
    onStartDateChange('');
    onEndDateChange('');
    onShowFavoritesChange(false);
  };

  const clearTag = (tag: string) => {
    onTagToggle(tag);
  };

  const clearDateRange = () => {
    onStartDateChange('');
    onEndDateChange('');
  };

  return (
    <div className={cn('bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm', className)}>
      {/* Main search bar */}
      <form onSubmit={handleSubmit} className="flex items-center p-3 gap-3">
        {/* Search input */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Search entries..."
            className="pl-9 h-9 border-gray-200 dark:border-gray-700"
          />
        </div>

        {/* Filter toggle button */}
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            'h-9 px-3 gap-2',
            hasActiveFilters && 'border-blue-500 text-blue-600 dark:text-blue-400',
            showFilters && 'bg-gray-100 dark:bg-gray-800'
          )}
        >
          <Filter className="h-4 w-4" />
          <span className="hidden sm:inline">Filters</span>
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="h-5 text-xs px-1.5">
              {activeFilterCount}
            </Badge>
          )}
          <ChevronDown className={cn('h-3 w-3 transition-transform', showFilters && 'rotate-180')} />
        </Button>

        {/* Search button */}
        <Button
          type="submit"
          disabled={!query.trim() && !hasActiveFilters}
          isLoading={isSearching}
          className="h-9 px-4 gap-2"
        >
          {useSemanticSearch ? (
            <>
              <Zap className="h-3 w-3" />
              <span className="hidden sm:inline">AI Search</span>
            </>
          ) : (
            <>
              <Search className="h-3 w-3" />
              <span className="hidden sm:inline">Search</span>
            </>
          )}
        </Button>
      </form>

      {/* Active filters summary (always visible when filters exist) */}
      {hasActiveFilters && (
        <div className="px-3 pb-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500 dark:text-gray-400">Active filters:</span>

            {/* Search query */}
            {query && (
              <div className="flex items-center gap-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-md text-xs">
                <Search className="h-3 w-3" />
                <span>&ldquo;{query}&rdquo;</span>
                <button
                  onClick={() => onQueryChange('')}
                  className="ml-1 hover:bg-blue-200 dark:hover:bg-blue-800/50 rounded p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            )}

            {/* Selected tags */}
            {selectedTags.slice(0, 3).map(tag => (
              <div
                key={tag}
                className="flex items-center gap-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 px-2 py-1 rounded-md text-xs"
              >
                <Tag className="h-3 w-3" />
                <span>{tag}</span>
                <button
                  onClick={() => clearTag(tag)}
                  className="ml-1 hover:bg-purple-200 dark:hover:bg-purple-800/50 rounded p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}

            {selectedTags.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{selectedTags.length - 3} more tags
              </Badge>
            )}

            {/* Date range */}
            {(startDate || endDate) && (
              <div className="flex items-center gap-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-2 py-1 rounded-md text-xs">
                <Calendar className="h-3 w-3" />
                <span>
                  {startDate && endDate ? (
                    `${new Date(startDate).toLocaleDateString()} - ${new Date(endDate).toLocaleDateString()}`
                  ) : startDate ? (
                    `From ${new Date(startDate).toLocaleDateString()}`
                  ) : (
                    `Until ${new Date(endDate).toLocaleDateString()}`
                  )}
                </span>
                <button
                  onClick={clearDateRange}
                  className="ml-1 hover:bg-green-200 dark:hover:bg-green-800/50 rounded p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            )}

            {/* Favorites filter */}
            {showFavorites && (
              <div className="flex items-center gap-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded-md text-xs">
                <Star className="h-3 w-3" />
                <span>Favorites only</span>
                <button
                  onClick={() => onShowFavoritesChange(false)}
                  className="ml-1 hover:bg-yellow-200 dark:hover:bg-yellow-800/50 rounded p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            )}

            {/* Clear all button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAll}
              className="h-6 px-2 text-xs text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            >
              Clear all
            </Button>
          </div>
        </div>
      )}

      {/* Collapsible filter panel */}
      {showFilters && (
        <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="p-4">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Search Options */}
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">Search Options</h3>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useSemanticSearch}
                      onChange={(e) => onUseSemanticSearchChange(e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span>Use AI semantic search</span>
                  </label>
                  <label className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showFavorites}
                      onChange={(e) => onShowFavoritesChange(e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span>Show only favorites</span>
                  </label>
                </div>
              </div>

              {/* Tags */}
              {availableTags.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Tags
                    {selectedTags.length > 0 && (
                      <Badge variant="secondary" className="ml-2 text-xs">
                        {selectedTags.length} selected
                      </Badge>
                    )}
                  </h3>
                  <CompactTagSelector
                    availableTags={availableTags}
                    selectedTags={selectedTags}
                    onTagToggle={onTagToggle}
                    maxVisibleTags={12}
                  />
                </div>
              )}

              {/* Date Range */}
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Date Range
                  {(startDate || endDate) && (
                    <Badge variant="secondary" className="ml-2 text-xs">
                      Active
                    </Badge>
                  )}
                </h3>
                <CompactDateRange
                  startDate={startDate}
                  endDate={endDate}
                  onStartDateChange={onStartDateChange}
                  onEndDateChange={onEndDateChange}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
