'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import Header from './Header';
import Footer from './Footer';
import FolderSidebar from './FolderSidebar';
import Container from './Container';

interface MainLayoutProps {
  children: React.ReactNode;
  className?: string;
  hideSidebar?: boolean;
}

/**
 * MainLayout component for the application's main layout structure
 * Provides a consistent layout with header, footer, and optional sidebar
 */
const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  className,
  hideSidebar = false
}) => {
  return (
    <div className={cn(
      'flex flex-col min-h-screen bg-background text-foreground',
      className
    )}>
      <Header />
      <div className="flex flex-grow">
        {!hideSidebar && <FolderSidebar />}
        <main className={cn(
          "flex-grow",
          hideSidebar ? 'w-full' : ''
        )}>
          {children}
        </main>
      </div>
      <Footer />
    </div>
  );
};

export default MainLayout;
