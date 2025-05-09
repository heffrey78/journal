'use client';

import { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { useTheme } from '../layout/ThemeProvider';

interface ColorSetting {
  name: string;
  variable: string;
  value: string;
  label: string;
  group?: string;
}

interface ColorCustomizerProps {
  onApply: (colors: Record<string, string>) => void;
  className?: string;
}

export default function ColorCustomizer({ onApply, className = '' }: ColorCustomizerProps) {
  const { theme, setComplimentaryColors } = useTheme();

  // Basic color settings that can be customized
  const [colorSettings, setColorSettings] = useState<ColorSetting[]>([
    { name: 'primary', variable: '--primary', value: '#3b82f6', label: 'Primary Color', group: 'main' },
    { name: 'accent', variable: '--accent', value: '#e0f2fe', label: 'Accent Color', group: 'main' },
    { name: 'background', variable: '--background', value: '#ffffff', label: 'Background', group: 'main' },
    { name: 'foreground', variable: '--foreground', value: '#171717', label: 'Text Color', group: 'main' },
    { name: 'muted', variable: '--muted', value: '#f3f4f6', label: 'Muted Background', group: 'main' },
    { name: 'border', variable: '--border', value: '#e5e7eb', label: 'Border Color', group: 'main' },
    { name: 'header-background', variable: '--header-background', value: '', label: 'Header Background', group: 'layout' },
    { name: 'sidebar-background', variable: '--sidebar-background', value: '', label: 'Sidebar Background', group: 'layout' },
    { name: 'footer-background', variable: '--footer-background', value: '', label: 'Footer Background', group: 'layout' },
  ]);

  // Toggle for enabling complimentary colors
  const [useComplimentaryColors, setUseComplimentaryColors] = useState(false);

  // Group settings for display
  const mainColorSettings = colorSettings.filter(color => color.group === 'main');
  const layoutColorSettings = colorSettings.filter(color => color.group === 'layout');

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

        // Check if complimentary colors are being used
        if (parsedColors['header-background'] || parsedColors['sidebar-background'] || parsedColors['footer-background']) {
          setUseComplimentaryColors(true);
        }
      } catch (err) {
        console.error('Error loading saved custom colors:', err);
      }
    }

    // Check if theme preferences has complimentary colors
    if (theme.complimentaryColors?.header || theme.complimentaryColors?.sidebar || theme.complimentaryColors?.footer) {
      setUseComplimentaryColors(true);
    }
  }, [theme]);

  // Handle color input change
  const handleColorChange = (index: number, newValue: string) => {
    setColorSettings(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], value: newValue };
      return updated;
    });
  };

  // Toggle complimentary colors
  const handleToggleComplimentaryColors = () => {
    setUseComplimentaryColors(!useComplimentaryColors);
  };

  // Apply custom colors
  const applyCustomColors = () => {
    const root = document.documentElement;
    const colorValues: Record<string, string> = {};

    // Apply each color variable to the document root
    colorSettings.forEach(setting => {
      // Only apply layout colors if complimentary colors are enabled
      if (setting.group === 'layout' && !useComplimentaryColors) {
        root.style.removeProperty(setting.variable);
        return;
      }

      root.style.setProperty(setting.variable, setting.value);
      colorValues[setting.name] = setting.value;
    });

    // Save custom theme to localStorage
    localStorage.setItem('customThemeColors', JSON.stringify(colorValues));

    // Update theme preferences with complimentary colors
    if (useComplimentaryColors) {
      // Find complimentary color values
      const headerColor = colorSettings.find(s => s.name === 'header-background')?.value || '';
      const sidebarColor = colorSettings.find(s => s.name === 'sidebar-background')?.value || '';
      const footerColor = colorSettings.find(s => s.name === 'footer-background')?.value || '';

      // Use the theme context to update complimentary colors
      setComplimentaryColors({
        header: headerColor,
        sidebar: sidebarColor,
        footer: footerColor
      });

      localStorage.setItem('themeCompColors', JSON.stringify({
        header: headerColor,
        sidebar: sidebarColor,
        footer: footerColor
      }));
    } else {
      setComplimentaryColors({
        header: '',
        sidebar: '',
        footer: ''
      });
      localStorage.removeItem('themeCompColors');
    }

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
    localStorage.removeItem('themeCompColors');
    setUseComplimentaryColors(false);

    // Reload page to apply default theme
    window.location.reload();
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="space-y-4">
        <h3 className="font-medium text-foreground">Main Theme Colors</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {mainColorSettings.map((color, index) => (
            <div key={color.name} className="space-y-1">
              <div className="flex justify-between items-center">
                <label htmlFor={`color-${color.name}`} className="text-sm font-medium text-muted-foreground">
                  {color.label}
                </label>
                <div
                  className="h-6 w-6 rounded border border-border"
                  style={{ backgroundColor: color.value }}
                />
              </div>
              <input
                id={`color-${color.name}`}
                type="color"
                value={color.value}
                onChange={(e) => handleColorChange(
                  colorSettings.findIndex(s => s.name === color.name),
                  e.target.value
                )}
                className="w-full h-8 rounded cursor-pointer"
              />
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-border pt-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-foreground">Layout Complimentary Colors</h3>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="use-complimentary"
              checked={useComplimentaryColors}
              onChange={handleToggleComplimentaryColors}
              className="mr-2 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <label htmlFor="use-complimentary" className="text-sm text-muted-foreground">
              Enable complimentary colors
            </label>
          </div>
        </div>

        {useComplimentaryColors && (
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {layoutColorSettings.map((color) => (
              <div key={color.name} className="space-y-1">
                <div className="flex justify-between items-center">
                  <label htmlFor={`color-${color.name}`} className="text-sm font-medium text-muted-foreground">
                    {color.label}
                  </label>
                  <div
                    className="h-6 w-6 rounded border border-border"
                    style={{ backgroundColor: color.value || 'transparent' }}
                  />
                </div>
                <input
                  id={`color-${color.name}`}
                  type="color"
                  value={color.value || '#ffffff'}
                  onChange={(e) => handleColorChange(
                    colorSettings.findIndex(s => s.name === color.name),
                    e.target.value
                  )}
                  className="w-full h-8 rounded cursor-pointer"
                />
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="pt-2 flex justify-between">
        <Button variant="outline" onClick={resetColors}>
          Reset Colors
        </Button>
        <Button onClick={applyCustomColors}>
          Apply Custom Colors
        </Button>
      </div>

      <div className="bg-muted rounded-md p-4 mt-4 border border-border">
        <h4 className="font-medium text-foreground text-sm mb-2">Preview</h4>
        <div className="space-y-3">
          <div className="h-8 rounded bg-primary"></div>
          <div className="h-8 rounded bg-accent"></div>
          <div className="flex space-x-2">
            <div className="h-8 flex-1 rounded bg-background border border-border"></div>
            <div className="h-8 flex-1 rounded bg-muted"></div>
          </div>
          {useComplimentaryColors && (
            <div className="flex space-x-2">
              <div className="h-8 flex-1 rounded border border-border" style={{backgroundColor: colorSettings.find(s => s.name === 'header-background')?.value || 'var(--background)'}}>
                <span className="text-xs px-2">Header</span>
              </div>
              <div className="h-8 flex-1 rounded border border-border" style={{backgroundColor: colorSettings.find(s => s.name === 'sidebar-background')?.value || 'var(--background)'}}>
                <span className="text-xs px-2">Sidebar</span>
              </div>
              <div className="h-8 flex-1 rounded border border-border" style={{backgroundColor: colorSettings.find(s => s.name === 'footer-background')?.value || 'var(--background)'}}>
                <span className="text-xs px-2">Footer</span>
              </div>
            </div>
          )}
          <p className="text-foreground">
            Sample text in <span className="text-primary font-medium">primary color</span>.
          </p>
        </div>
      </div>
    </div>
  );
}
