'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface CardListProps {
  children: React.ReactNode;
  className?: string;
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  dividers?: boolean;
  dividerColor?: string;
}

/**
 * CardList component for displaying cards in a vertical list layout
 * Supports optional dividers between items and consistent spacing
 */
const CardList: React.FC<CardListProps> = ({
  children,
  className,
  gap = 'md',
  dividers = false,
  dividerColor = 'border-border',
}) => {
  const gapClasses = {
    'none': 'space-y-0',
    'xs': 'space-y-2',
    'sm': 'space-y-4',
    'md': 'space-y-6',
    'lg': 'space-y-8',
    'xl': 'space-y-10',
  };

  // Convert React children to array to add dividers between them
  const childrenArray = React.Children.toArray(children);

  if (dividers && childrenArray.length > 0) {
    return (
      <div className={cn('w-full', className)}>
        {childrenArray.map((child, index) => (
          <React.Fragment key={index}>
            <div>{child}</div>
            {index < childrenArray.length - 1 && (
              <div className={cn('w-full border-b', dividerColor)} />
            )}
          </React.Fragment>
        ))}
      </div>
    );
  }

  return (
    <div className={cn('w-full', gapClasses[gap], className)}>
      {children}
    </div>
  );
};

export default CardList;
