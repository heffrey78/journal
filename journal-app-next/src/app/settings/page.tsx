'use client';

import { useState, useEffect } from 'react';
import MainLayout from '@/components/layout/MainLayout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import LLMSettings from '@/components/settings/LLMSettings';
import ThemeSettings from '@/components/theme/ThemeSettings';
import WebSearchSettings from '@/components/settings/WebSearchSettings';
import PersonaManager from '@/components/settings/PersonaManager';
import { AppSettings } from '@/lib/types';
import Container from '@/components/layout/Container';
import ContentPadding from '@/components/layout/ContentPadding';

// Default settings
const defaultSettings: AppSettings = {
  theme: 'system',
  fontFamily: 'Geist Sans',
  fontSize: 16,
  lineHeight: 1.6,
  showWordCount: true,
  autoSaveInterval: 30,
};

type SettingTab = 'appearance' | 'editor' | 'llm' | 'personas' | 'tools';

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

  const handleSettingsSave = (success: boolean = true, message: string = 'Settings saved successfully.') => {
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
        <Container maxWidth="4xl" className="mx-auto">
          <ContentPadding size="md">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
            </div>
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          </ContentPadding>
        </Container>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <Container maxWidth="4xl" className="mx-auto">
        <ContentPadding size="md">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
          </div>

          {/* Settings tab navigation */}
          <div className="mb-8 border-b border-gray-200 dark:border-gray-700">
            <div className="flex flex-wrap -mb-px">
              <button
                className={`mr-4 inline-block py-3 px-4 border-b-2 font-medium text-sm ${
                  currentTab === 'appearance'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
                onClick={() => setCurrentTab('appearance')}
              >
                Appearance
              </button>
              <button
                className={`mr-4 inline-block py-3 px-4 border-b-2 font-medium text-sm ${
                  currentTab === 'editor'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
                onClick={() => setCurrentTab('editor')}
              >
                Editor
              </button>
              <button
                className={`mr-4 inline-block py-3 px-4 border-b-2 font-medium text-sm ${
                  currentTab === 'llm'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
                onClick={() => setCurrentTab('llm')}
              >
                LLM Configuration
              </button>
              <button
                className={`mr-4 inline-block py-3 px-4 border-b-2 font-medium text-sm ${
                  currentTab === 'personas'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
                onClick={() => setCurrentTab('personas')}
              >
                Personas
              </button>
              <button
                className={`mr-4 inline-block py-3 px-4 border-b-2 font-medium text-sm ${
                  currentTab === 'tools'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
                onClick={() => setCurrentTab('tools')}
              >
                Tools
              </button>
            </div>
          </div>

          {/* Appearance settings */}
          {currentTab === 'appearance' && (
            <Card className="mb-6">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-white">Appearance</h2>
                <ThemeSettings onSave={() => handleSettingsSave()} />
              </div>
            </Card>
          )}

          {/* Editor settings */}
          {currentTab === 'editor' && (
            <Card className="mb-6">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-white">Editor</h2>

                <div className="space-y-6">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="word-count"
                      checked={settings.showWordCount}
                      onChange={(e) => setSettings({...settings, showWordCount: e.target.checked})}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="word-count" className="ml-3 block text-sm text-gray-700 dark:text-gray-300">
                      Show word count
                    </label>
                  </div>

                  <div>
                    <label htmlFor="auto-save" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      {settings.autoSaveInterval === 0 ? 'Auto-save disabled' : `Auto-save every ${settings.autoSaveInterval} seconds`}
                    </p>
                  </div>
                </div>

                <div className="flex justify-between mt-8">
                  <Button variant="outline" onClick={handleReset}>
                    Reset to Default
                  </Button>
                  <div className="flex items-center gap-4">
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
              </div>
            </Card>
          )}

          {/* LLM settings */}
          {currentTab === 'llm' && (
            <Card className="mb-6">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-white">LLM Configuration</h2>
                <LLMSettings onSaveComplete={handleSettingsSave} />
              </div>
            </Card>
          )}

          {/* Personas settings */}
          {currentTab === 'personas' && (
            <Card className="mb-6">
              <div className="p-6">
                <PersonaManager onSaveComplete={handleSettingsSave} />
              </div>
            </Card>
          )}

          {/* Tools settings */}
          {currentTab === 'tools' && (
            <div className="space-y-6">
              <WebSearchSettings />
            </div>
          )}

          {/* Show global save notification when not on a specific tab */}
          {saveMessage && !['appearance', 'editor', 'llm', 'personas', 'tools'].includes(currentTab) && (
            <div className={`fixed bottom-4 right-4 px-4 py-2 rounded-md ${
              saveMessage.type === 'success'
                ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300'
                : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300'
            }`}>
              {saveMessage.text}
            </div>
          )}
        </ContentPadding>
      </Container>
    </MainLayout>
  );
}
