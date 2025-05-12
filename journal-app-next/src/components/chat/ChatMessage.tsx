'use client';

import React from 'react';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Link from 'next/link';
import { Message, EntryReference } from './types';

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  // Process message content to handle citation references like [1], [2], etc.
  const processMessageContent = (content: string) => {
    if (!message.has_references || !message.references || message.references.length === 0) {
      return content;
    }

    // Replace citation markers [1], [2], etc. with marker and superscript
    return content.replace(/\[(\d+)\]/g, '[$1]^');
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`
        max-w-[80%] p-4 rounded-lg
        ${isUser ? 'bg-blue-500 text-white rounded-br-none' : 'bg-gray-100 text-gray-800 rounded-bl-none'}
      `}>
        {isUser ? (
          // User messages are shown as plain text
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          // Assistant messages are rendered as markdown
          <div className={`markdown-content ${isUser ? 'text-white' : 'text-gray-800'} prose prose-sm max-w-none`}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: ({ node, ...props }) => (
                  <a {...props} className="text-blue-600 underline" target="_blank" rel="noopener noreferrer" />
                ),
                pre: ({ node, ...props }) => (
                  <pre {...props} className="bg-gray-800 text-gray-100 p-2 rounded overflow-x-auto" />
                ),
                code: ({ node, inline, ...props }) => (
                  inline ?
                  <code {...props} className="bg-gray-200 px-1 py-0.5 rounded text-sm" /> :
                  <code {...props} className="block text-sm" />
                ),
              }}
            >
              {processMessageContent(message.content)}
            </ReactMarkdown>

            {/* Display references if available */}
            {message.references && message.references.length > 0 && (
              <div className="mt-4 pt-2 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-2">References:</h4>
                <ul className="space-y-2">
                  {message.references.map((ref, index) => (
                    <CitationItem key={ref.entry_id} reference={ref} index={index + 1} />
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        <div className={`text-xs mt-2 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {format(new Date(message.timestamp), 'h:mm a')}
        </div>
      </div>
    </div>
  );
}

interface CitationItemProps {
  reference: EntryReference;
  index: number;
}

function CitationItem({ reference, index }: CitationItemProps) {
  // Use entry_title or fall back to title, and extract date from entry_id format (YYYYMMDDHHMMSS)
  const title = reference.entry_title || reference.title || 'Journal entry';

  // Format date from entry_id (if available and in expected format) or use provided date
  let displayDate = reference.date || '';

  if (!displayDate && reference.entry_id && reference.entry_id.length >= 8) {
    try {
      // Try to extract date from entry_id format (YYYYMMDDHHMMSS)
      const year = reference.entry_id.substring(0, 4);
      const month = reference.entry_id.substring(4, 6);
      const day = reference.entry_id.substring(6, 8);

      // Create a date object and format it
      const entryDate = new Date(`${year}-${month}-${day}`);
      if (!isNaN(entryDate.getTime())) {
        displayDate = entryDate.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
      }
    } catch (e) {
      console.error('Error parsing date from entry_id:', e);
    }
  }

  // Use entry_snippet or fall back to preview
  const snippet = reference.entry_snippet || reference.preview || '';

  // Use similarity_score or fall back to relevance_score
  const relevanceScore = reference.similarity_score || reference.relevance_score || 0;

  return (
    <li className="text-sm">
      <div className="flex items-start">
        <span className="font-medium text-gray-600 mr-2">[{index}]</span>
        <div className="flex-1">
          <Link
            href={`/entries/${reference.entry_id}`}
            className="font-medium text-blue-600 hover:text-blue-800 transition-colors"
            target="_blank"
          >
            {title}
            {displayDate && <span className="ml-1 text-gray-500">({displayDate})</span>}
          </Link>

          {/* Preview/snippet of the referenced entry */}
          {snippet && <p className="text-gray-600 mt-1 line-clamp-2">{snippet}</p>}

          {/* Show tags if available */}
          {reference.tags && reference.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {reference.tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Show relevance score if available */}
          {relevanceScore > 0 && (
            <div className="mt-1 flex items-center">
              <span className="text-xs text-gray-500">Relevance:</span>
              <div className="ml-1 bg-gray-200 h-1.5 w-24 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500"
                  style={{ width: `${Math.min(100, Math.max(0, relevanceScore * 100))}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </li>
  );
}
