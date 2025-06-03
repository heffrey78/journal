'use client';

import { useState, useMemo } from 'react';
import { X, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

interface CompactTagSelectorProps {
  availableTags: string[];
  selectedTags: string[];
  onTagToggle: (tag: string) => void;
  maxVisibleTags?: number;
  className?: string;
}

export function CompactTagSelector({
  availableTags,
  selectedTags,
  onTagToggle,
  maxVisibleTags = 15,
  className,
}: CompactTagSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showAll, setShowAll] = useState(false);

  // Filter tags based on search query
  const filteredTags = useMemo(() => {
    if (!searchQuery.trim()) return availableTags;

    const query = searchQuery.toLowerCase();
    return availableTags.filter(tag =>
      tag.toLowerCase().includes(query)
    );
  }, [availableTags, searchQuery]);

  // Determine which tags to show
  const visibleTags = useMemo(() => {
    // Always show selected tags
    const selected = filteredTags.filter(tag => selectedTags.includes(tag));
    const unselected = filteredTags.filter(tag => !selectedTags.includes(tag));

    if (showAll || filteredTags.length <= maxVisibleTags) {
      return [...selected, ...unselected];
    }

    // Show selected tags + top unselected tags up to maxVisibleTags
    const remainingSlots = Math.max(0, maxVisibleTags - selected.length);
    return [...selected, ...unselected.slice(0, remainingSlots)];
  }, [filteredTags, selectedTags, showAll, maxVisibleTags]);

  const hiddenCount = filteredTags.length - visibleTags.length;

  return (
    <div className={cn('space-y-3', className)}>
      {/* Search input */}
      {availableTags.length > 10 && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tags..."
            className="pl-9 h-8 text-sm"
          />
        </div>
      )}

      {/* Selected tags summary */}
      {selectedTags.length > 0 && (
        <div className="flex items-center gap-2 pb-2 border-b border-gray-200 dark:border-gray-700">
          <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
            Selected ({selectedTags.length}):
          </span>
          <div className="flex flex-wrap gap-1">
            {selectedTags.map(tag => (
              <Badge
                key={tag}
                variant="secondary"
                className="h-6 text-xs cursor-pointer group"
                onClick={() => onTagToggle(tag)}
              >
                {tag}
                <X className="ml-1 h-3 w-3 opacity-50 group-hover:opacity-100" />
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Tag grid */}
      <div className="flex flex-wrap gap-1.5">
        {visibleTags.map(tag => {
          const isSelected = selectedTags.includes(tag);
          return (
            <button
              key={tag}
              type="button"
              onClick={() => onTagToggle(tag)}
              className={cn(
                'px-2.5 py-1 text-xs rounded-md transition-all duration-150',
                'border hover:shadow-sm',
                isSelected
                  ? 'bg-blue-500 text-white border-blue-600 hover:bg-blue-600'
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300',
                  'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              )}
            >
              {tag}
            </button>
          );
        })}
      </div>

      {/* Show more/less button */}
      {hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setShowAll(!showAll)}
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
        >
          {showAll ? 'Show less' : `Show ${hiddenCount} more`}
        </button>
      )}

      {/* No results message */}
      {filteredTags.length === 0 && searchQuery && (
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-2">
          No tags match &ldquo;{searchQuery}&rdquo;
        </p>
      )}
    </div>
  );
}
