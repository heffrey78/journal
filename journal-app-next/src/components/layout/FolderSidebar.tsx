'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { organizationApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import Stack from './Stack';
import ContentPadding from './ContentPadding';

const FolderSidebar: React.FC = () => {
  const [folders, setFolders] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const fetchFolders = async () => {
      try {
        setLoading(true);
        const data = await organizationApi.getFolders();

        // Filter out any empty folder names
        const validFolders = data.filter(folder => folder && folder.trim().length > 0);

        // Sort the folders alphabetically and add the root folder at the top
        const sortedFolders = [...validFolders].sort((a, b) => a.localeCompare(b));
        setFolders(['..', ...sortedFolders]); // Add root folder as ".." at the top

        setError(null);
      } catch (err) {
        console.error('Failed to fetch folders:', err);
        setError('Failed to load folders');
      } finally {
        setLoading(false);
      }
    };

    fetchFolders();
  }, []);

  return (
    <>
      {/* Mobile toggle */}
      <div className="md:hidden">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 text-muted-foreground hover:text-foreground"
          aria-expanded={isOpen}
          aria-label="Toggle sidebar"
        >
          <span className="sr-only">Toggle Sidebar</span>
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
          </svg>
        </button>
      </div>

      {/* Sidebar - always visible on desktop, toggle on mobile */}
      <div className={cn(
        'fixed inset-0 z-40 transform',
        isOpen ? 'translate-x-0' : '-translate-x-full',
        'md:relative md:translate-x-0 transition-transform duration-300 ease-in-out'
      )}>
        <div
          className="absolute inset-0 bg-black/50 md:hidden"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />

        <aside
          className="w-64 h-full text-card-foreground border-r border-border shadow-lg"
          style={{ backgroundColor: 'var(--sidebar-background, var(--background))' }}
        >
          <Stack gap="none">
            <ContentPadding size="md" className="border-b border-border">
              <h2 className="text-xl font-semibold">Notebooks</h2>
            </ContentPadding>

            <nav className="overflow-y-auto flex-grow">
              <ContentPadding size="sm">
                <Stack gap="xs">
                  <Link
                    href="/entries"
                    className="flex items-center py-2 px-3 rounded-md hover:bg-accent hover:text-accent-foreground"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                    </svg>
                    All Entries
                  </Link>

                  <Link
                    href="/entries/favorites"
                    className="flex items-center py-2 px-3 rounded-md hover:bg-accent hover:text-accent-foreground"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>
                    </svg>
                    Favorites
                  </Link>

                  <Link
                    href="/calendar"
                    className="flex items-center py-2 px-3 rounded-md hover:bg-accent hover:text-accent-foreground"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    Calendar
                  </Link>
                </Stack>

                <div className="mt-6 mb-2 px-3">
                  <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Folders</h3>
                </div>

                {loading ? (
                  <div className="flex justify-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-muted"></div>
                  </div>
                ) : error ? (
                  <div className="px-3 py-2 text-sm text-destructive">{error}</div>
                ) : (
                  <Stack gap="none" className="space-y-1">
                    {folders.length > 0 ? (
                      folders.map((folder) => (
                        <li key={folder} className="list-none">
                          <Link
                            href={folder === '..' ? '/entries' : `/folders/${encodeURIComponent(folder)}`}
                            className="flex items-center py-2 px-3 rounded-md hover:bg-accent hover:text-accent-foreground"
                          >
                            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                            </svg>
                            {folder}
                          </Link>
                        </li>
                      ))
                    ) : (
                      <li className="px-3 py-2 text-sm text-muted-foreground list-none">No folders found</li>
                    )}
                  </Stack>
                )}
              </ContentPadding>
            </nav>

            <ContentPadding size="md" className="border-t border-border">
              <button
                className="w-full flex items-center justify-center py-2 px-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                onClick={async () => {
                  // Get folder name from prompt
                  const folderName = prompt('Enter new folder name:');
                  if (folderName && folderName.trim()) {
                    try {
                      // Call API to create the folder
                      const result = await organizationApi.createFolder(folderName.trim());
                      console.log('Folder created:', result);

                      // Refresh the folder list
                      const updatedFolders = await organizationApi.getFolders();
                      setFolders(updatedFolders);

                      // Navigate to the new folder page
                      router.push(`/folders/${encodeURIComponent(folderName.trim())}`);
                    } catch (err) {
                      console.error('Failed to create folder:', err);
                      alert('Failed to create folder. Please try again.');
                    }
                  }
                }}
              >
                <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
                New Folder
              </button>
            </ContentPadding>
          </Stack>
        </aside>
      </div>
    </>
  );
};

export default FolderSidebar;
