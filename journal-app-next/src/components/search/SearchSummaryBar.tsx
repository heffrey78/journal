'use client';

import { X, Filter, Calendar, Tag, Star, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface SearchSummaryBarProps {
  resultsCount: number;
  searchQuery?: string;
  selectedTags: string[];
  startDate?: string;
  endDate?: string;
  showFavorites?: boolean;
  searchType?: 'basic' | 'semantic' | 'filtered';
  isLoading?: boolean;
  onClearQuery?: () => void;
  onClearTag?: (tag: string) => void;
  onClearDateRange?: () => void;
  onClearFavorites?: () => void;
  onClearAll?: () => void;
  className?: string;
}

export function SearchSummaryBar({
  resultsCount,
  searchQuery,
  selectedTags,
  startDate,
  endDate,
  showFavorites,
  searchType,
  isLoading = false,
  onClearQuery,
  onClearTag,
  onClearDateRange,
  onClearFavorites,
  onClearAll,
  className,
}: SearchSummaryBarProps) {
  const hasFilters = searchQuery || selectedTags.length > 0 || startDate || endDate || showFavorites;
  const activeFilterCount =
    (searchQuery ? 1 : 0) +
    selectedTags.length +
    (startDate || endDate ? 1 : 0) +
    (showFavorites ? 1 : 0);

  if (!hasFilters && !isLoading) return null;

  const formatDateRange = () => {
    if (startDate && endDate) {
      return `${new Date(startDate).toLocaleDateString()} - ${new Date(endDate).toLocaleDateString()}`;
    } else if (startDate) {
      return `From ${new Date(startDate).toLocaleDateString()}`;
    } else if (endDate) {
      return `Until ${new Date(endDate).toLocaleDateString()}`;
    }
    return '';
  };

  return (
    <div className={cn(
      'bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3',
      className
    )}>
      {/* Results summary */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {isLoading ? (
                'Searching...'
              ) : (
                <>
                  {resultsCount} {resultsCount === 1 ? 'result' : 'results'}
                  {searchType === 'semantic' && (
                    <Badge variant="secondary" className="ml-2 text-xs">
                      Semantic
                    </Badge>
                  )}
                </>
              )}
            </span>
          </div>

          {activeFilterCount > 0 && (
            <Badge variant="outline" className="text-xs">
              {activeFilterCount} {activeFilterCount === 1 ? 'filter' : 'filters'} active
            </Badge>
          )}
        </div>

        {hasFilters && onClearAll && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearAll}
            className="h-7 px-2 text-xs text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          >
            Clear all
          </Button>
        )}
      </div>

      {/* Active filters */}
      {hasFilters && (
        <div className="flex flex-wrap gap-2">
          {/* Search query */}
          {searchQuery && (
            <div className="flex items-center gap-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-md text-xs">
              <Search className="h-3 w-3" />
              <span>&ldquo;{searchQuery}&rdquo;</span>
              {onClearQuery && (
                <button
                  onClick={onClearQuery}
                  className="ml-1 hover:bg-blue-200 dark:hover:bg-blue-800/50 rounded p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
          )}

          {/* Selected tags */}
          {selectedTags.map(tag => (
            <div
              key={tag}
              className="flex items-center gap-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 px-2 py-1 rounded-md text-xs"
            >
              <Tag className="h-3 w-3" />
              <span>{tag}</span>
              {onClearTag && (
                <button
                  onClick={() => onClearTag(tag)}
                  className="ml-1 hover:bg-purple-200 dark:hover:bg-purple-800/50 rounded p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
          ))}

          {/* Date range */}
          {(startDate || endDate) && (
            <div className="flex items-center gap-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-2 py-1 rounded-md text-xs">
              <Calendar className="h-3 w-3" />
              <span>{formatDateRange()}</span>
              {onClearDateRange && (
                <button
                  onClick={onClearDateRange}
                  className="ml-1 hover:bg-green-200 dark:hover:bg-green-800/50 rounded p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
          )}

          {/* Favorites filter */}
          {showFavorites && (
            <div className="flex items-center gap-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded-md text-xs">
              <Star className="h-3 w-3" />
              <span>Favorites only</span>
              {onClearFavorites && (
                <button
                  onClick={onClearFavorites}
                  className="ml-1 hover:bg-yellow-200 dark:hover:bg-yellow-800/50 rounded p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
