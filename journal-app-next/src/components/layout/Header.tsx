'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ThemeToggle from '../theme/ThemeToggle';
import GlobalActions from './GlobalActions';
import { ChartBarIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import Container from './Container';
import Cluster from './Cluster';

const Header: React.FC = () => {
  const pathname = usePathname();

  const isActive = (path: string) => {
    return pathname === path || pathname?.startsWith(path + '/') ? 'border-b-2 border-primary' : '';
  };

  return (
    <header className="sticky top-0 z-50 border-b border-border shadow-sm" style={{ backgroundColor: 'var(--header-background, var(--background))' }}>
      <div className="flex items-center justify-between w-full">
        {/* Left section - aligned with sidebar on desktop, flexible on mobile */}
        <div className="md:w-64 flex-shrink-0 px-4 sm:px-6 md:px-8 py-4 md:border-r border-border">
          <Link href="/" className="text-2xl font-bold text-primary">
            Reflection
          </Link>
        </div>

        {/* Right section - navigation and actions */}
        <div className="flex-1 px-4 sm:px-6 md:px-8 py-4">
          <Cluster justify="between" align="center" gap="sm">

            <nav className="hidden md:flex flex-1">
              <Cluster gap="md" align="center">
              <Link
                href="/"
                className={cn(
                  "text-foreground hover:text-primary px-1 py-2 transition-colors",
                  isActive('/')
                )}
              >
                Home
              </Link>
              <Link
                href="/entries"
                className={cn(
                  "text-foreground hover:text-primary px-1 py-2 transition-colors",
                  isActive('/entries')
                )}
              >
                Entries
              </Link>
              <Link
                href="/analyses"
                className={cn(
                  "text-foreground hover:text-primary px-1 py-2 flex items-center transition-colors",
                  isActive('/analyses')
                )}
              >
                <ChartBarIcon className="h-4 w-4 mr-1" />
                Analyses
              </Link>
              <Link
                href="/chat"
                className={cn(
                  "text-foreground hover:text-primary px-1 py-2 flex items-center transition-colors",
                  isActive('/chat')
                )}
              >
                <ChatBubbleLeftRightIcon className="h-4 w-4 mr-1" />
                Chat
              </Link>
              <Link
                href="/search"
                className={cn(
                  "text-foreground hover:text-primary px-1 py-2 transition-colors",
                  isActive('/search')
                )}
              >
                Search
              </Link>
              <Link
                href="/settings"
                className={cn(
                  "text-foreground hover:text-primary px-1 py-2 transition-colors",
                  isActive('/settings')
                )}
              >
                Settings
              </Link>

              {/* Global Actions */}
              <GlobalActions />

              {/* Theme Toggle */}
              <ThemeToggle className="ml-2" />
            </Cluster>
          </nav>

          {/* Mobile header with global actions and theme toggle */}
          <div className="md:hidden flex items-center space-x-2">
            <GlobalActions />
            <ThemeToggle />

            <button className="text-foreground hover:text-primary p-2" aria-label="Open menu">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
              </svg>
            </button>
            </div>
          </Cluster>
        </div>
      </div>
    </header>
  );
};

export default Header;
