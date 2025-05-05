'use client';

import { useState, useEffect } from 'react';
import MainLayout from '@/components/layout/MainLayout';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import LLMSettings from '@/components/settings/LLMSettings';
import { AppSettings } from '@/lib/types';

// Default settings
const defaultSettings: AppSettings = {
  theme: 'system',
  fontFamily: 'Geist Sans',
  fontSize: 16,
  lineHeight: 1.6,
  showWordCount: true,
  autoSaveInterval: 30,
};

type SettingTab = 'appearance' | 'editor' | 'llm';

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [currentTab, setCurrentTab] = useState<SettingTab>('appearance');
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [mounted, setMounted] = useState(false);

  // Load settings on mount
  useEffect(() => {
    setMounted(true);
    const savedSettings = localStorage.getItem('journalSettings');
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (e) {
        console.error('Failed to parse saved settings:', e);
        // Continue with default settings if parsing fails
      }
    }
  }, []);

  // Save settings to localStorage
  const saveSettings = () => {
    if (!mounted) return;

    setIsSaving(true);
    setSaveMessage(null);

    try {
      localStorage.setItem('journalSettings', JSON.stringify(settings));

      // Apply theme
      if (settings.theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else if (settings.theme === 'light') {
        document.documentElement.classList.remove('dark');
      } else {
        // For system preference, check user preference
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }

      setSaveMessage({
        type: 'success',
        text: 'Settings saved successfully.',
      });
    } catch (e) {
      console.error('Failed to save settings:', e);
      setSaveMessage({
        type: 'error',
        text: 'Failed to save settings. Please try again.',
      });
    } finally {
      setIsSaving(false);

      // Clear message after 3 seconds
      setTimeout(() => {
        setSaveMessage(null);
      }, 3000);
    }
  };

  const handleReset = () => {
    if (!mounted) return;
    if (confirm('Are you sure you want to reset all settings to default?')) {
      setSettings(defaultSettings);
    }
  };

  const handleLLMSettingsSave = (success: boolean, message: string) => {
    setSaveMessage({
      type: success ? 'success' : 'error',
      text: message,
    });

    // Clear message after 3 seconds
    setTimeout(() => {
      setSaveMessage(null);
    }, 3000);
  };

  // Only render settings UI when client-side
  if (!mounted) {
    return (
      <MainLayout>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        </div>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
      </div>

      {/* Settings tab navigation */}
      <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap -mb-px">
          <button
            className={`mr-2 inline-block py-2 px-4 border-b-2 font-medium text-sm ${
              currentTab === 'appearance'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
            onClick={() => setCurrentTab('appearance')}
          >
            Appearance
          </button>
          <button
            className={`mr-2 inline-block py-2 px-4 border-b-2 font-medium text-sm ${
              currentTab === 'editor'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
            onClick={() => setCurrentTab('editor')}
          >
            Editor
          </button>
          <button
            className={`mr-2 inline-block py-2 px-4 border-b-2 font-medium text-sm ${
              currentTab === 'llm'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
            onClick={() => setCurrentTab('llm')}
          >
            LLM Configuration
          </button>
        </div>
      </div>

      {/* Appearance settings */}
      {currentTab === 'appearance' && (
        <Card className="mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Appearance</h2>

          <div className="space-y-4">
            <div>
              <label htmlFor="theme" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Theme
              </label>
              <select
                id="theme"
                value={settings.theme}
                onChange={(e) => setSettings({...settings, theme: e.target.value as 'light' | 'dark' | 'system'})}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System</option>
              </select>
            </div>

            <div>
              <label htmlFor="font-family" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Font Family
              </label>
              <select
                id="font-family"
                value={settings.fontFamily}
                onChange={(e) => setSettings({...settings, fontFamily: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Geist Sans">Geist Sans</option>
                <option value="Geist Mono">Geist Mono</option>
                <option value="serif">Serif</option>
              </select>
            </div>

            <div>
              <label htmlFor="font-size" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Font Size: {settings.fontSize}px
              </label>
              <input
                type="range"
                id="font-size"
                min="12"
                max="24"
                step="1"
                value={settings.fontSize}
                onChange={(e) => setSettings({...settings, fontSize: parseInt(e.target.value, 10)})}
                className="w-full"
              />
            </div>

            <div>
              <label htmlFor="line-height" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Line Height: {settings.lineHeight}
              </label>
              <input
                type="range"
                id="line-height"
                min="1"
                max="2.5"
                step="0.1"
                value={settings.lineHeight}
                onChange={(e) => setSettings({...settings, lineHeight: parseFloat(e.target.value)})}
                className="w-full"
              />
            </div>
          </div>

          <div className="flex justify-between mt-6">
            <Button variant="outline" onClick={handleReset}>
              Reset to Default
            </Button>
            <div className="flex items-center gap-3">
              {saveMessage && (
                <p className={`text-sm ${saveMessage.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {saveMessage.text}
                </p>
              )}
              <Button
                onClick={saveSettings}
                isLoading={isSaving}
              >
                Save Settings
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Editor settings */}
      {currentTab === 'editor' && (
        <Card className="mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Editor</h2>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="word-count"
                checked={settings.showWordCount}
                onChange={(e) => setSettings({...settings, showWordCount: e.target.checked})}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="word-count" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                Show word count
              </label>
            </div>

            <div>
              <label htmlFor="auto-save" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Auto-save Interval: {settings.autoSaveInterval} seconds
              </label>
              <input
                type="range"
                id="auto-save"
                min="0"
                max="120"
                step="5"
                value={settings.autoSaveInterval}
                onChange={(e) => setSettings({...settings, autoSaveInterval: parseInt(e.target.value, 10)})}
                className="w-full"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {settings.autoSaveInterval === 0 ? 'Auto-save disabled' : `Auto-save every ${settings.autoSaveInterval} seconds`}
              </p>
            </div>
          </div>

          <div className="flex justify-between mt-6">
            <Button variant="outline" onClick={handleReset}>
              Reset to Default
            </Button>
            <div className="flex items-center gap-3">
              {saveMessage && (
                <p className={`text-sm ${saveMessage.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {saveMessage.text}
                </p>
              )}
              <Button
                onClick={saveSettings}
                isLoading={isSaving}
              >
                Save Settings
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* LLM settings */}
      {currentTab === 'llm' && (
        <Card className="mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">LLM Configuration</h2>
          <LLMSettings onSaveComplete={handleLLMSettingsSave} />
        </Card>
      )}

      {/* Show global save notification when not on a specific tab */}
      {saveMessage && !['appearance', 'editor', 'llm'].includes(currentTab) && (
        <div className={`fixed bottom-4 right-4 px-4 py-2 rounded-md ${
          saveMessage.type === 'success'
            ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300'
            : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300'
        }`}>
          {saveMessage.text}
        </div>
      )}
    </MainLayout>
  );
}
