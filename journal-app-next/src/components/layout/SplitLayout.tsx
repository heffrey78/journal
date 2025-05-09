'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface SplitLayoutProps {
  children: React.ReactNode;
  className?: string;
  sidebar?: React.ReactNode;
  sidebarPosition?: 'left' | 'right';
  sidebarWidth?: string;
  sidebarClassName?: string;
  contentClassName?: string;
  stackBelowBreakpoint?: 'sm' | 'md' | 'lg' | 'xl';
  reversed?: boolean;
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

/**
 * SplitLayout component for side-by-side content layouts
 * Supports responsive behavior, configurable split ratios, and positioning
 */
const SplitLayout: React.FC<SplitLayoutProps> = ({
  children,
  className,
  sidebar,
  sidebarPosition = 'left',
  sidebarWidth = '300px',
  sidebarClassName,
  contentClassName,
  stackBelowBreakpoint = 'md',
  reversed = false,
  gap = 'md',
}) => {
  const breakpointClasses = {
    'sm': 'flex-col sm:flex-row',
    'md': 'flex-col md:flex-row',
    'lg': 'flex-col lg:flex-row',
    'xl': 'flex-col xl:flex-row',
  };

  const gapClasses = {
    'none': 'gap-0',
    'xs': 'gap-2',
    'sm': 'gap-4',
    'md': 'gap-6',
    'lg': 'gap-8',
    'xl': 'gap-10',
  };

  const isSidebarRight = sidebarPosition === 'right' ? !reversed : reversed;

  return (
    <div
      className={cn(
        'flex w-full',
        breakpointClasses[stackBelowBreakpoint],
        gapClasses[gap],
        isSidebarRight ? 'flex-row-reverse' : '',
        className
      )}
    >
      <div
        className={cn(
          'shrink-0',
          {
            'sm:w-auto': stackBelowBreakpoint === 'sm',
            'md:w-auto': stackBelowBreakpoint === 'md',
            'lg:w-auto': stackBelowBreakpoint === 'lg',
            'xl:w-auto': stackBelowBreakpoint === 'xl',
          },
          sidebarClassName
        )}
        style={{
          [stackBelowBreakpoint]: {
            width: sidebarWidth,
          }
        }}
      >
        {sidebar}
      </div>
      <div
        className={cn(
          'flex-grow min-w-0',
          contentClassName
        )}
      >
        {children}
      </div>
    </div>
  );
};

export default SplitLayout;
