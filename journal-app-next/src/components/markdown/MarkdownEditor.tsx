import React, { useEffect, useState, useRef } from 'react';
import ImageBrowser from '../images/ImageBrowser';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autofocus?: boolean;
  entryId?: string;
}

const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  placeholder = 'Write your thoughts here...',
  autofocus = false,
  entryId,
}) => {
  const [showImageBrowser, setShowImageBrowser] = useState(false);
  const editorRef = useRef<HTMLTextAreaElement>(null);

  // Apply focus when the component mounts if autofocus is true
  useEffect(() => {
    if (autofocus && editorRef.current) {
      editorRef.current.focus();
    }
  }, [autofocus]);

  const handleImageUploadClick = () => {
    setShowImageBrowser(prev => !prev);
  };

  const handleInsertImage = (imageUrl: string) => {
    // Create image markdown
    const imageMarkdown = `![Image](${imageUrl})`;

    // Get cursor position to insert at if possible
    if (editorRef.current) {
      const textarea = editorRef.current;
      const startPos = textarea.selectionStart;
      const endPos = textarea.selectionEnd;

      // Insert image at cursor position, or append
      const newValue =
        value.substring(0, startPos) +
        imageMarkdown +
        value.substring(endPos);

      onChange(newValue);

      // Focus back on textarea and set cursor position after the inserted image
      setTimeout(() => {
        if (editorRef.current) {
          editorRef.current.focus();
          const newCursorPos = startPos + imageMarkdown.length;
          editorRef.current.setSelectionRange(newCursorPos, newCursorPos);
        }
      }, 50);
    } else {
      // Fallback if ref isn't available - just append
      onChange(value + '\n' + imageMarkdown);
    }

    // Hide image browser
    setShowImageBrowser(false);
  };

  return (
    <div>
      <div className="markdown-editor-container border rounded-md overflow-hidden">
        {/* Simple toolbar */}
        <div className="toolbar bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-2 flex items-center gap-2">
          <button
            onClick={() => {
              if (editorRef.current) {
                const startPos = editorRef.current.selectionStart;
                const endPos = editorRef.current.selectionEnd;
                const selectedText = value.substring(startPos, endPos);
                const newText = `**${selectedText}**`;
                onChange(value.substring(0, startPos) + newText + value.substring(endPos));
                editorRef.current.focus();
              }
            }}
            className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
            title="Bold"
            type="button"
          >
            <b>B</b>
          </button>
          <button
            onClick={() => {
              if (editorRef.current) {
                const startPos = editorRef.current.selectionStart;
                const endPos = editorRef.current.selectionEnd;
                const selectedText = value.substring(startPos, endPos);
                const newText = `*${selectedText}*`;
                onChange(value.substring(0, startPos) + newText + value.substring(endPos));
                editorRef.current.focus();
              }
            }}
            className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
            title="Italic"
            type="button"
          >
            <i>I</i>
          </button>
          <button
            onClick={() => {
              if (editorRef.current) {
                const startPos = editorRef.current.selectionStart;
                const prefix = value.substring(0, startPos).endsWith('\n')
                  ? '# '
                  : '\n# ';
                onChange(value.substring(0, startPos) + prefix + value.substring(startPos));
                editorRef.current.focus();
              }
            }}
            className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
            title="Heading"
            type="button"
          >
            H
          </button>
          <span className="border-l border-gray-300 dark:border-gray-600 h-6 mx-1"></span>
          <button
            onClick={() => {
              if (editorRef.current) {
                const startPos = editorRef.current.selectionStart;
                const prefix = value.substring(0, startPos).endsWith('\n')
                  ? '- '
                  : '\n- ';
                onChange(value.substring(0, startPos) + prefix + value.substring(startPos));
                editorRef.current.focus();
              }
            }}
            className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
            title="List"
            type="button"
          >
            •
          </button>
          <span className="border-l border-gray-300 dark:border-gray-600 h-6 mx-1"></span>
          <button
            onClick={handleImageUploadClick}
            className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
            title="Image"
            type="button"
          >
            🖼
          </button>
        </div>

        {/* Editor textarea */}
        <textarea
          ref={editorRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full p-4 min-h-60 focus:outline-none bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
          placeholder={placeholder}
          autoFocus={autofocus}
        />
      </div>

      {/* Helper text */}
      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 px-2">
        Use Markdown for formatting: **bold**, *italic*, # headings, - lists
      </div>

      {/* Image browser */}
      {showImageBrowser && (
        <div className="mt-4 border rounded-lg p-4 bg-gray-50 dark:bg-gray-800">
          <ImageBrowser
            entryId={entryId}
            onInsertImage={handleInsertImage}
          />
        </div>
      )}
    </div>
  );
};

export default MarkdownEditor;
