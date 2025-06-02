'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/design-system';
import { ImportModal } from '@/components/entries/ImportModal';
import { FileUp, Plus } from 'lucide-react';
// Note: Dropdown menu component not available - using simple buttons for now

/**
 * GlobalActions component provides quick access to common actions
 * Available globally in the header across all pages
 */
export const GlobalActions: React.FC = () => {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  const handleImportComplete = () => {
    // Refresh could be handled by the current page
    // For now, we'll just close the modal
    setIsImportModalOpen(false);
  };

  return (
    <>
      {/* Desktop Actions */}
      <div className="hidden md:flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsImportModalOpen(true)}
          className="flex items-center gap-1"
        >
          <FileUp className="h-4 w-4" />
          Import
        </Button>
        <Link href="/entries/new">
          <Button size="sm" className="flex items-center gap-1">
            <Plus className="h-4 w-4" />
            New Entry
          </Button>
        </Link>
      </div>

      {/* Mobile Actions - Simplified for now */}
      <div className="md:hidden flex items-center gap-1">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsImportModalOpen(true)}
        >
          <FileUp className="h-4 w-4" />
          <span className="sr-only">Import</span>
        </Button>
        <Link href="/entries/new">
          <Button size="sm">
            <Plus className="h-4 w-4" />
            <span className="sr-only">New Entry</span>
          </Button>
        </Link>
      </div>

      {/* Import Modal */}
      <ImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImportComplete={handleImportComplete}
      />
    </>
  );
};

export default GlobalActions;
