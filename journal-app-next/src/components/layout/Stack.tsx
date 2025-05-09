'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface StackProps {
  children: React.ReactNode;
  className?: string;
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  as?: React.ElementType;
  align?: 'start' | 'center' | 'end' | 'stretch';
}

/**
 * Stack component for vertical arrangement with consistent spacing
 * Used for elements that should be stacked vertically with consistent gap
 */
const Stack: React.FC<StackProps> = ({
  children,
  className,
  gap = 'md',
  as: Component = 'div',
  align = 'stretch',
}) => {
  const gapClasses = {
    'none': 'gap-0',
    'xs': 'gap-2',
    'sm': 'gap-4',
    'md': 'gap-6',
    'lg': 'gap-8',
    'xl': 'gap-10',
  };

  const alignClasses = {
    'start': 'items-start',
    'center': 'items-center',
    'end': 'items-end',
    'stretch': 'items-stretch',
  };

  return (
    <Component
      className={cn(
        'flex flex-col',
        gapClasses[gap],
        alignClasses[align],
        className
      )}
    >
      {children}
    </Component>
  );
};

export default Stack;
