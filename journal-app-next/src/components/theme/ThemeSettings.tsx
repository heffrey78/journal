'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '../layout/ThemeProvider';
import { Button } from '../ui/button';
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
      <div className="flex border-b border-border">
        <button
          className={`px-4 py-2 font-medium text-sm ${
            activeTab === 'general'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('general')}
        >
          General
        </button>
        <button
          className={`px-4 py-2 font-medium text-sm ${
            activeTab === 'advanced'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('advanced')}
        >
          Advanced
        </button>
      </div>

      {activeTab === 'general' && (
        <>
          <div className="space-y-4">
            <h3 className="font-medium text-foreground">Color Theme</h3>
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
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-input bg-background text-foreground hover:bg-accent/50'
                    }`}
                  >
                    {colorTheme.name}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="font-medium text-foreground">Typography</h3>

            <div className="space-y-3">
              <div>
                <label htmlFor="font-family" className="block text-sm font-medium text-muted-foreground mb-1">
                  Font Family
                </label>
                <select
                  id="font-family"
                  value={localSettings.fontFamily}
                  onChange={handleFontFamilyChange}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {fontFamilies.map((font) => (
                    <option key={font.value} value={font.value}>
                      {font.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="font-size" className="block text-sm font-medium text-muted-foreground mb-1">
                  Font Size: {localSettings.fontSize}px
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">12</span>
                  <input
                    type="range"
                    id="font-size"
                    min="12"
                    max="24"
                    step="1"
                    value={localSettings.fontSize}
                    onChange={handleFontSizeChange}
                    className="flex-1 h-2 bg-muted rounded-full appearance-none"
                  />
                  <span className="text-xs text-muted-foreground">24</span>
                </div>
              </div>

              <div>
                <label htmlFor="line-height" className="block text-sm font-medium text-muted-foreground mb-1">
                  Line Height: {localSettings.lineHeight.toFixed(1)}
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">1.0</span>
                  <input
                    type="range"
                    id="line-height"
                    min="1"
                    max="2.5"
                    step="0.1"
                    value={localSettings.lineHeight}
                    onChange={handleLineHeightChange}
                    className="flex-1 h-2 bg-muted rounded-full appearance-none"
                  />
                  <span className="text-xs text-muted-foreground">2.5</span>
                </div>
              </div>
            </div>
          </div>

          <div className="text-preview p-4 border border-border rounded-md">
            <h4 className="font-medium text-foreground mb-2">Preview</h4>
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
              className="text-foreground"
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
