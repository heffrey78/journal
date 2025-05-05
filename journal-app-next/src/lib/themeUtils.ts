import { ThemePreferences } from './types';

// Default theme preferences
export const defaultTheme: ThemePreferences = {
  colorTheme: 'system',
  fontFamily: 'Geist Sans',
  fontSize: 16,
  lineHeight: 1.6,
};

/**
 * Apply theme CSS variables based on theme preferences
 */
export function applyThemeVariables(theme: ThemePreferences) {
  if (typeof window === 'undefined') return;

  const root = document.documentElement;
  const body = document.body;

  // Apply font size and line height
  root.style.setProperty('--font-size-base', `${theme.fontSize}px`);
  root.style.setProperty('--line-height', theme.lineHeight.toString());

  // Apply font family
  switch (theme.fontFamily) {
    case 'Geist Sans':
      body.style.fontFamily = 'var(--font-geist-sans), -apple-system, BlinkMacSystemFont, sans-serif';
      break;
    case 'Geist Mono':
      body.style.fontFamily = 'var(--font-geist-mono), monospace';
      break;
    case 'serif':
      body.style.fontFamily = 'Georgia, Times, "Times New Roman", serif';
      break;
  }
}

/**
 * Apply custom color theme from localStorage if available
 */
export function applyCustomColors() {
  if (typeof window === 'undefined') return;

  const root = document.documentElement;
  const savedCustomColors = localStorage.getItem('customThemeColors');

  if (savedCustomColors) {
    try {
      const colors = JSON.parse(savedCustomColors);

      // Apply each saved color to the document root
      Object.entries(colors).forEach(([name, value]) => {
        root.style.setProperty(`--${name}`, value as string);
      });
    } catch (err) {
      console.error('Error applying custom colors:', err);
    }
  }
}

/**
 * Initialize theme settings from localStorage
 */
export function initializeTheme() {
  if (typeof window === 'undefined') return;

  // Apply custom colors first (base theme colors)
  applyCustomColors();

  // Then apply theme preferences (typography, etc.)
  try {
    const savedThemePrefs = localStorage.getItem('themePreferences');
    if (savedThemePrefs) {
      const themePrefs = JSON.parse(savedThemePrefs) as ThemePreferences;
      applyThemeVariables(themePrefs);
    }
  } catch (err) {
    console.error('Error initializing theme:', err);
  }
}
