'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ContentPaddingProps {
  children: React.ReactNode;
  className?: string;
  size?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  as?: React.ElementType;
}

/**
 * ContentPadding utility component for consistent internal padding
 * Used within cards, sections, and other content containers
 */
const ContentPadding: React.FC<ContentPaddingProps> = ({
  children,
  className,
  size = 'md',
  as: Component = 'div',
}) => {
  const paddingClasses = {
    'none': '',
    'xs': 'p-2',
    'sm': 'p-4',
    'md': 'p-6',
    'lg': 'p-8',
    'xl': 'p-10',
  };

  return (
    <Component
      className={cn(
        paddingClasses[size],
        className
      )}
    >
      {children}
    </Component>
  );
};

export default ContentPadding;
