import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import { cn } from '@/lib/utils';

// Component for rendering images with error handling and loading state
const MarkdownImage = ({ src, alt }: { src?: string, alt?: string }) => {
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Use relative URL if it's an absolute API URL
  const imgSrc = src?.startsWith(baseUrl) ? src : src || '';

  if (error) {
    return (
      <div className="flex items-center justify-center p-6 border border-dashed border-muted rounded-lg bg-muted/20">
        <div className="text-center">
          <div className="text-muted-foreground mb-2">🖼️</div>
          <p className="text-sm text-muted-foreground">Image could not be loaded</p>
          <p className="text-xs text-muted-foreground break-all mt-1">{src}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative my-4">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/20 rounded">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={imgSrc}
        alt={alt || 'Image'}
        className="rounded-lg max-w-full mx-auto"
        style={{ maxHeight: '500px' }}
        onLoad={() => setLoading(false)}
        onError={() => {
          setError(true);
          setLoading(false);
        }}
      />
    </div>
  );
};

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={cn('prose max-w-none dark:prose-invert markdown-enhanced', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex, rehypeHighlight]}
        components={{
          // Custom image renderer
          img: (props) => <MarkdownImage src={props.src as string} alt={props.alt} />,
          
          // Custom link renderer
          a: ({ href, children, ...props }) => (
            <a
              href={href}
              {...props}
              className="text-primary hover:text-primary/80 underline transition-colors"
              target={href?.startsWith('http') ? '_blank' : undefined}
              rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
            >
              {children}
            </a>
          ),
          
          // Custom table styling
          table: ({ children, ...props }) => (
            <div className="overflow-x-auto">
              <table {...props} className="min-w-full border-collapse border border-border">
                {children}
              </table>
            </div>
          ),
          
          th: ({ children, ...props }) => (
            <th {...props} className="border border-border bg-muted p-2 text-left font-semibold">
              {children}
            </th>
          ),
          
          td: ({ children, ...props }) => (
            <td {...props} className="border border-border p-2">
              {children}
            </td>
          ),
          
          // Custom code block styling
          pre: ({ children, ...props }) => (
            <pre {...props} className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
              {children}
            </pre>
          ),
          
          // Checkbox styling for task lists
          input: ({ type, checked, ...props }) => {
            if (type === 'checkbox') {
              return (
                <input
                  type="checkbox"
                  checked={checked}
                  readOnly
                  {...props}
                  className="mr-2 w-4 h-4 text-primary bg-background border-border rounded focus:ring-primary"
                />
              );
            }
            return <input type={type} {...props} />;
          },
          
          // Custom list rendering
          ul: ({ children, ...props }) => (
            <ul className="list-disc pl-6 my-4 space-y-2" {...props}>
              {children}
            </ul>
          ),
          
          ol: ({ children, ...props }) => (
            <ol className="list-decimal pl-6 my-4 space-y-2" {...props}>
              {children}
            </ol>
          ),
          
          li: ({ children, ...props }) => (
            <li className="pl-1" {...props}>
              {children}
            </li>
          ),

          // Heading styles
          h1: ({ children, ...props }) => (
            <h1 className="text-3xl font-bold mt-6 mb-4 pb-2 border-b border-border/60" {...props}>
              {children}
            </h1>
          ),
          
          h2: ({ children, ...props }) => (
            <h2 className="text-2xl font-semibold mt-5 mb-3" {...props}>
              {children}
            </h2>
          ),
          
          h3: ({ children, ...props }) => (
            <h3 className="text-xl font-medium mt-4 mb-2" {...props}>
              {children}
            </h3>
          ),
          
          h4: ({ children, ...props }) => (
            <h4 className="text-lg font-medium mt-4 mb-2" {...props}>
              {children}
            </h4>
          ),
          
          h5: ({ children, ...props }) => (
            <h5 className="text-base font-medium mt-3 mb-2" {...props}>
              {children}
            </h5>
          ),
          
          h6: ({ children, ...props }) => (
            <h6 className="text-sm font-medium mt-3 mb-2 text-muted-foreground" {...props}>
              {children}
            </h6>
          )
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
