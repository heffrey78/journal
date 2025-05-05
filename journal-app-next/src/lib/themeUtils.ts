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

  // Check if we need to apply dark mode colors (either explicit dark mode or system preference)
  const isDarkMode = theme.colorTheme === 'dark' ||
    (theme.colorTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

  // Apply base color theme
  if (isDarkMode) {
    // Dark mode colors
    root.style.setProperty('--background', '#0a0a0a');
    root.style.setProperty('--foreground', '#ededed');
    root.style.setProperty('--card', '#1a1a1a');
    root.style.setProperty('--card-foreground', '#ededed');
    root.style.setProperty('--popover', '#1a1a1a');
    root.style.setProperty('--popover-foreground', '#ededed');
    root.style.setProperty('--primary', '#3b82f6');
    root.style.setProperty('--primary-foreground', '#ffffff');
    root.style.setProperty('--secondary', '#1f2937');
    root.style.setProperty('--secondary-foreground', '#f3f4f6');
    root.style.setProperty('--muted', '#374151');
    root.style.setProperty('--muted-foreground', '#9ca3af');
    root.style.setProperty('--accent', '#075985');
    root.style.setProperty('--accent-foreground', '#e0f2fe');
    root.style.setProperty('--border', '#374151');
    root.style.setProperty('--input', '#374151');
  } else {
    // Light mode colors
    root.style.setProperty('--background', '#ffffff');
    root.style.setProperty('--foreground', '#171717');
    root.style.setProperty('--card', '#ffffff');
    root.style.setProperty('--card-foreground', '#171717');
    root.style.setProperty('--popover', '#ffffff');
    root.style.setProperty('--popover-foreground', '#171717');
    root.style.setProperty('--primary', '#3b82f6');
    root.style.setProperty('--primary-foreground', '#ffffff');
    root.style.setProperty('--secondary', '#f3f4f6');
    root.style.setProperty('--secondary-foreground', '#1f2937');
    root.style.setProperty('--muted', '#f3f4f6');
    root.style.setProperty('--muted-foreground', '#6b7280');
    root.style.setProperty('--accent', '#e0f2fe');
    root.style.setProperty('--accent-foreground', '#0c4a6e');
    root.style.setProperty('--border', '#e5e7eb');
    root.style.setProperty('--input', '#e5e7eb');
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
