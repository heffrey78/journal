'use client';

import React from 'react';
import Header from './Header';
import Footer from './Footer';
import FolderSidebar from './FolderSidebar';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      <Header />
      <div className="flex flex-grow">
        <FolderSidebar />
        <main className="flex-grow container mx-auto px-4 py-8">
          {children}
        </main>
      </div>
      <Footer />
    </div>
  );
};

export default MainLayout;
