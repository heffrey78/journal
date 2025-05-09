'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ThemeToggle from '../theme/ThemeToggle';
import { ChartBarIcon } from '@heroicons/react/24/outline';

const Header: React.FC = () => {
  const pathname = usePathname();

  const isActive = (path: string) => {
    return pathname === path || pathname?.startsWith(path + '/') ? 'border-b-2 border-primary' : '';
  };

  return (
    <header className="sticky top-0 z-10 bg-background border-b border-border shadow-sm">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center">
          <Link href="/" className="text-2xl font-bold text-primary">
            Journal App
          </Link>
        </div>

        <nav className="hidden md:flex items-center space-x-6">
          <Link
            href="/"
            className={`text-foreground hover:text-primary px-1 py-2 ${isActive('/')}`}
          >
            Home
          </Link>
          <Link
            href="/entries"
            className={`text-foreground hover:text-primary px-1 py-2 ${isActive('/entries')}`}
          >
            Entries
          </Link>
          <Link
            href="/analyses"
            className={`text-foreground hover:text-primary px-1 py-2 flex items-center ${isActive('/analyses')}`}
          >
            <ChartBarIcon className="h-4 w-4 mr-1" />
            Analyses
          </Link>
          <Link
            href="/search"
            className={`text-foreground hover:text-primary px-1 py-2 ${isActive('/search')}`}
          >
            Search
          </Link>
          <Link
            href="/settings"
            className={`text-foreground hover:text-primary px-1 py-2 ${isActive('/settings')}`}
          >
            Settings
          </Link>

          {/* Theme Toggle */}
          <ThemeToggle className="ml-2" />
        </nav>

        {/* Mobile header with menu button and theme toggle */}
        <div className="md:hidden flex items-center space-x-2">
          <ThemeToggle />

          <button className="text-foreground hover:text-primary p-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
