'use client';

import * as React from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Command, CommandGroup, CommandItem } from '@/components/ui/command';
import { Command as CommandPrimitive } from 'cmdk';

interface TagInputProps {
  placeholder?: string;
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  disabled?: boolean;
  id?: string;
  className?: string;
  suggestions?: string[];
}

export function TagInput({
  placeholder = 'Add tag...',
  tags,
  onTagsChange,
  disabled,
  id,
  className,
  suggestions = [],
}: TagInputProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [inputValue, setInputValue] = React.useState('');
  const [open, setOpen] = React.useState(false);

  const handleUnselect = (tag: string) => {
    onTagsChange(tags.filter((t) => t !== tag));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const input = e.currentTarget;

    if (e.key === 'Enter' && inputValue) {
      e.preventDefault();
      // Avoid adding duplicate tags
      if (!tags.includes(inputValue.trim()) && inputValue.trim() !== '') {
        onTagsChange([...tags, inputValue.trim()]);
        setInputValue('');
      }
    } else if (e.key === 'Backspace' && !inputValue && tags.length > 0) {
      // Remove the last tag when backspace is pressed on an empty input
      onTagsChange(tags.slice(0, -1));
    }
  };

  const handleBlur = () => {
    if (inputValue.trim() !== '' && !tags.includes(inputValue.trim())) {
      onTagsChange([...tags, inputValue.trim()]);
      setInputValue('');
    }
  };

  const filteredSuggestions = suggestions.filter(
    (suggestion) =>
      !tags.includes(suggestion) &&
      suggestion.toLowerCase().includes(inputValue.toLowerCase())
  );

  return (
    <div
      className={cn(
        'border border-input rounded-md px-3 py-2 flex flex-wrap gap-2 focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2',
        className
      )}
    >
      {tags.map((tag) => (
        <Badge key={tag} variant="secondary" className="flex items-center gap-1">
          {tag}
          <button
            type="button"
            className="rounded-full outline-none"
            onClick={() => handleUnselect(tag)}
            disabled={disabled}
          >
            <X className="h-3 w-3" />
            <span className="sr-only">Remove {tag}</span>
          </button>
        </Badge>
      ))}

      <CommandPrimitive onKeyDown={(e) => e.stopPropagation()}>
        <div className="flex-1 min-w-32">
          <input
            ref={inputRef}
            id={id}
            value={inputValue}
            disabled={disabled}
            onChange={(e) => {
              setInputValue(e.target.value);
              if (suggestions.length > 0) {
                setOpen(true);
              }
            }}
            onKeyDown={handleKeyDown}
            onBlur={() => {
              handleBlur();
              setOpen(false);
            }}
            className="outline-none bg-transparent placeholder:text-muted-foreground flex-1 min-w-32"
            placeholder={tags.length > 0 ? '' : placeholder}
          />
        </div>

        {open && filteredSuggestions.length > 0 && (
          <div className="relative mt-2">
            <Command className="absolute top-0 z-10 w-full rounded-md border border-border bg-popover shadow-md outline-none animate-in">
              <CommandGroup>
                {filteredSuggestions.map((suggestion) => (
                  <CommandItem
                    key={suggestion}
                    onSelect={() => {
                      onTagsChange([...tags, suggestion]);
                      setInputValue('');
                      setOpen(false);
                      inputRef.current?.focus();
                    }}
                  >
                    {suggestion}
                  </CommandItem>
                ))}
              </CommandGroup>
            </Command>
          </div>
        )}
      </CommandPrimitive>
    </div>
  );
}
