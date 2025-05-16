'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import MarkdownRenderer from './MarkdownRenderer';
import MarkdownToolbar from './MarkdownToolbar';
import ImageBrowser from '../images/ImageBrowser';
import { cn } from '@/lib/utils';

interface AdvancedMarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autofocus?: boolean;
  entryId?: string;
  className?: string;
  showPreview?: boolean;
  height?: string;
}

// Helper function to get view mode text
const getViewModeText = (mode: 'split' | 'editor' | 'preview'): string => {
  switch (mode) {
    case 'split': return ' Split View';
    case 'editor': return ' Editor View';
    case 'preview': return ' Preview View';
    default: return ' Split View';
  }
};

export default function AdvancedMarkdownEditor({
  value,
  onChange,
  placeholder = 'Write your thoughts here...',
  autofocus = false,
  entryId,
  className,
  showPreview = true,
  height = '500px'
}: AdvancedMarkdownEditorProps) {
  const [showImageBrowser, setShowImageBrowser] = useState(false);
  const [syncScrolling, setSyncScrolling] = useState(true);
  const [currentPreviewMode, setCurrentPreviewMode] = useState<'split' | 'editor' | 'preview'>(
    showPreview ? 'split' : 'editor'
  );
  
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const previewRef = useRef<HTMLDivElement>(null);
  // Ref to track when we're programmatically scrolling to prevent feedback loops
  const isScrollingRef = useRef(false);
  
  // Debounced value for preview updates
  const debouncedValue = useDebounce(value, 100);

  useEffect(() => {
    if (autofocus && editorRef.current) {
      editorRef.current.focus();
    }
  }, [autofocus]);
  
  // Update preview mode when showPreview prop changes
  useEffect(() => {
    setCurrentPreviewMode(showPreview ? 'split' : 'editor');
  }, [showPreview]);

  // Improved synchronized scrolling with adjusted proportional scrolling
  const handleEditorScroll = useCallback(() => {
    if (!syncScrolling || !editorRef.current || !previewRef.current) return;
    
    const editor = editorRef.current;
    const preview = previewRef.current;
    
    // Skip if we're handling a programmatic scroll
    if (isScrollingRef.current) return;
    
    try {
      isScrollingRef.current = true;
      
      // Calculate the fraction of the document we've scrolled through
      const scrollFraction = editor.scrollTop / (editor.scrollHeight - editor.clientHeight);
      
      // Apply smoothing for bottom of the document
      // This helps with alignment toward the end of the document where the differences are most noticeable
      let adjustedFraction = scrollFraction;
      
      // More aggressive adjustment near the bottom
      if (scrollFraction > 0.85) {
        // Gradually increase the scroll position as we get closer to the bottom
        // This counteracts the typical issue where preview content is taller
        const bottomFactor = (scrollFraction - 0.85) / 0.15; // 0 at 85%, 1 at 100%
        adjustedFraction = scrollFraction + (bottomFactor * 0.1); // Add up to 10% more scroll
        adjustedFraction = Math.min(adjustedFraction, 1); // Cap at 1
      }
      
      // Apply the adjusted scroll position
      const previewScrollTop = adjustedFraction * (preview.scrollHeight - preview.clientHeight);
      
      setEditorScrollTop(editor.scrollTop);
      setPreviewScrollTop(previewScrollTop);
      preview.scrollTop = previewScrollTop;
    } finally {
      // Release the scroll lock after a short delay
      setTimeout(() => {
        isScrollingRef.current = false;
      }, 50);
    }
  }, [syncScrolling]);

  const handlePreviewScroll = useCallback(() => {
    if (!syncScrolling || !editorRef.current || !previewRef.current) return;
    
    const editor = editorRef.current;
    const preview = previewRef.current;
    
    // Skip if we're handling a programmatic scroll
    if (isScrollingRef.current) return;
    
    try {
      isScrollingRef.current = true;
      
      // Calculate the fraction of the document we've scrolled through
      const scrollFraction = preview.scrollTop / (preview.scrollHeight - preview.clientHeight);
      
      // Apply a reverse adjustment for the editor
      let adjustedFraction = scrollFraction;
      
      // Adjust for the bottom of the document
      if (scrollFraction > 0.85) {
        const bottomFactor = (scrollFraction - 0.85) / 0.15;
        adjustedFraction = scrollFraction - (bottomFactor * 0.1); // Subtract up to 10%
        adjustedFraction = Math.max(adjustedFraction, 0);
      }
      
      const editorScrollTop = adjustedFraction * (editor.scrollHeight - editor.clientHeight);
      
      setPreviewScrollTop(preview.scrollTop);
      setEditorScrollTop(editorScrollTop);
      editor.scrollTop = editorScrollTop;
    } finally {
      // Release the scroll lock after a short delay
      setTimeout(() => {
        isScrollingRef.current = false;
      }, 50);
    }
  }, [syncScrolling]);

  // Toolbar actions
  const insertMarkdown = useCallback((before: string, after: string = '', placeholder: string = '') => {
    if (!editorRef.current) return;
    
    const textarea = editorRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end) || placeholder;
    
    const newText = `${before}${selectedText}${after}`;
    const newValue = value.substring(0, start) + newText + value.substring(end);
    
    onChange(newValue);
    
    // Restore cursor position
    setTimeout(() => {
      textarea.focus();
      const newCursorPos = start + before.length + selectedText.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  }, [value, onChange]);

  const handleInsertImage = useCallback((imageUrl: string) => {
    insertMarkdown('![Image](', ')', imageUrl);
    setShowImageBrowser(false);
  }, [insertMarkdown]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    // Handle common markdown shortcuts
    if (e.ctrlKey || e.metaKey) {
      // Prevent any potential form submission for ctrl/cmd key combinations
      e.preventDefault();
      
      switch (e.key) {
        case 'b':
          insertMarkdown('**', '**', 'bold text');
          break;
        case 'i':
          insertMarkdown('*', '*', 'italic text');
          break;
        case 'k':
          insertMarkdown('[', '](url)', 'link text');
          break;
        case 'Enter':
          // Explicitly prevent Ctrl+Enter form submission
          return;
      }
    }
    
    // Handle tab for indentation
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = editorRef.current!;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      
      if (e.shiftKey) {
        // Outdent
        const lines = value.substring(0, start).split('\n');
        const currentLine = lines[lines.length - 1];
        if (currentLine.startsWith('  ')) {
          const newValue = value.substring(0, start - 2) + value.substring(start);
          onChange(newValue);
          setTimeout(() => {
            textarea.setSelectionRange(start - 2, end - 2);
          }, 0);
        }
      } else {
        // Indent
        const newValue = value.substring(0, start) + '  ' + value.substring(end);
        onChange(newValue);
        setTimeout(() => {
          textarea.setSelectionRange(start + 2, end + 2);
        }, 0);
      }
    }
  }, [value, onChange, insertMarkdown]);

  const togglePreviewMode = useCallback(() => {
    setCurrentPreviewMode((current) => {
      if (current === 'split') return 'editor';
      if (current === 'editor') return 'preview';
      return 'split';
    });
  }, []);

  return (
    <div className={cn('border rounded-lg overflow-hidden bg-background', className)}>
      {/* Toolbar */}
      <MarkdownToolbar
        onAction={insertMarkdown}
        onToggleImageBrowser={() => setShowImageBrowser(!showImageBrowser)}
        onToggleSyncScrolling={() => setSyncScrolling(!syncScrolling)}
        onTogglePreviewMode={togglePreviewMode}
        currentPreviewMode={currentPreviewMode}
        syncScrolling={syncScrolling}
      />
      
      {/* Editor and Preview */}
      <div className="flex" style={{ height }}>
        {/* Editor */}
        {(currentPreviewMode === 'editor' || currentPreviewMode === 'split') && (
          <div className={cn(
            'flex-1',
            currentPreviewMode === 'split' ? 'w-1/2 border-r' : 'w-full'
          )}>
            <textarea
              ref={editorRef}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onScroll={handleEditorScroll}
              onKeyDown={handleKeyDown}
              className="w-full h-full p-4 resize-none focus:outline-none bg-background text-foreground font-mono text-sm leading-relaxed"
              placeholder={placeholder}
              spellCheck={true}
            />
          </div>
        )}
        
        {/* Preview */}
        {(currentPreviewMode === 'preview' || currentPreviewMode === 'split') && (
          <div 
            className={cn(
              'flex-1 overflow-y-auto bg-muted/20',
              currentPreviewMode === 'split' ? 'w-1/2' : 'w-full'
            )} 
            ref={previewRef} 
            onScroll={handlePreviewScroll}
          >
            <div className="p-4">
              <MarkdownRenderer content={debouncedValue} />
            </div>
          </div>
        )}
      </div>
      
      {/* Image Browser */}
      {showImageBrowser && (
        <div className="border-t bg-background p-4">
          <ImageBrowser
            entryId={entryId}
            onInsertImage={handleInsertImage}
          />
        </div>
      )}
      
      {/* Status Bar */}
      <div className="border-t bg-muted/30 px-4 py-2 text-xs text-muted-foreground flex justify-between">
        <div>
          Lines: {value.split('\n').length} | 
          Characters: {value.length} | 
          Words: {value.trim() ? value.trim().split(/\s+/).length : 0}
        </div>
        <div>
          {syncScrolling ? '🔗 Sync' : '🔗 No Sync'} | 
          {currentPreviewMode === 'split' ? ' Split View' : 
           currentPreviewMode === 'editor' ? ' Editor View' : ' Preview View'}
        </div>
      </div>
    </div>
  );
}
