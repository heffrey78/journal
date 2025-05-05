'use client';

import { useState, useEffect } from 'react';
import Button from '../ui/Button';

interface ColorSetting {
  name: string;
  variable: string;
  value: string;
  label: string;
}

interface ColorCustomizerProps {
  onApply: (colors: Record<string, string>) => void;
  className?: string;
}

export default function ColorCustomizer({ onApply, className = '' }: ColorCustomizerProps) {
  // Basic color settings that can be customized
  const [colorSettings, setColorSettings] = useState<ColorSetting[]>([
    { name: 'primary', variable: '--primary', value: '#3b82f6', label: 'Primary Color' },
    { name: 'accent', variable: '--accent', value: '#e0f2fe', label: 'Accent Color' },
    { name: 'background', variable: '--background', value: '#ffffff', label: 'Background' },
    { name: 'foreground', variable: '--foreground', value: '#171717', label: 'Text Color' },
    { name: 'muted', variable: '--muted', value: '#f3f4f6', label: 'Muted Background' },
    { name: 'border', variable: '--border', value: '#e5e7eb', label: 'Border Color' },
  ]);

  // Load current theme colors when component mounts
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Get computed styles to extract current CSS variables
    const root = document.documentElement;
    const computedStyles = getComputedStyle(root);

    setColorSettings(prevSettings => {
      return prevSettings.map(setting => {
        // Try to get the CSS variable value
        const currentColor = computedStyles.getPropertyValue(setting.variable).trim();
        return {
          ...setting,
          value: currentColor || setting.value
        };
      });
    });

    // Load saved custom theme if available
    const savedCustomColors = localStorage.getItem('customThemeColors');
    if (savedCustomColors) {
      try {
        const parsedColors = JSON.parse(savedCustomColors);
        setColorSettings(prevSettings => {
          return prevSettings.map(setting => {
            return {
              ...setting,
              value: parsedColors[setting.name] || setting.value
            };
          });
        });
      } catch (err) {
        console.error('Error loading saved custom colors:', err);
      }
    }
  }, []);

  // Handle color input change
  const handleColorChange = (index: number, newValue: string) => {
    setColorSettings(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], value: newValue };
      return updated;
    });
  };

  // Apply custom colors
  const applyCustomColors = () => {
    const root = document.documentElement;
    const colorValues: Record<string, string> = {};

    // Apply each color variable to the document root
    colorSettings.forEach(setting => {
      root.style.setProperty(setting.variable, setting.value);
      colorValues[setting.name] = setting.value;
    });

    // Save custom theme to localStorage
    localStorage.setItem('customThemeColors', JSON.stringify(colorValues));

    // Call the onApply callback with the color values
    onApply(colorValues);
  };

  // Reset to default colors
  const resetColors = () => {
    const root = document.documentElement;

    // Remove custom color properties
    colorSettings.forEach(setting => {
      root.style.removeProperty(setting.variable);
    });

    // Clear saved custom theme
    localStorage.removeItem('customThemeColors');

    // Reload page to apply default theme
    window.location.reload();
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <h3 className="font-medium text-gray-900 dark:text-gray-100">Custom Colors</h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {colorSettings.map((color, index) => (
          <div key={color.name} className="space-y-1">
            <div className="flex justify-between items-center">
              <label htmlFor={`color-${color.name}`} className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {color.label}
              </label>
              <div
                className="h-6 w-6 rounded border border-gray-300 dark:border-gray-600"
                style={{ backgroundColor: color.value }}
              />
            </div>
            <input
              id={`color-${color.name}`}
              type="color"
              value={color.value}
              onChange={(e) => handleColorChange(index, e.target.value)}
              className="w-full h-8 rounded cursor-pointer"
            />
          </div>
        ))}
      </div>

      <div className="pt-2 flex justify-between">
        <Button variant="outline" onClick={resetColors}>
          Reset Colors
        </Button>
        <Button onClick={applyCustomColors}>
          Apply Custom Colors
        </Button>
      </div>

      <div className="bg-muted dark:bg-muted rounded-md p-4 mt-4 border border-border">
        <h4 className="font-medium text-foreground text-sm mb-2">Preview</h4>
        <div className="space-y-2">
          <div className="h-8 rounded bg-primary"></div>
          <div className="h-8 rounded bg-accent"></div>
          <div className="flex space-x-2">
            <div className="h-8 flex-1 rounded bg-background border border-border"></div>
            <div className="h-8 flex-1 rounded bg-muted"></div>
          </div>
          <p className="text-foreground">
            Sample text in <span className="text-primary font-medium">primary color</span>.
          </p>
        </div>
      </div>
    </div>
  );
}
