/**
 * Spacing System
 *
 * This file defines the standardized spacing scale for the application.
 * All components should use these values for consistent spacing.
 *
 * Usage in Tailwind classes:
 * - p-2 (equivalent to spacing.xs)
 * - gap-4 (equivalent to spacing.sm)
 * - m-6 (equivalent to spacing.md)
 * - etc.
 *
 * Usage in styles:
 * - import { spacing } from '@/lib/spacing';
 * - style={{ padding: spacing.md }}
 */

export const spacing = {
  none: '0px',
  xs: '0.5rem', // 8px - Equivalent to p-2, m-2 etc.
  sm: '1rem',   // 16px - Equivalent to p-4, m-4 etc.
  md: '1.5rem', // 24px - Equivalent to p-6, m-6 etc.
  lg: '2rem',   // 32px - Equivalent to p-8, m-8 etc.
  xl: '2.5rem', // 40px - Equivalent to p-10, m-10 etc.
};

export const inlineSpacing = {
  none: 0,
  xs: 8,
  sm: 16,
  md: 24,
  lg: 32,
  xl: 40,
};

export type SpacingKey = keyof typeof spacing;

/**
 * Helper function to get spacing value from key
 */
export const getSpacing = (key: SpacingKey): string => spacing[key];

/**
 * Helper function to get spacing value in pixels
 */
export const getSpacingPx = (key: SpacingKey): number => inlineSpacing[key];

export default spacing;
