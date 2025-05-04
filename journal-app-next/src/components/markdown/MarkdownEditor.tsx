import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import 'easymde/dist/easymde.min.css';

// Import SimpleMDE dynamically to avoid SSR issues
const SimpleMDE = dynamic(() => import('react-simplemde-editor'), { ssr: false });

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autofocus?: boolean;
}

const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  placeholder = 'Write your thoughts here...',
  autofocus = false,
}) => {
  const [mounted, setMounted] = useState(false);

  // This is required to ensure the editor is only rendered client-side
  useEffect(() => {
    setMounted(true);
  }, []);

  const options = {
    autofocus,
    spellChecker: true,
    placeholder,
    status: ['lines', 'words', 'cursor'],
    toolbar: [
      'bold', 'italic', 'heading', '|',
      'quote', 'unordered-list', 'ordered-list', '|',
      'link', 'image', '|',
      'preview', 'side-by-side', 'fullscreen', '|',
      'guide'
    ],
  };

  if (!mounted) {
    return <div className="border rounded-md h-64 p-4 bg-gray-50 dark:bg-gray-700"></div>;
  }

  return (
    <SimpleMDE
      value={value}
      onChange={onChange}
      options={options}
      className="prose max-w-none dark:prose-invert"
    />
  );
};

export default MarkdownEditor;
