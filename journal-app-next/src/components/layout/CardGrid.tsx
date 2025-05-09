'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface CardGridProps {
  children: React.ReactNode;
  className?: string;
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  minWidth?: string;
  columns?: {
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
    '2xl'?: number;
  };
}

/**
 * CardGrid component for displaying cards in a responsive grid layout
 * Supports customizable minimum card width or explicit column counts per breakpoint
 */
const CardGrid: React.FC<CardGridProps> = ({
  children,
  className,
  gap = 'md',
  minWidth = '320px',
  columns,
}) => {
  const gapClasses = {
    'none': 'gap-0',
    'xs': 'gap-2',
    'sm': 'gap-4',
    'md': 'gap-6',
    'lg': 'gap-8',
    'xl': 'gap-10',
  };

  // Use either responsive columns or auto-fit with minWidth
  let gridTemplateColumns = `repeat(auto-fill, minmax(${minWidth}, 1fr))`;

  // If explicit columns are defined, use responsive grid columns
  let responsiveColumnsClasses = '';

  if (columns) {
    responsiveColumnsClasses = cn(
      columns.sm && 'sm:grid-cols-' + columns.sm,
      columns.md && 'md:grid-cols-' + columns.md,
      columns.lg && 'lg:grid-cols-' + columns.lg,
      columns.xl && 'xl:grid-cols-' + columns.xl,
      columns['2xl'] && '2xl:grid-cols-' + columns['2xl'],
    );
  }

  return (
    <div
      className={cn(
        'grid w-full',
        gapClasses[gap],
        responsiveColumnsClasses,
        className
      )}
      style={
        !columns ? { gridTemplateColumns } : undefined
      }
    >
      {children}
    </div>
  );
};

export default CardGrid;
