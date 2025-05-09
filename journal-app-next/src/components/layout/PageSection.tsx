'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import Stack from './Stack';

interface PageSectionProps {
  children: React.ReactNode;
  className?: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  titleClassName?: string;
  descriptionClassName?: string;
  contentClassName?: string;
  divider?: boolean;
  spacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  as?: React.ElementType;
}

/**
 * PageSection component for consistent page sectioning
 * Provides standardized structure for section headings and content
 */
const PageSection: React.FC<PageSectionProps> = ({
  children,
  className,
  title,
  description,
  titleClassName,
  descriptionClassName,
  contentClassName,
  divider = false,
  spacing = 'lg',
  as: Component = 'section',
}) => {
  return (
    <Component
      className={cn(
        'w-full py-6 md:py-8',
        divider && 'border-b border-border',
        className
      )}
    >
      <Stack gap={spacing}>
        {(title || description) && (
          <div className="w-full">
            {title && (
              <h2 className={cn('text-2xl font-semibold tracking-tight', titleClassName)}>
                {title}
              </h2>
            )}
            {description && (
              <p className={cn('mt-2 text-muted-foreground', descriptionClassName)}>
                {description}
              </p>
            )}
          </div>
        )}
        <div className={cn('w-full', contentClassName)}>
          {children}
        </div>
      </Stack>
    </Component>
  );
};

export default PageSection;
