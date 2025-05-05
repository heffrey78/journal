'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { ColorTheme, FontFamily, ThemePreferences } from '@/lib/types';
import { defaultTheme, applyThemeVariables, initializeTheme } from '@/lib/themeUtils';

type ThemeContextType = {
  theme: ThemePreferences;
  setColorTheme: (theme: ColorTheme) => void;
  setFontFamily: (fontFamily: FontFamily) => void;
  setFontSize: (size: number) => void;
  setLineHeight: (lineHeight: number) => void;
  toggleDarkMode: () => void;
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<ThemePreferences>(defaultTheme);
  const [mounted, setMounted] = useState(false);

  // Load theme settings from localStorage on component mount
  useEffect(() => {
    setMounted(true);

    try {
      // Check for legacy theme setting
      const savedColorTheme = localStorage.getItem('theme') as ColorTheme | null;

      // Check for full theme settings
      const savedThemePrefs = localStorage.getItem('themePreferences');

      if (savedThemePrefs) {
        const parsedTheme = JSON.parse(savedThemePrefs) as ThemePreferences;
        setTheme(parsedTheme);
      } else if (savedColorTheme) {
        // Migrate legacy setting
        setTheme(prev => ({...prev, colorTheme: savedColorTheme}));
      }

      // Initialize theme variables
      initializeTheme();
    } catch (error) {
      console.error('Error loading theme preferences:', error);
    }
  }, []);

  // Apply theme changes to document
  useEffect(() => {
    if (!mounted) return;

    const root = document.documentElement;

    // Apply color theme
    if (theme.colorTheme === 'dark' ||
        (theme.colorTheme === 'system' &&
         window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.remove('dark');
      root.classList.add('light');
    }

    // Apply typography and other theme variables
    applyThemeVariables(theme);

    // Save settings to localStorage
    localStorage.setItem('themePreferences', JSON.stringify(theme));

  }, [theme, mounted]);

  // Listen for system theme preference changes
  useEffect(() => {
    if (!mounted || theme.colorTheme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e: MediaQueryListEvent) => {
      const root = document.documentElement;
      if (e.matches) {
        root.classList.add('dark');
        root.classList.remove('light');
      } else {
        root.classList.remove('dark');
        root.classList.add('light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme.colorTheme, mounted]);

  // Theme setting functions
  const setColorTheme = (colorTheme: ColorTheme) => {
    setTheme(prev => ({...prev, colorTheme}));
  };

  const setFontFamily = (fontFamily: FontFamily) => {
    setTheme(prev => ({...prev, fontFamily}));
  };

  const setFontSize = (fontSize: number) => {
    setTheme(prev => ({...prev, fontSize}));
  };

  const setLineHeight = (lineHeight: number) => {
    setTheme(prev => ({...prev, lineHeight}));
  };

  const toggleDarkMode = () => {
    setTheme(prev => ({
      ...prev,
      colorTheme: prev.colorTheme === 'dark' ? 'light' : 'dark'
    }));
  };

  // Return early to avoid hydration mismatch
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setColorTheme,
        setFontFamily,
        setFontSize,
        setLineHeight,
        toggleDarkMode
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
