/**
 * Theme Tokens Documentation
 *
 * This file serves as documentation for the theme tokens available in the application.
 * These tokens should be used consistently throughout the app to maintain a cohesive design.
 *
 * Using these tokens allows for:
 * 1. Consistent design across the application
 * 2. Easier theme switching (light/dark mode)
 * 3. Simpler global theme adjustments
 * 4. Better maintainability
 */

/**
 * Base color tokens
 * Use these for the main background and text colors
 */
export const baseColors = {
  background: 'bg-background',     // Main background color (white in light mode, dark gray in dark mode)
  foreground: 'text-foreground',   // Main text color (dark gray in light mode, white in dark mode)
}

/**
 * Theme color tokens
 * Use these for primary, secondary, and accent UI elements
 */
export const themeColors = {
  // Primary (blue)
  primary: {
    DEFAULT: 'bg-primary',                 // Background color
    hover: 'hover:bg-primary/90',          // Slightly lighter/darker on hover
    text: 'text-primary',                  // Text in primary color
    foreground: 'text-primary-foreground', // Text on primary background
    border: 'border-primary',              // Border in primary color
    ring: 'ring-primary',                  // Focus ring in primary color
    outline: 'outline-primary',            // Outline in primary color
  },

  // Secondary (light gray in light mode, dark gray in dark mode)
  secondary: {
    DEFAULT: 'bg-secondary',                 // Background color
    hover: 'hover:bg-secondary/90',          // Slightly lighter/darker on hover
    text: 'text-secondary',                  // Text in secondary color
    foreground: 'text-secondary-foreground', // Text on secondary background
    border: 'border-secondary',              // Border in secondary color
  },

  // Accent (light blue in light mode, darker blue in dark mode)
  accent: {
    DEFAULT: 'bg-accent',                 // Background color
    hover: 'hover:bg-accent/90',          // Slightly lighter/darker on hover
    text: 'text-accent',                  // Text in accent color
    foreground: 'text-accent-foreground', // Text on accent background
    border: 'border-accent',              // Border in accent color
  },
}

/**
 * UI Element tokens
 * Use these for cards, popovers, muted elements, borders, and inputs
 */
export const uiTokens = {
  // Cards
  card: {
    background: 'bg-card',             // Card background
    foreground: 'text-card-foreground', // Text on card
    hover: 'hover:bg-card/90',         // Card hover state
  },

  // Popover elements
  popover: {
    background: 'bg-popover',             // Popover background
    foreground: 'text-popover-foreground', // Text on popover
  },

  // Muted elements (less prominent UI)
  muted: {
    background: 'bg-muted',             // Muted background
    foreground: 'text-muted-foreground', // Muted text
    hover: 'hover:text-foreground',     // Hover state for muted text (changes to regular text color)
  },

  // Borders and dividers
  border: {
    DEFAULT: 'border-border',         // Standard border
    hover: 'hover:border-primary',    // Border hover state
    focus: 'focus:border-primary',    // Border focus state
  },

  // Input elements
  input: {
    DEFAULT: 'border-input',           // Input border
    focus: 'focus:border-primary',    // Input focus border
    background: 'bg-background',       // Input background
    text: 'text-foreground',           // Input text
  },

  // Ring for focus states
  ring: {
    DEFAULT: 'ring-ring',              // Standard focus ring
    focus: 'focus:ring-2',            // Focus ring thickness
    offset: 'focus:ring-offset-2',    // Focus ring offset
  }
}

/**
 * Status tokens
 * Use these for indicating status, errors, warnings, success, etc.
 */
export const statusTokens = {
  // Success (green)
  success: {
    background: 'bg-success',
    foreground: 'text-success-foreground',
    light: 'bg-success/10',
    border: 'border-success/30',
  },

  // Warning (amber)
  warning: {
    background: 'bg-warning',
    foreground: 'text-warning-foreground',
    light: 'bg-warning/10',
    border: 'border-warning/30',
  },

  // Error/destructive (red)
  destructive: {
    background: 'bg-destructive',
    foreground: 'text-destructive-foreground',
    light: 'bg-destructive/10',
    border: 'border-destructive/30',
    text: 'text-destructive',
  },

  // Info (blue)
  info: {
    background: 'bg-info',
    foreground: 'text-info-foreground',
    light: 'bg-info/10',
    border: 'border-info/30',
  },
}

/**
 * Radius tokens
 * Use these for consistent rounding of corners
 */
export const radiusTokens = {
  none: 'rounded-none',
  sm: 'rounded-sm',  // calc(var(--radius) - 4px)
  md: 'rounded-md',  // calc(var(--radius) - 2px)
  lg: 'rounded-lg',  // var(--radius) (default: 0.5rem)
  xl: 'rounded-xl',
  '2xl': 'rounded-2xl',
  full: 'rounded-full',
}

/**
 * Common component patterns using tokens
 * These are common styling patterns for reuse across components
 */
export const componentPatterns = {
  // Standard button patterns
  button: {
    primary: `bg-primary text-primary-foreground hover:bg-primary/90`,
    secondary: `bg-secondary text-secondary-foreground hover:bg-secondary/90`,
    outline: `border border-input bg-transparent hover:bg-accent hover:text-accent-foreground`,
    ghost: `hover:bg-accent hover:text-accent-foreground`,
    destructive: `bg-destructive text-destructive-foreground hover:bg-destructive/90`,
    link: `text-primary underline-offset-4 hover:underline`,
  },

  // Badge patterns
  badge: {
    default: `bg-primary text-primary-foreground`,
    secondary: `bg-secondary text-secondary-foreground`,
    outline: `text-foreground border border-border`,
    destructive: `bg-destructive text-destructive-foreground`,
  },

  // Alert/notification patterns
  alert: {
    default: `bg-background text-foreground border border-border`,
    destructive: `bg-destructive/10 text-destructive border border-destructive/30`,
    warning: `bg-warning/10 text-foreground border border-warning/30`,
    success: `bg-success/10 text-foreground border border-success/30`,
    info: `bg-info/10 text-foreground border border-info/30`,
  }
}

/**
 * Typography tokens
 * Use these for consistent text styling
 */
export const typographyTokens = {
  size: {
    small: `text-size-small`,
    base: `text-size-base`,
    large: `text-size-large`,
    xl: `text-size-xl`,
    '2xl': `text-size-2xl`,
  },
}

/**
 * Usage examples:
 *
 * // Button with primary styling
 * <button className={componentPatterns.button.primary}>Submit</button>
 *
 * // Card with theme tokens
 * <div className="bg-card text-card-foreground p-4 rounded-lg">Card content</div>
 *
 * // Status message with destructive styling
 * <div className={`${statusTokens.destructive.light} ${statusTokens.destructive.border} p-3 rounded-md`}>
 *   <p className={statusTokens.destructive.text}>Error message</p>
 * </div>
 */
