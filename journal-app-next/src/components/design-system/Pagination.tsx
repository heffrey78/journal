import React from 'react';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PaginationProps {
  currentPage: number;
  totalPages?: number;
  hasMore?: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onFirst?: () => void;
  onLast?: () => void;
  showFirstLast?: boolean;
  showPageNumbers?: boolean;
  pageLabel?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Unified Pagination component for consistent pagination across the application
 * Supports both totalPages mode (when total is known) and hasMore mode (for infinite scroll)
 */
export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  hasMore = true,
  onPrevious,
  onNext,
  onFirst,
  onLast,
  showFirstLast = false,
  showPageNumbers = true,
  pageLabel = 'Page',
  className,
  size = 'md',
}) => {
  const isFirstPage = currentPage === 0;
  const isLastPage = totalPages ? currentPage >= totalPages - 1 : !hasMore;

  const sizeClasses = {
    sm: 'gap-1',
    md: 'gap-2',
    lg: 'gap-3',
  };

  const buttonSize = {
    sm: 'sm' as const,
    md: 'default' as const,
    lg: 'lg' as const,
  };

  return (
    <div
      className={cn(
        'flex justify-between items-center pt-4 border-t border-border',
        className
      )}
    >
      {/* Left side - Previous controls */}
      <div className={cn('flex items-center', sizeClasses[size])}>
        {showFirstLast && onFirst && (
          <Button
            variant="outline"
            size={buttonSize[size]}
            onClick={onFirst}
            disabled={isFirstPage}
            aria-label="Go to first page"
          >
            <ChevronsLeft className="h-4 w-4" />
            <span className="sr-only">First</span>
          </Button>
        )}
        <Button
          variant="outline"
          size={buttonSize[size]}
          onClick={onPrevious}
          disabled={isFirstPage}
          className="flex items-center gap-1"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </Button>
      </div>

      {/* Center - Page info */}
      {showPageNumbers && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            {pageLabel} {currentPage + 1}
            {totalPages && (
              <>
                {' of '}
                <span className="font-medium">{totalPages}</span>
              </>
            )}
          </span>
        </div>
      )}

      {/* Right side - Next controls */}
      <div className={cn('flex items-center', sizeClasses[size])}>
        <Button
          variant="outline"
          size={buttonSize[size]}
          onClick={onNext}
          disabled={isLastPage}
          className="flex items-center gap-1"
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
        {showFirstLast && onLast && totalPages && (
          <Button
            variant="outline"
            size={buttonSize[size]}
            onClick={onLast}
            disabled={isLastPage}
            aria-label="Go to last page"
          >
            <ChevronsRight className="h-4 w-4" />
            <span className="sr-only">Last</span>
          </Button>
        )}
      </div>
    </div>
  );
};

export default Pagination;
