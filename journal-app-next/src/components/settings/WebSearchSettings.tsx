'use client';

import React, { useState, useEffect } from 'react';
import { Globe, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { CONFIG_API } from '../../config/api';

interface WebSearchConfig {
  id: string;
  enabled: boolean;
  max_searches_per_minute: number;
  max_results_per_search: number;
  default_region: string;
  cache_duration_hours: number;
  enable_news_search: boolean;
  max_snippet_length: number;
}

const WebSearchSettings: React.FC = () => {
  const [config, setConfig] = useState<WebSearchConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const defaultConfig: WebSearchConfig = {
    id: 'default',
    enabled: true,
    max_searches_per_minute: 10,
    max_results_per_search: 5,
    default_region: 'wt-wt',
    cache_duration_hours: 1,
    enable_news_search: true,
    max_snippet_length: 200,
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(CONFIG_API.WEB_SEARCH);
      if (!response.ok) {
        throw new Error(`Failed to load config: ${response.statusText}`);
      }

      const configData = await response.json();
      setConfig(configData);
    } catch (err) {
      console.error('Error loading web search config:', err);
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
      // Set default config on error
      setConfig(defaultConfig);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async (newConfig: WebSearchConfig) => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      const response = await fetch(CONFIG_API.WEB_SEARCH, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newConfig),
      });

      if (!response.ok) {
        throw new Error(`Failed to save config: ${response.statusText}`);
      }

      const savedConfig = await response.json();
      setConfig(savedConfig);
      setSuccessMessage('Web search settings saved successfully');

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Error saving web search config:', err);
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleEnabled = async () => {
    if (!config) return;

    const newConfig = { ...config, enabled: !config.enabled };
    await saveConfig(newConfig);
  };

  const handleToggleNewsSearch = async () => {
    if (!config) return;

    const newConfig = { ...config, enable_news_search: !config.enable_news_search };
    await saveConfig(newConfig);
  };

  const handleRateLimitChange = async (newValue: number) => {
    if (!config) return;

    const newConfig = { ...config, max_searches_per_minute: newValue };
    await saveConfig(newConfig);
  };

  const handleMaxResultsChange = async (newValue: number) => {
    if (!config) return;

    const newConfig = { ...config, max_results_per_search: newValue };
    await saveConfig(newConfig);
  };

  const handleRegionChange = async (newRegion: string) => {
    if (!config) return;

    const newConfig = { ...config, default_region: newRegion };
    await saveConfig(newConfig);
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center space-x-3">
          <RefreshCw className="h-5 w-5 animate-spin" />
          <span>Loading web search settings...</span>
        </div>
      </Card>
    );
  }

  if (!config) {
    return (
      <Card className="p-6">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <div>
            <strong>Error</strong>
            <p>Failed to load web search configuration.</p>
          </div>
        </Alert>
      </Card>
    );
  }

  const regions = [
    { value: 'wt-wt', label: 'Worldwide' },
    { value: 'us-en', label: 'United States' },
    { value: 'uk-en', label: 'United Kingdom' },
    { value: 'ca-en', label: 'Canada' },
    { value: 'au-en', label: 'Australia' },
    { value: 'de-de', label: 'Germany' },
    { value: 'fr-fr', label: 'France' },
    { value: 'es-es', label: 'Spain' },
    { value: 'it-it', label: 'Italy' },
    { value: 'jp-jp', label: 'Japan' },
  ];

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Globe className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold">Web Search Settings</h3>
            <Badge variant={config.enabled ? 'default' : 'secondary'}>
              {config.enabled ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>

          <Button
            onClick={handleToggleEnabled}
            disabled={saving}
            variant={config.enabled ? 'outline' : 'default'}
          >
            {config.enabled ? 'Disable' : 'Enable'} Web Search
          </Button>
        </div>

        {error && (
          <Alert className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <div>
              <strong>Error</strong>
              <p>{error}</p>
            </div>
          </Alert>
        )}

        {successMessage && (
          <Alert className="mb-4 border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <div>
              <strong className="text-green-800">Success</strong>
              <p className="text-green-700">{successMessage}</p>
            </div>
          </Alert>
        )}

        <div className="space-y-6">
          {/* Rate Limiting */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Rate Limit (searches per minute)
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="number"
                min="1"
                max="60"
                value={config.max_searches_per_minute}
                onChange={(e) => handleRateLimitChange(parseInt(e.target.value) || 1)}
                className="w-20 px-3 py-1 border border-gray-300 rounded-md text-sm"
                disabled={saving}
              />
              <span className="text-sm text-gray-600">
                Maximum number of web searches allowed per minute
              </span>
            </div>
          </div>

          {/* Max Results */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Maximum Results per Search
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="number"
                min="1"
                max="10"
                value={config.max_results_per_search}
                onChange={(e) => handleMaxResultsChange(parseInt(e.target.value) || 1)}
                className="w-20 px-3 py-1 border border-gray-300 rounded-md text-sm"
                disabled={saving}
              />
              <span className="text-sm text-gray-600">
                Number of search results to return (1-10)
              </span>
            </div>
          </div>

          {/* Region */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Default Search Region
            </label>
            <select
              value={config.default_region}
              onChange={(e) => handleRegionChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm min-w-[200px]"
              disabled={saving}
            >
              {regions.map((region) => (
                <option key={region.value} value={region.value}>
                  {region.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Search results will be localized to this region when possible
            </p>
          </div>

          {/* News Search Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium">Enable News Search</h4>
              <p className="text-xs text-gray-500">
                Allow searching for recent news articles when relevant
              </p>
            </div>
            <Button
              onClick={handleToggleNewsSearch}
              disabled={saving}
              variant={config.enable_news_search ? 'default' : 'outline'}
              size="sm"
            >
              {config.enable_news_search ? 'Enabled' : 'Disabled'}
            </Button>
          </div>

          {/* Cache Duration */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Cache Duration (hours)
            </label>
            <div className="flex items-center space-x-3">
              <span className="text-sm text-gray-600">{config.cache_duration_hours}</span>
              <span className="text-sm text-gray-500">
                How long to cache search results to avoid duplicate requests
              </span>
            </div>
          </div>

          {/* Max Snippet Length */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Snippet Length (characters)
            </label>
            <div className="flex items-center space-x-3">
              <span className="text-sm text-gray-600">{config.max_snippet_length}</span>
              <span className="text-sm text-gray-500">
                Maximum length of result snippets displayed in chat
              </span>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Web search is powered by DuckDuckGo and respects user privacy.
            No search queries are tracked or stored by the search provider.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default WebSearchSettings;
