/**
 * This script runs at page load before React hydration to set the correct theme
 * and avoid any flash of unstyled content (FOUC)
 */
function initTheme() {
  try {
    const root = document.documentElement;

    // Get stored theme preference
    const storedTheme = localStorage.getItem('themePreferences');
    let colorTheme = 'system';

    if (storedTheme) {
      try {
        const parsed = JSON.parse(storedTheme);
        colorTheme = parsed.colorTheme;
      } catch (e) {
        // Fallback to legacy theme setting if parsing fails
        const legacyTheme = localStorage.getItem('theme');
        if (legacyTheme) {
          colorTheme = legacyTheme;
        }
      }
    }

    // Apply appropriate theme class
    if (colorTheme === 'dark' ||
        (colorTheme === 'system' &&
         window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      root.classList.add('dark');
    } else {
      root.classList.add('light');
    }

    // Apply custom colors
    const customColors = localStorage.getItem('customThemeColors');
    if (customColors) {
      try {
        const colors = JSON.parse(customColors);
        Object.entries(colors).forEach(([name, value]) => {
          root.style.setProperty(`--${name}`, value as string);
        });
      } catch (e) {
        console.error('Failed to apply custom colors', e);
      }
    }
  } catch (e) {
    // If anything fails, we don't want to break the page
    console.error('Failed to initialize theme', e);
  }
}

export const themeScript = `(${initTheme.toString()})()`;
