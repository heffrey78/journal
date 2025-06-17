'use client';

import { useEffect, useState } from 'react';
import { useTheme } from '../layout/ThemeProvider';

type ThemeToggleProps = {
  className?: string;
};

export default function ThemeToggle({ className = '' }: ThemeToggleProps) {
  // Safe default state for isDarkMode
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Use a try-catch to safely access the theme context
  let themeContext;
  try {
    themeContext = useTheme();
  } catch (e) {
    // Silently handle the case where theme context isn't ready yet
    // This is expected during initial render
  }

  // Wait for component to mount to avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  // Update isDarkMode whenever theme changes or system preference changes
  useEffect(() => {
    if (!mounted || !themeContext?.theme) return;

    // Function to check if dark mode is currently active
    const checkIsDarkMode = () => {
      const { colorTheme } = themeContext.theme;
      return colorTheme === 'dark' ||
        (colorTheme === 'system' &&
         window.matchMedia('(prefers-color-scheme: dark)').matches);
    };

    // Set the initial state
    setIsDarkMode(checkIsDarkMode());

    // If using system theme, also listen for system preference changes
    if (themeContext.theme.colorTheme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

      const handleChange = () => {
        setIsDarkMode(checkIsDarkMode());
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [mounted, themeContext?.theme]);

  // Handle toggle with fallback
  const handleToggle = () => {
    if (themeContext?.toggleDarkMode) {
      themeContext.toggleDarkMode();
      // We don't need to manually update isDarkMode here
      // The effect above will handle it based on the theme change
    } else {
      // Theme toggle not available yet, silently ignore
    }
  };

  if (!mounted) {
    // Return empty div with same dimensions to prevent layout shift
    return <div className={`w-10 h-10 ${className}`} />;
  }

  return (
    <button
      onClick={handleToggle}
      className={`p-2 rounded-md hover:bg-accent transition-colors ${className}`}
      title={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
      aria-label={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
    >
      {isDarkMode ? (
        <MoonIcon className="h-6 w-6 text-foreground" />
      ) : (
        <SunIcon className="h-6 w-6 text-amber-500" />
      )}
    </button>
  );
}

// Sun icon for light mode
function SunIcon({ className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z" />
    </svg>
  );
}

// Moon icon for dark mode
function MoonIcon({ className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path fillRule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" clipRule="evenodd" />
    </svg>
  );
}
