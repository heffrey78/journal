import React, { useState, useEffect } from 'react';
import { LLMConfig } from '@/lib/types';
import { llmApi } from '@/lib/api';
import Button from '@/components/ui/Button';

// Default LLM configuration
const defaultLLMConfig: LLMConfig = {
  model_name: 'llama3',
  embedding_model: 'nomic-embed-text',
  temperature: 0.7,
  max_tokens: 1000,
  max_retries: 2,
  retry_delay: 1.0,
  system_prompt: 'You are a helpful journaling assistant.'
};

interface LLMSettingsProps {
  onSaveComplete?: (success: boolean, message: string) => void;
}

const LLMSettings: React.FC<LLMSettingsProps> = ({ onSaveComplete }) => {
  const [config, setConfig] = useState<LLMConfig>(defaultLLMConfig);
  const [originalConfig, setOriginalConfig] = useState<LLMConfig>(defaultLLMConfig);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<{
    status: 'success' | 'error' | 'none';
    message: string;
  }>({ status: 'none', message: '' });

  // Load configuration and available models
  useEffect(() => {
    const loadConfig = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Load LLM configuration
        const configData = await llmApi.getLLMConfig();
        setConfig(configData);
        setOriginalConfig(configData);

        // Load available models
        const models = await llmApi.getAvailableModels();
        setAvailableModels(models);
      } catch (err) {
        console.error('Failed to load LLM configuration:', err);
        setError('Failed to load LLM configuration. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    loadConfig();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);

    try {
      const updatedConfig = await llmApi.updateLLMConfig(config);
      setConfig(updatedConfig);
      setOriginalConfig(updatedConfig);

      if (onSaveComplete) {
        onSaveComplete(true, 'LLM configuration saved successfully.');
      }
    } catch (err) {
      console.error('Failed to save LLM configuration:', err);

      if (onSaveComplete) {
        onSaveComplete(false, 'Failed to save LLM configuration. Please try again.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setIsTestingConnection(true);
    setConnectionStatus({ status: 'none', message: '' });

    try {
      const result = await llmApi.testConnection();
      setConnectionStatus({
        status: result.status === 'success' ? 'success' : 'error',
        message: result.message
      });
    } catch (err) {
      setConnectionStatus({
        status: 'error',
        message: 'Failed to connect to LLM service. Please check your settings and ensure Ollama is running.'
      });
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleResetDefaults = () => {
    if (confirm('Are you sure you want to reset to default LLM settings?')) {
      setConfig(defaultLLMConfig);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-300 p-4 rounded-md mb-4">
        <p>{error}</p>
        <Button
          className="mt-3"
          onClick={() => window.location.reload()}
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <label htmlFor="model-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Text Generation Model:
        </label>
        <select
          id="model-name"
          value={config.model_name}
          onChange={(e) => setConfig({...config, model_name: e.target.value})}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {availableModels.length > 0 ? (
            availableModels.map(model => (
              <option key={model} value={model}>{model}</option>
            ))
          ) : (
            <option value={config.model_name}>{config.model_name}</option>
          )}
        </select>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          The model used for text generation and summarization.
        </p>
      </div>

      <div>
        <label htmlFor="embedding-model" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Embedding Model:
        </label>
        <select
          id="embedding-model"
          value={config.embedding_model}
          onChange={(e) => setConfig({...config, embedding_model: e.target.value})}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {availableModels.length > 0 ? (
            availableModels.map(model => (
              <option key={model} value={model}>{model}</option>
            ))
          ) : (
            <option value={config.embedding_model}>{config.embedding_model}</option>
          )}
        </select>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          The model used for generating embeddings for semantic search.
        </p>
      </div>

      <div>
        <label htmlFor="temperature" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Temperature: {config.temperature}
        </label>
        <div className="flex items-center gap-2">
          <input
            type="range"
            id="temperature"
            min="0"
            max="1"
            step="0.1"
            value={config.temperature}
            onChange={(e) => setConfig({...config, temperature: parseFloat(e.target.value)})}
            className="w-full"
          />
          <span className="text-sm w-10 text-center">{config.temperature}</span>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Controls randomness in generation. Lower values are more deterministic, higher values more creative.
        </p>
      </div>

      <div>
        <label htmlFor="max-tokens" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Max Tokens:
        </label>
        <input
          type="number"
          id="max-tokens"
          value={config.max_tokens}
          onChange={(e) => setConfig({...config, max_tokens: parseInt(e.target.value, 10)})}
          min="100"
          max="4000"
          step="100"
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Maximum number of tokens to generate in responses.
        </p>
      </div>

      <div>
        <label htmlFor="max-retries" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Max Retries:
        </label>
        <input
          type="number"
          id="max-retries"
          value={config.max_retries}
          onChange={(e) => setConfig({...config, max_retries: parseInt(e.target.value, 10)})}
          min="1"
          max="5"
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Maximum number of retries for API calls.
        </p>
      </div>

      <div>
        <label htmlFor="retry-delay" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Retry Delay (seconds):
        </label>
        <input
          type="number"
          id="retry-delay"
          value={config.retry_delay}
          onChange={(e) => setConfig({...config, retry_delay: parseFloat(e.target.value)})}
          min="0.5"
          max="5"
          step="0.5"
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Delay between retries in seconds.
        </p>
      </div>

      <div>
        <label htmlFor="system-prompt" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          System Prompt:
        </label>
        <textarea
          id="system-prompt"
          value={config.system_prompt}
          onChange={(e) => setConfig({...config, system_prompt: e.target.value})}
          rows={4}
          placeholder="You are a helpful journaling assistant."
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        ></textarea>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Custom system prompt for the LLM. Leave empty to use the default.
        </p>
      </div>

      {connectionStatus.status !== 'none' && (
        <div className={`p-4 rounded-md ${
          connectionStatus.status === 'success'
            ? 'bg-green-100 dark:bg-green-900/20 border border-green-200 dark:border-green-900/30 text-green-700 dark:text-green-300'
            : 'bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-300'
        }`}>
          <p>{connectionStatus.message}</p>
        </div>
      )}

      <div className="flex flex-wrap gap-3 justify-end">
        <Button
          variant="outline"
          onClick={handleResetDefaults}
          disabled={isSaving || isTestingConnection}
        >
          Reset to Defaults
        </Button>

        <Button
          variant="secondary"
          onClick={handleTestConnection}
          isLoading={isTestingConnection}
          disabled={isSaving}
        >
          Test Connection
        </Button>

        <Button
          onClick={handleSave}
          isLoading={isSaving}
          disabled={isTestingConnection}
        >
          Save Changes
        </Button>
      </div>
    </div>
  );
};

export default LLMSettings;
