import { ThemePreferences } from './types';

// Default theme preferences
export const defaultTheme: ThemePreferences = {
  colorTheme: 'system',
  fontFamily: 'Geist Sans',
  fontSize: 16,
  lineHeight: 1.6,
  complimentaryColors: {
    header: '',
    sidebar: '',
    footer: ''
  }
};

/**
 * Generate complimentary color based on the main color
 * Used as fallback when user hasn't set custom complimentary colors
 */
function getComplimentaryColor(hexColor: string, darken: boolean = false): string {
  // Default fallback colors if can't extract from base
  if (!hexColor || hexColor === '') {
    return darken ? '#1a1a1a' : '#f3f4f6';
  }

  // Convert hex to RGB
  let r = 0, g = 0, b = 0;

  // Handle #RGB format
  if (hexColor.length === 4) {
    r = parseInt(hexColor.charAt(1) + hexColor.charAt(1), 16);
    g = parseInt(hexColor.charAt(2) + hexColor.charAt(2), 16);
    b = parseInt(hexColor.charAt(3) + hexColor.charAt(3), 16);
  }
  // Handle #RRGGBB format
  else if (hexColor.length === 7) {
    r = parseInt(hexColor.substring(1, 3), 16);
    g = parseInt(hexColor.substring(3, 5), 16);
    b = parseInt(hexColor.substring(5, 7), 16);
  }

  // Create slightly darker/lighter variant as complimentary
  if (darken) {
    r = Math.max(0, r - 20);
    g = Math.max(0, g - 20);
    b = Math.max(0, b - 20);
  } else {
    r = Math.min(255, r + 20);
    g = Math.min(255, g + 20);
    b = Math.min(255, b + 20);
  }

  // Convert back to hex
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

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

  // Get any existing custom colors from localStorage
  const savedCustomColors = localStorage.getItem('customThemeColors');
  let customColors: Record<string, string> = {};

  if (savedCustomColors) {
    try {
      customColors = JSON.parse(savedCustomColors);
    } catch (err) {
      console.error('Error parsing custom colors:', err);
    }
  }

  // Check if we need to apply dark mode colors (either explicit dark mode or system preference)
  const isDarkMode = theme.colorTheme === 'dark' ||
    (theme.colorTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

  // Set base theme colors first - these will be overridden by custom colors if needed
  if (isDarkMode) {
    // Dark mode default colors
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
    // Light mode default colors
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

  // Apply main background to body
  document.body.style.backgroundColor = 'var(--background)';

  // Re-apply custom colors if they exist in the current theme
  if (savedCustomColors) {
    try {
      // Only apply custom colors that don't depend on theme mode
      // This allows proper toggling between light and dark modes
      const preservedColors = ['primary', 'accent'];
      preservedColors.forEach(colorName => {
        if (customColors[colorName]) {
          root.style.setProperty(`--${colorName}`, customColors[colorName]);
        }
      });

      // Handle background color specially - if a custom background is set, and we've
      // manually toggled the theme mode (not using system), apply the custom background
      // Otherwise, let the theme's default background take precedence
      if (customColors['background'] && theme.colorTheme !== 'system') {
        root.style.setProperty('--background', customColors['background']);
        document.body.style.backgroundColor = customColors['background'];
      }
    } catch (err) {
      console.error('Error applying custom colors:', err);
    }
  }

  // Apply complimentary colors only if they are explicitly set
  const hasHeaderColor = theme.complimentaryColors?.header && theme.complimentaryColors.header !== '';
  const hasSidebarColor = theme.complimentaryColors?.sidebar && theme.complimentaryColors.sidebar !== '';
  const hasFooterColor = theme.complimentaryColors?.footer && theme.complimentaryColors.footer !== '';

  if (hasHeaderColor) {
    root.style.setProperty('--header-background', theme.complimentaryColors!.header!);
  } else if (customColors['header-background']) {
    // Keep the custom header color if set
    root.style.setProperty('--header-background', customColors['header-background']);
  } else {
    root.style.removeProperty('--header-background');
  }

  if (hasSidebarColor) {
    root.style.setProperty('--sidebar-background', theme.complimentaryColors!.sidebar!);
  } else if (customColors['sidebar-background']) {
    // Keep the custom sidebar color if set
    root.style.setProperty('--sidebar-background', customColors['sidebar-background']);
  } else {
    root.style.removeProperty('--sidebar-background');
  }

  if (hasFooterColor) {
    root.style.setProperty('--footer-background', theme.complimentaryColors!.footer!);
  } else if (customColors['footer-background']) {
    // Keep the custom footer color if set
    root.style.setProperty('--footer-background', customColors['footer-background']);
  } else {
    root.style.removeProperty('--footer-background');
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
