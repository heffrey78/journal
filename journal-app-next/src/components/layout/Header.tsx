'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ThemeToggle from '../theme/ThemeToggle';
import { ChartBarIcon } from '@heroicons/react/24/outline';
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
      <Container as="div" className="py-4">
        <Cluster justify="between" align="center" gap="sm">
          <div className="flex items-center">
            <Link href="/" className="text-2xl font-bold text-primary">
              Journal App
            </Link>
          </div>

          <nav className="hidden md:flex">
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

              {/* Theme Toggle */}
              <ThemeToggle className="ml-2" />
            </Cluster>
          </nav>

          {/* Mobile header with menu button and theme toggle */}
          <div className="md:hidden flex items-center space-x-2">
            <ThemeToggle />

            <button className="text-foreground hover:text-primary p-2" aria-label="Open menu">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
              </svg>
            </button>
          </div>
        </Cluster>
      </Container>
    </header>
  );
};

export default Header;
