'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl' | 'full';
  centered?: boolean;
  as?: React.ElementType;
}

/**
 * Container component for consistent width constraints across the application
 * Provides standardized horizontal padding and max-width options
 */
const Container: React.FC<ContainerProps> = ({
  children,
  className,
  maxWidth = 'xl',
  centered = true,
  as: Component = 'div',
}) => {
  const maxWidthClasses = {
    sm: 'max-w-screen-sm',
    md: 'max-w-screen-md',
    lg: 'max-w-screen-lg',
    xl: 'max-w-screen-xl',
    '2xl': 'max-w-screen-2xl',
    '3xl': 'max-w-[1600px]',
    '4xl': 'max-w-[1800px]',
    '5xl': 'max-w-[2000px]',
    '6xl': 'max-w-[2200px]',
    'full': 'max-w-full',
  };

  return (
    <Component
      className={cn(
        'w-full px-4 sm:px-6 md:px-8',
        maxWidthClasses[maxWidth],
        centered && 'mx-auto',
        className
      )}
    >
      {children}
    </Component>
  );
};

export default Container;
