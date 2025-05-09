'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface GridProps {
  children: React.ReactNode;
  className?: string;
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  columns?: number | {
    initial?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
    '2xl'?: number;
  };
  rows?: number;
  as?: React.ElementType;
  autoFlow?: 'row' | 'column' | 'dense' | 'row-dense' | 'column-dense';
}

/**
 * Grid component for creating CSS Grid layouts
 * Supports responsive column definitions and standardized gap spacing
 */
const Grid: React.FC<GridProps> = ({
  children,
  className,
  gap = 'md',
  columns = 1,
  rows,
  as: Component = 'div',
  autoFlow,
}) => {
  const gapClasses = {
    'none': 'gap-0',
    'xs': 'gap-2',
    'sm': 'gap-4',
    'md': 'gap-6',
    'lg': 'gap-8',
    'xl': 'gap-10',
  };

  const autoFlowClasses = {
    'row': 'grid-flow-row',
    'column': 'grid-flow-col',
    'dense': 'grid-flow-dense',
    'row-dense': 'grid-flow-row-dense',
    'column-dense': 'grid-flow-col-dense',
  };

  // Set column classes based on responsive object or simple number
  let columnClasses = '';

  if (typeof columns === 'number') {
    columnClasses = `grid-cols-${columns}`;
  } else {
    columnClasses = cn(
      columns.initial && `grid-cols-${columns.initial}`,
      columns.sm && `sm:grid-cols-${columns.sm}`,
      columns.md && `md:grid-cols-${columns.md}`,
      columns.lg && `lg:grid-cols-${columns.lg}`,
      columns.xl && `xl:grid-cols-${columns.xl}`,
      columns['2xl'] && `2xl:grid-cols-${columns['2xl']}`
    );
  }

  return (
    <Component className={cn(
      'grid w-full',
      gapClasses[gap],
      columnClasses,
      rows && `grid-rows-${rows}`,
      autoFlow && autoFlowClasses[autoFlow],
      className
    )}>
      {children}
    </Component>
  );
};

export default Grid;
