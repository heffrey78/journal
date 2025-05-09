/**
 * Breakpoint System
 *
 * This file defines the standardized breakpoints for responsive design.
 * All components should use these values for consistent responsive behavior.
 *
 * These values match Tailwind's default breakpoints for consistency:
 * - sm: 640px
 * - md: 768px
 * - lg: 1024px
 * - xl: 1280px
 * - 2xl: 1536px
 */

export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
};

export type BreakpointKey = keyof typeof breakpoints;

/**
 * Creates a media query string for min-width (mobile first)
 */
export const minWidth = (key: BreakpointKey): string => {
  return `@media (min-width: ${breakpoints[key]}px)`;
};

/**
 * Creates a media query string for max-width
 */
export const maxWidth = (key: BreakpointKey): string => {
  return `@media (max-width: ${breakpoints[key] - 1}px)`;
};

/**
 * Creates a media query string for a range between two breakpoints
 */
export const between = (minKey: BreakpointKey, maxKey: BreakpointKey): string => {
  return `@media (min-width: ${breakpoints[minKey]}px) and (max-width: ${breakpoints[maxKey] - 1}px)`;
};

/**
 * Responsive object type for defining values at different breakpoints
 */
export type ResponsiveValue<T> = {
  base: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  '2xl'?: T;
};

export default breakpoints;
