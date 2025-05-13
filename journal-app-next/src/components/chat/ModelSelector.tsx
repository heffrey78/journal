'use client';

import React, { useEffect, useState } from 'react';
import { Select, SelectOption } from "@/components/ui/select";
import { CONFIG_API } from '@/config/api';

interface ModelSelectorProps {
  currentModel: string | null;
  onModelChange: (model: string) => void;
  disabled?: boolean;
}

export default function ModelSelector({ currentModel, onModelChange, disabled = false }: ModelSelectorProps) {
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchModels() {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch(CONFIG_API.AVAILABLE_MODELS);

        if (!response.ok) {
          throw new Error(`Failed to fetch models: ${response.statusText}`);
        }

        const data = await response.json();

        // The API returns an object with a "models" array
        if (data && Array.isArray(data.models)) {
          setAvailableModels(data.models);
        } else {
          console.warn('Unexpected format for models data:', data);
          setAvailableModels([]);
        }
      } catch (error) {
        console.error('Error fetching available models:', error);
        setError('Failed to load available models');
        setAvailableModels([]);
      } finally {
        setIsLoading(false);
      }
    }

    fetchModels();
  }, []);

  const handleModelChange = (value: string) => {
    onModelChange(value);
  };

  return (
    <div className="flex items-center space-x-1">
      <span className="text-sm text-foreground whitespace-nowrap">
        Model:
      </span>
      <Select
        value={currentModel || undefined}
        onChange={handleModelChange}
        disabled={disabled || isLoading}
        placeholder={isLoading ? "Loading..." : "Select model"}
        className="max-w-[150px]"
      >
        {error ? (
          <SelectOption value="error" disabled>
            Failed to load models
          </SelectOption>
        ) : availableModels.length === 0 && !isLoading ? (
          <SelectOption value="none" disabled>
            No models available
          </SelectOption>
        ) : (
          availableModels.map((model) => (
            <SelectOption key={model} value={model}>
              {model}
            </SelectOption>
          ))
        )}
      </Select>
    </div>
  );
}
