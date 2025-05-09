'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import Grid from './Grid';
import Stack from './Stack';
import Cluster from './Cluster';

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  sidebarPosition?: 'left' | 'right';
  sidebarWidth?: string | {
    sm?: string;
    md?: string;
    lg?: string;
    xl?: string;
  };
  className?: string;
  collapseBelow?: 'sm' | 'md' | 'lg' | 'xl' | 'never';
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  sidebarClassName?: string;
  contentClassName?: string;
  type?: 'sidebar-content' | 'equal-columns' | 'content-sidebar-sidebar';
}

/**
 * ResponsiveLayout component providing standardized responsive layout patterns
 * Handles common layouts like sidebar+content and multi-column layouts
 * with consistent responsive behavior
 */
const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  children,
  sidebar,
  sidebarPosition = 'left',
  sidebarWidth = '320px',
  className,
  collapseBelow = 'md',
  gap = 'md',
  sidebarClassName,
  contentClassName,
  type = 'sidebar-content'
}) => {
  // Handle different responsive patterns based on layout type
  if (!sidebar || type === 'equal-columns') {
    // For equal column layouts or when no sidebar is provided
    return (
      <div className={cn('w-full', className)}>
        {type === 'equal-columns' ? (
          <Grid
            columns={{
              initial: 1,
              md: 2
            }}
            gap={gap}
          >
            {children}
          </Grid>
        ) : (
          <div className={cn(contentClassName)}>
            {children}
          </div>
        )}
      </div>
    );
  }

  // CSS classes for different breakpoints
  const collapseClasses = {
    'never': 'flex',
    'sm': 'flex flex-col sm:flex-row',
    'md': 'flex flex-col md:flex-row',
    'lg': 'flex flex-col lg:flex-row',
    'xl': 'flex flex-col xl:flex-row'
  };

  // Gap classes
  const gapClasses = {
    'none': 'gap-0',
    'xs': 'gap-2',
    'sm': 'gap-4',
    'md': 'gap-6',
    'lg': 'gap-8',
    'xl': 'gap-10',
  };

  // Handle sidebar width at different breakpoints
  let sidebarResponsiveWidthStyle = {};
  if (typeof sidebarWidth === 'string') {
    sidebarResponsiveWidthStyle = collapseBelow === 'never' ?
      { width: sidebarWidth } :
      { [`${collapseBelow}:width`]: sidebarWidth };
  } else {
    // Apply responsive widths if provided as an object
    sidebarResponsiveWidthStyle = Object.entries(sidebarWidth).reduce((acc, [breakpoint, width]) => {
      return {
        ...acc,
        [`${breakpoint}:width`]: width
      };
    }, {});
  }

  // For multi-section layout with content and two sidebars
  if (type === 'content-sidebar-sidebar') {
    return (
      <div className={cn(
        'grid grid-cols-1 lg:grid-cols-12',
        gapClasses[gap],
        className
      )}>
        <div className={cn('lg:col-span-7', contentClassName)}>
          {children}
        </div>
        <div className={cn('lg:col-span-5 grid grid-cols-1 md:grid-cols-2', gapClasses[gap])}>
          {React.Children.map(sidebar, (child, index) => (
            <div key={index} className={sidebarClassName}>
              {child}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Standard sidebar-content layout
  return (
    <div className={cn(
      collapseClasses[collapseBelow],
      gapClasses[gap],
      sidebarPosition === 'right' ? 'flex-row-reverse' : '',
      className
    )}>
      <div
        className={cn('w-full',
          collapseBelow !== 'never' && {
            'sm:w-auto': collapseBelow === 'sm',
            'md:w-auto': collapseBelow === 'md',
            'lg:w-auto': collapseBelow === 'lg',
            'xl:w-auto': collapseBelow === 'xl',
          },
          sidebarClassName
        )}
        style={sidebarResponsiveWidthStyle}
      >
        {sidebar}
      </div>
      <div className={cn('flex-grow', contentClassName)}>
        {children}
      </div>
    </div>
  );
};

export default ResponsiveLayout;
