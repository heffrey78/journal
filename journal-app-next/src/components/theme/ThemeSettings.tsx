'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '../layout/ThemeProvider';
import Button from '../ui/Button';
import ColorCustomizer from './ColorCustomizer';

type ThemeSettingsProps = {
  onSave?: () => void;
};

// Available preset color themes
const colorThemes = [
  { name: 'Light', value: 'light' },
  { name: 'Dark', value: 'dark' },
  { name: 'System', value: 'system' },
];

// Available font families
const fontFamilies = [
  { name: 'Geist Sans', value: 'Geist Sans' },
  { name: 'Geist Mono', value: 'Geist Mono' },
  { name: 'Serif', value: 'serif' },
];

export default function ThemeSettings({ onSave }: ThemeSettingsProps) {
  const { theme, setColorTheme, setFontFamily, setFontSize, setLineHeight } = useTheme();
  const [activeTab, setActiveTab] = useState<'general' | 'advanced'>('general');

  // Local state for form values
  const [localSettings, setLocalSettings] = useState({
    colorTheme: theme.colorTheme,
    fontFamily: theme.fontFamily,
    fontSize: theme.fontSize,
    lineHeight: theme.lineHeight,
  });

  // Update local state when theme changes
  useEffect(() => {
    setLocalSettings({
      colorTheme: theme.colorTheme,
      fontFamily: theme.fontFamily,
      fontSize: theme.fontSize,
      lineHeight: theme.lineHeight,
    });
  }, [theme]);

  // Handle theme changes
  const handleColorThemeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalSettings({
      ...localSettings,
      colorTheme: e.target.value as 'light' | 'dark' | 'system',
    });
  };

  // Handle font family changes
  const handleFontFamilyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLocalSettings({
      ...localSettings,
      fontFamily: e.target.value as 'Geist Sans' | 'Geist Mono' | 'serif',
    });
  };

  // Handle font size changes
  const handleFontSizeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalSettings({
      ...localSettings,
      fontSize: parseInt(e.target.value, 10),
    });
  };

  // Handle line height changes
  const handleLineHeightChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalSettings({
      ...localSettings,
      lineHeight: parseFloat(e.target.value),
    });
  };

  // Apply all theme settings
  const applySettings = () => {
    setColorTheme(localSettings.colorTheme);
    setFontFamily(localSettings.fontFamily);
    setFontSize(localSettings.fontSize);
    setLineHeight(localSettings.lineHeight);

    if (onSave) {
      onSave();
    }
  };

  // Handle custom color apply
  const handleCustomColorsApply = () => {
    if (onSave) {
      onSave();
    }
  };

  return (
    <div className="space-y-6">
      {/* Theme settings tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        <button
          className={`px-4 py-2 font-medium text-sm ${
            activeTab === 'general'
              ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
          onClick={() => setActiveTab('general')}
        >
          General
        </button>
        <button
          className={`px-4 py-2 font-medium text-sm ${
            activeTab === 'advanced'
              ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
          onClick={() => setActiveTab('advanced')}
        >
          Advanced
        </button>
      </div>

      {activeTab === 'general' && (
        <>
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900 dark:text-gray-100">Color Theme</h3>
            <div className="grid grid-cols-3 gap-3">
              {colorThemes.map((colorTheme) => (
                <div key={colorTheme.value} className="flex items-center">
                  <input
                    type="radio"
                    id={`theme-${colorTheme.value}`}
                    name="colorTheme"
                    value={colorTheme.value}
                    checked={localSettings.colorTheme === colorTheme.value}
                    onChange={handleColorThemeChange}
                    className="sr-only"
                  />
                  <label
                    htmlFor={`theme-${colorTheme.value}`}
                    className={`flex-1 cursor-pointer rounded-md border px-3 py-2 text-center text-sm transition-all ${
                      localSettings.colorTheme === colorTheme.value
                        ? 'border-blue-600 bg-blue-50 text-blue-600 dark:border-blue-400 dark:bg-blue-900/20 dark:text-blue-400'
                        : 'border-gray-200 bg-white text-gray-900 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700/70'
                    }`}
                  >
                    {colorTheme.name}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="font-medium text-gray-900 dark:text-gray-100">Typography</h3>

            <div className="space-y-3">
              <div>
                <label htmlFor="font-family" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Font Family
                </label>
                <select
                  id="font-family"
                  value={localSettings.fontFamily}
                  onChange={handleFontFamilyChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {fontFamilies.map((font) => (
                    <option key={font.value} value={font.value}>
                      {font.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="font-size" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Font Size: {localSettings.fontSize}px
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">12</span>
                  <input
                    type="range"
                    id="font-size"
                    min="12"
                    max="24"
                    step="1"
                    value={localSettings.fontSize}
                    onChange={handleFontSizeChange}
                    className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full appearance-none"
                  />
                  <span className="text-xs text-gray-500">24</span>
                </div>
              </div>

              <div>
                <label htmlFor="line-height" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Line Height: {localSettings.lineHeight.toFixed(1)}
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">1.0</span>
                  <input
                    type="range"
                    id="line-height"
                    min="1"
                    max="2.5"
                    step="0.1"
                    value={localSettings.lineHeight}
                    onChange={handleLineHeightChange}
                    className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full appearance-none"
                  />
                  <span className="text-xs text-gray-500">2.5</span>
                </div>
              </div>
            </div>
          </div>

          <div className="text-preview p-4 border border-gray-200 dark:border-gray-700 rounded-md">
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Preview</h4>
            <p
              style={{
                fontFamily:
                  localSettings.fontFamily === 'Geist Sans'
                    ? 'var(--font-geist-sans), sans-serif'
                    : localSettings.fontFamily === 'Geist Mono'
                    ? 'var(--font-geist-mono), monospace'
                    : 'Georgia, serif',
                fontSize: `${localSettings.fontSize}px`,
                lineHeight: localSettings.lineHeight,
              }}
              className="text-gray-700 dark:text-gray-300"
            >
              The quick brown fox jumps over the lazy dog. This is a preview of how your text will look with the selected settings.
            </p>
          </div>

          <div className="flex justify-end">
            <Button onClick={applySettings}>
              Apply Theme Settings
            </Button>
          </div>
        </>
      )}

      {activeTab === 'advanced' && (
        <ColorCustomizer onApply={handleCustomColorsApply} />
      )}
    </div>
  );
}
