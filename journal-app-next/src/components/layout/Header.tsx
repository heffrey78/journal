'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Header: React.FC = () => {
  const pathname = usePathname();

  const isActive = (path: string) => {
    return pathname === path ? 'border-b-2 border-blue-500' : '';
  };

  return (
    <header className="sticky top-0 z-10 bg-white dark:bg-gray-900 shadow-sm">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center">
          <Link href="/" className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            Journal App
          </Link>
        </div>

        <nav className="hidden md:flex space-x-6">
          <Link
            href="/"
            className={`text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-1 py-2 ${isActive('/')}`}
          >
            Home
          </Link>
          <Link
            href="/entries"
            className={`text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-1 py-2 ${isActive('/entries')}`}
          >
            Entries
          </Link>
          <Link
            href="/search"
            className={`text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-1 py-2 ${isActive('/search')}`}
          >
            Search
          </Link>
          <Link
            href="/settings"
            className={`text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-1 py-2 ${isActive('/settings')}`}
          >
            Settings
          </Link>
        </nav>

        {/* Mobile menu button */}
        <div className="md:hidden">
          <button className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
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
