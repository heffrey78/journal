'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import { DocumentTextIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import { EntryReference } from './types';

interface EntryReferencesProps {
  references: EntryReference[];
}

export default function EntryReferences({ references }: EntryReferencesProps) {
  const [expanded, setExpanded] = useState(false);

  // Sort references by relevance score if available
  const sortedReferences = [...references].sort((a, b) => {
    if (a.relevance_score && b.relevance_score) {
      return b.relevance_score - a.relevance_score;
    }
    return 0;
  });

  const displayedReferences = expanded ? sortedReferences : sortedReferences.slice(0, 2);

  return (
    <div className="mt-2 border-t pt-2">
      <div className="mb-2 text-sm text-gray-600 flex items-center">
        <DocumentTextIcon className="h-4 w-4 mr-1" />
        <span>Sources: {references.length}</span>
      </div>

      <div className="space-y-2">
        {displayedReferences.map((ref) => (
          <Link
            key={ref.entry_id}
            href={`/entries/${ref.entry_id}`}
            className="block p-2 rounded-md bg-gray-50 hover:bg-gray-100 transition-colors border border-gray-200"
          >
            <div className="flex justify-between">
              <h4 className="font-medium">{ref.title || 'Journal Entry'}</h4>
              <span className="text-sm text-gray-500">
                {ref.date ? format(new Date(ref.date), 'MMM dd, yyyy') : 'No date'}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1 line-clamp-2">{ref.preview}</p>
          </Link>
        ))}
      </div>

      {references.length > 2 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 text-sm text-blue-600 hover:text-blue-800 flex items-center"
        >
          {expanded ? (
            <>
              <ChevronUpIcon className="h-4 w-4 mr-1" />
              Show fewer sources
            </>
          ) : (
            <>
              <ChevronDownIcon className="h-4 w-4 mr-1" />
              Show {references.length - 2} more {references.length - 2 === 1 ? 'source' : 'sources'}
            </>
          )}
        </button>
      )}
    </div>
  );
}
