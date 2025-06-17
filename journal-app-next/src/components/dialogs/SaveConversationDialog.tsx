'use client';

import React, { useState, useEffect } from 'react';
import { X, Download, MessageSquare, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { CHAT_API } from '@/config/api';

interface SaveConversationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  sessionTitle: string;
  messages?: Array<{
    id: string;
    content: string;
    role: string;
    timestamp: Date;
  }>;
}

interface SaveOptions {
  title: string;
  messageIds?: string[];
  additionalNotes?: string;
  tags: string[];
  folder?: string;
}

// Simple TagInput component
interface SimpleTagInputProps {
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  placeholder?: string;
}

function SimpleTagInput({ tags, onTagsChange, placeholder }: SimpleTagInputProps) {
  const [inputValue, setInputValue] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      const newTag = inputValue.trim();
      if (!tags.includes(newTag)) {
        onTagsChange([...tags, newTag]);
      }
      setInputValue('');
    } else if (e.key === 'Backspace' && !inputValue && tags.length > 0) {
      onTagsChange(tags.slice(0, -1));
    }
  };

  const removeTag = (tagToRemove: string) => {
    onTagsChange(tags.filter(tag => tag !== tagToRemove));
  };

  return (
    <div className="border border-gray-300 rounded-md p-2 min-h-[40px] flex flex-wrap gap-2 items-center focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
      {tags.map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-sm"
        >
          {tag}
          <button
            type="button"
            onClick={() => removeTag(tag)}
            className="ml-1 text-blue-600 hover:text-blue-800"
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={tags.length === 0 ? placeholder : ''}
        className="flex-1 min-w-[120px] outline-none bg-transparent text-sm"
      />
    </div>
  );
}

export default function SaveConversationDialog({
  isOpen,
  onClose,
  sessionId,
  sessionTitle,
  messages = []
}: SaveConversationDialogProps) {
  const [saveOptions, setSaveOptions] = useState<SaveOptions>({
    title: `Chat: ${sessionTitle}`,
    tags: [],
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMode, setSaveMode] = useState<'full' | 'selective'>('full');
  const [selectedMessageIds, setSelectedMessageIds] = useState<string[]>([]);
  const [folders, setFolders] = useState<string[]>([]);

  // Load available folders
  useEffect(() => {
    const loadFolders = async () => {
      try {
        // Call backend directly to get folders
        const response = await fetch('http://127.0.0.1:8000/folders/');
        if (response.ok) {
          const data = await response.json();
          setFolders(data || []);
        }
      } catch (error) {
        console.error('Error loading folders:', error);
      }
    };

    if (isOpen) {
      loadFolders();
    }
  }, [isOpen]);

  // Reset form when dialog opens
  useEffect(() => {
    if (isOpen) {
      setSaveOptions({
        title: `Chat: ${sessionTitle}`,
        tags: [],
      });
      setSaveMode('full');
      setSelectedMessageIds([]);
      setError(null);
    }
  }, [isOpen, sessionTitle]);

  const handleSave = async () => {
    if (!saveOptions.title.trim()) {
      setError('Please enter a title for the journal entry');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const requestBody: {
        title: string;
        tags: string[];
        additional_notes?: string;
        folder?: string;
        message_ids?: string[];
      } = {
        title: saveOptions.title.trim(),
        tags: saveOptions.tags,
        additional_notes: saveOptions.additionalNotes?.trim() || undefined,
        folder: saveOptions.folder || undefined,
      };

      // Add message IDs for selective save
      if (saveMode === 'selective' && selectedMessageIds.length > 0) {
        requestBody.message_ids = selectedMessageIds;
      }

      const response = await fetch(CHAT_API.SAVE_AS_ENTRY(sessionId), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save conversation');
      }

      const result = await response.json();

      // Success - close dialog and optionally show success message
      onClose();

      // You could add a toast notification here
      console.log('Conversation saved successfully:', result);

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save conversation');
    } finally {
      setSaving(false);
    }
  };

  const toggleMessageSelection = (messageId: string) => {
    setSelectedMessageIds(prev =>
      prev.includes(messageId)
        ? prev.filter(id => id !== messageId)
        : [...prev, messageId]
    );
  };

  const selectAllMessages = () => {
    setSelectedMessageIds(messages.map(m => m.id));
  };

  const clearSelection = () => {
    setSelectedMessageIds([]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-2">
            <Download className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold">Save Conversation as Journal Entry</h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[70vh]">
          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Save Mode Selection */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              What to save
            </label>
            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="saveMode"
                  value="full"
                  checked={saveMode === 'full'}
                  onChange={(e) => setSaveMode(e.target.value as 'full' | 'selective')}
                  className="text-blue-600"
                />
                <span>Entire conversation ({messages.length} messages)</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="saveMode"
                  value="selective"
                  checked={saveMode === 'selective'}
                  onChange={(e) => setSaveMode(e.target.value as 'full' | 'selective')}
                  className="text-blue-600"
                />
                <span>Selected messages only</span>
              </label>
            </div>
          </div>

          {/* Message Selection (only shown in selective mode) */}
          {saveMode === 'selective' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-700">
                  Select messages to save
                </label>
                <div className="space-x-2">
                  <button
                    type="button"
                    onClick={selectAllMessages}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    Select all
                  </button>
                  <button
                    type="button"
                    onClick={clearSelection}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Clear
                  </button>
                </div>
              </div>

              <div className="border rounded-lg max-h-48 overflow-y-auto">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`p-3 border-b last:border-b-0 cursor-pointer hover:bg-gray-50 ${
                      selectedMessageIds.includes(message.id) ? 'bg-blue-50 border-blue-200' : ''
                    }`}
                    onClick={() => toggleMessageSelection(message.id)}
                  >
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={selectedMessageIds.includes(message.id)}
                        onChange={() => toggleMessageSelection(message.id)}
                        className="mt-1 text-blue-600"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <MessageSquare className="h-4 w-4 text-gray-500" />
                          <span className="text-sm font-medium text-gray-900">
                            {message.role === 'user' ? 'You' : 'Assistant'}
                          </span>
                          <span className="text-xs text-gray-500">
                            {message.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 truncate">
                          {message.content.substring(0, 100)}
                          {message.content.length > 100 ? '...' : ''}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {selectedMessageIds.length > 0 && (
                <p className="text-sm text-gray-600">
                  {selectedMessageIds.length} message{selectedMessageIds.length === 1 ? '' : 's'} selected
                </p>
              )}
            </div>
          )}

          {/* Title Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Entry title *
            </label>
            <Input
              type="text"
              value={saveOptions.title}
              onChange={(e) => setSaveOptions(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Enter a title for the journal entry..."
              className="w-full"
            />
          </div>

          {/* Additional Notes */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Additional notes (optional)
            </label>
            <textarea
              value={saveOptions.additionalNotes || ''}
              onChange={(e) => setSaveOptions(prev => ({ ...prev, additionalNotes: e.target.value }))}
              placeholder="Add any additional context or notes about this conversation..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Tags (optional)
            </label>
            <SimpleTagInput
              tags={saveOptions.tags}
              onTagsChange={(tags) => setSaveOptions(prev => ({ ...prev, tags }))}
              placeholder="Add tags (press Enter to add)..."
            />
            <p className="text-xs text-gray-500">
              Tags help organize and find your entries later. &quot;chat-conversation&quot; and &quot;saved-chat&quot; will be added automatically.
            </p>
          </div>

          {/* Folder Selection */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Folder (optional)
            </label>
            <div className="flex items-center space-x-2">
              <FolderOpen className="h-4 w-4 text-gray-500" />
              <Select
                value={saveOptions.folder || ''}
                onChange={(value) => setSaveOptions(prev => ({ ...prev, folder: value || undefined }))}
                className="flex-1"
              >
                <option value="">No folder</option>
                {folders.map((folder) => (
                  <option key={folder} value={folder}>
                    {folder}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t bg-gray-50">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !saveOptions.title.trim() || (saveMode === 'selective' && selectedMessageIds.length === 0)}
            className="min-w-[100px]"
          >
            {saving ? 'Saving...' : 'Save Entry'}
          </Button>
        </div>
      </div>
    </div>
  );
}
