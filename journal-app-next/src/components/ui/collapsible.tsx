'use client';

import * as React from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CollapsibleProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
  triggerClassName?: string;
  contentClassName?: string;
  storageKey?: string; // For persisting state in localStorage
  badge?: React.ReactNode; // Optional badge to show next to title
}

export function Collapsible({
  title,
  children,
  defaultOpen = false,
  onOpenChange,
  className,
  triggerClassName,
  contentClassName,
  storageKey,
  badge,
}: CollapsibleProps) {
  const [isOpen, setIsOpen] = React.useState(() => {
    if (storageKey && typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey);
      return stored ? JSON.parse(stored) : defaultOpen;
    }
    return defaultOpen;
  });

  const handleToggle = () => {
    const newState = !isOpen;
    setIsOpen(newState);
    onOpenChange?.(newState);

    if (storageKey && typeof window !== 'undefined') {
      localStorage.setItem(storageKey, JSON.stringify(newState));
    }
  };

  return (
    <div className={cn('border-b border-gray-200 dark:border-gray-700', className)}>
      <button
        type="button"
        onClick={handleToggle}
        className={cn(
          'flex w-full items-center justify-between py-3 px-4',
          'text-left text-sm font-medium text-gray-900 dark:text-gray-100',
          'hover:bg-gray-50 dark:hover:bg-gray-800/50',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
          'transition-colors duration-150',
          triggerClassName
        )}
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2">
          <ChevronDown
            className={cn(
              'h-4 w-4 transition-transform duration-200',
              isOpen && 'rotate-180'
            )}
          />
          <span>{title}</span>
          {badge}
        </div>
      </button>

      <div
        className={cn(
          'transition-all duration-200 ease-in-out',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none',
          contentClassName
        )}
        style={{
          maxHeight: isOpen ? '2000px' : '0',
          overflow: 'hidden',
        }}
      >
        <div className="px-4 pb-4">{children}</div>
      </div>
    </div>
  );
}

interface CollapsibleSectionProps {
  children: React.ReactNode;
  className?: string;
}

export function CollapsibleSection({ children, className }: CollapsibleSectionProps) {
  return <div className={cn('space-y-2', className)}>{children}</div>;
}
