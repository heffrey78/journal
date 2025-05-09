'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ClusterProps {
  children: React.ReactNode;
  className?: string;
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  as?: React.ElementType;
  align?: 'start' | 'center' | 'end' | 'stretch';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
  wrap?: boolean;
}

/**
 * Cluster component for horizontal arrangement with consistent spacing
 * Used for elements that should be arranged horizontally with consistent gap
 */
const Cluster: React.FC<ClusterProps> = ({
  children,
  className,
  gap = 'md',
  as: Component = 'div',
  align = 'center',
  justify = 'start',
  wrap = true,
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

  const justifyClasses = {
    'start': 'justify-start',
    'center': 'justify-center',
    'end': 'justify-end',
    'between': 'justify-between',
    'around': 'justify-around',
    'evenly': 'justify-evenly',
  };

  return (
    <Component
      className={cn(
        'flex',
        wrap ? 'flex-wrap' : 'flex-nowrap',
        gapClasses[gap],
        alignClasses[align],
        justifyClasses[justify],
        className
      )}
    >
      {children}
    </Component>
  );
};

export default Cluster;
