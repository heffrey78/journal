'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import {
  BoldIcon,
  ItalicIcon,
  LinkIcon,
  ListIcon,
  ImageIcon,
  CodeIcon,
  TableIcon,
  EyeIcon,
  EyeOffIcon,
  Columns2Icon,
  Heading1,
  Heading2,
  Heading3,
  StrikethroughIcon,
  QuoteIcon,
  ListOrderedIcon,
  CheckSquareIcon
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface MarkdownToolbarProps {
  onAction: (before: string, after?: string, placeholder?: string) => void;
  onToggleImageBrowser: () => void;
  onToggleSyncScrolling: () => void;
  onTogglePreviewMode: () => void;
  currentPreviewMode: 'split' | 'editor' | 'preview';
  syncScrolling: boolean;
}

export default function MarkdownToolbar({
  onAction,
  onToggleImageBrowser,
  onToggleSyncScrolling,
  onTogglePreviewMode,
  currentPreviewMode,
  syncScrolling
}: MarkdownToolbarProps) {

  // Format toolbar groups
  const toolbarGroups = [
    // Text formatting
    [
      { icon: <BoldIcon className="h-4 w-4" />, action: () => onAction('**', '**', 'bold text'), label: 'Bold (Ctrl+B)' },
      { icon: <ItalicIcon className="h-4 w-4" />, action: () => onAction('*', '*', 'italic text'), label: 'Italic (Ctrl+I)' },
      { icon: <StrikethroughIcon className="h-4 w-4" />, action: () => onAction('~~', '~~', 'strikethrough'), label: 'Strikethrough' },
      { icon: <CodeIcon className="h-4 w-4" />, action: () => onAction('`', '`', 'code'), label: 'Inline Code' },
    ],
    // Headings
    [
      { icon: <Heading1 className="h-4 w-4" />, action: () => onAction('# ', '', 'Heading 1'), label: 'Heading 1' },
      { icon: <Heading2 className="h-4 w-4" />, action: () => onAction('## ', '', 'Heading 2'), label: 'Heading 2' },
      { icon: <Heading3 className="h-4 w-4" />, action: () => onAction('### ', '', 'Heading 3'), label: 'Heading 3' },
    ],
    // Lists and links
    [
      { icon: <ListIcon className="h-4 w-4" />, action: () => onAction('- ', '', 'List item'), label: 'Bullet List' },
      { icon: <ListOrderedIcon className="h-4 w-4" />, action: () => onAction('1. ', '', 'List item'), label: 'Numbered List' },
      { icon: <CheckSquareIcon className="h-4 w-4" />, action: () => onAction('- [ ] ', '', 'Task item'), label: 'Task List' },
      { icon: <LinkIcon className="h-4 w-4" />, action: () => onAction('[', '](url)', 'link text'), label: 'Link (Ctrl+K)' },
    ],
    // Advanced
    [
      { icon: <QuoteIcon className="h-4 w-4" />, action: () => onAction('> ', '', 'Quote'), label: 'Blockquote' },
      { icon: <span className="text-xs font-mono">```</span>, action: () => onAction('```\n', '\n```', 'code block'), label: 'Code Block' },
      { icon: <TableIcon className="h-4 w-4" />, action: () => insertTable(), label: 'Table' },
      { icon: <span className="text-xs">---</span>, action: () => onAction('\n---\n', '', ''), label: 'Horizontal Rule' },
    ],
    // Media and view
    [
      { icon: <ImageIcon className="h-4 w-4" />, action: onToggleImageBrowser, label: 'Insert Image' },
    ],
    // View Controls
    [
      { 
        icon: currentPreviewMode === 'split' ? <Columns2Icon className="h-4 w-4" /> : 
              currentPreviewMode === 'editor' ? <EyeIcon className="h-4 w-4" /> : 
                                             <EyeOffIcon className="h-4 w-4" />,
        action: onTogglePreviewMode, 
        label: currentPreviewMode === 'split' ? 'Split View' : 
              currentPreviewMode === 'editor' ? 'Show Preview' : 'Show Editor',
        isActive: currentPreviewMode !== 'editor'
      },
      { 
        icon: <div className={`h-1.5 w-1.5 rounded-full ${syncScrolling ? 'bg-green-500' : 'bg-gray-400'}`} />,
        action: onToggleSyncScrolling, 
        label: `${syncScrolling ? 'Disable' : 'Enable'} Scroll Sync`,
        isActive: syncScrolling
      }
    ]
  ];

  const insertTable = () => {
    const tableTemplate = `| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |`;
    onAction('\n' + tableTemplate + '\n', '', '');
  };

  return (
    <div className="border-b bg-background p-1.5 flex flex-wrap gap-1 items-center">
      {toolbarGroups.map((group, groupIndex) => (
        <React.Fragment key={groupIndex}>
          {groupIndex > 0 && (
            <div className="w-px bg-border h-4 mx-1"></div>
          )}
          {group.map((tool, toolIndex) => (
            <Button
              key={toolIndex}
              variant="ghost"
              size="sm"
              type="button" /* Add type="button" to prevent form submission */
              onClick={(e) => {
                e.preventDefault(); /* Prevent default to be extra safe */
                tool.action();
              }}
              title={tool.label}
              className={cn(
                'h-7 w-7 p-0',
                'tool' in tool && 'isActive' in tool && tool.isActive ? 'bg-accent text-accent-foreground' : ''
              )}
            >
              <span className="h-4 w-4 flex items-center justify-center">
                {tool.icon}
              </span>
            </Button>
          ))}
        </React.Fragment>
      ))}
    </div>
  );
}
