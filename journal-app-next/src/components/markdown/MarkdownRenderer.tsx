import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import Image from 'next/image';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`prose max-w-none dark:prose-invert ${className}`}>
      <ReactMarkdown
        components={{
          img: ({ node, alt, src, ...props }) => {
            const [error, setError] = useState(false);
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

            // Use relative URL if it's an absolute API URL
            const imgSrc = src?.startsWith(baseUrl) ? src : src || '';

            // Return a responsive image with error handling
            return error ? (
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-800 text-center">
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                  Image could not be loaded
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 break-all">
                  {src}
                </p>
              </div>
            ) : (
              <span className="block relative my-4">
                <img
                  src={imgSrc}
                  alt={alt || 'Image'}
                  className="rounded-md max-w-full mx-auto"
                  style={{ maxHeight: '500px' }}
                  onError={() => setError(true)}
                />
              </span>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
