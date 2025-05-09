'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import MainLayout from './MainLayout';
import Container from './Container';
import Stack from './Stack';

interface PageLayoutProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  containerClassName?: string;
  contentClassName?: string;
  header?: React.ReactNode;
  spacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

/**
 * PageLayout component that extends MainLayout with consistent page structure
 * Provides standardized header and content areas with consistent spacing
 */
const PageLayout: React.FC<PageLayoutProps> = ({
  children,
  className,
  maxWidth = 'xl',
  containerClassName,
  contentClassName,
  header,
  spacing = 'lg',
}) => {
  return (
    <MainLayout className={className}>
      <Container
        maxWidth={maxWidth}
        className={cn('py-6 md:py-8', containerClassName)}
      >
        <Stack gap={spacing}>
          {header && (
            <div className="w-full">
              {header}
            </div>
          )}
          <div className={cn("w-full", contentClassName)}>
            {children}
          </div>
        </Stack>
      </Container>
    </MainLayout>
  );
};

export default PageLayout;
