# Journal App Theme System

## Overview

The Journal App uses a comprehensive theme system built on CSS variables and Tailwind CSS. This approach provides:

1. Consistent design language across all components
2. Easy light/dark mode switching
3. Support for custom theme colors
4. Maintainable and scalable styling

## Theme Architecture

### Core Components

1. **CSS Variables** (`globals.css`)
   - Base definition of all colors, spacing, and typography
   - Light/dark mode variants
   - User-customizable properties

2. **Tailwind Configuration** (`tailwind.config.js`)
   - Maps CSS variables to Tailwind classes
   - Extends Tailwind with theme-specific utilities

3. **Token Documentation** (`src/lib/tokens.ts`)
   - TypeScript constants for all available tokens
   - Usage examples and component patterns
   - Organized by semantic categories

4. **ThemeProvider** (`src/components/layout/ThemeProvider.tsx`)
   - React context for theme settings
   - Handles theme preference persistence
   - Provides theme switching functions

## Usage Guide

### Basic Usage

Use semantic class names instead of hardcoded colors:

```tsx
// ❌ Avoid
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
  <h2 className="text-blue-600 dark:text-blue-400">Title</h2>
</div>

// ✅ Recommended
<div className="bg-background text-foreground">
  <h2 className="text-primary">Title</h2>
</div>
```

### Available Token Categories

1. **Base Colors**
   - Background: `bg-background`
   - Foreground (text): `text-foreground`

2. **Theme Colors**
   - Primary: `bg-primary`, `text-primary`, `text-primary-foreground`
   - Secondary: `bg-secondary`, `text-secondary`, `text-secondary-foreground`
   - Accent: `bg-accent`, `text-accent`, `text-accent-foreground`

3. **UI Elements**
   - Card: `bg-card`, `text-card-foreground`
   - Popover: `bg-popover`, `text-popover-foreground`
   - Muted: `bg-muted`, `text-muted-foreground`
   - Border: `border-border`
   - Input: `border-input`
   - Ring: `ring-ring`

4. **Status Colors**
   - Success: `bg-success`, `text-success-foreground`
   - Warning: `bg-warning`, `text-warning-foreground`
   - Error/Destructive: `bg-destructive`, `text-destructive-foreground`, `text-destructive`
   - Info: `bg-info`, `text-info-foreground`

### Programmatic Usage

Import token groups for more complex styling:

```tsx
import { themeColors, statusTokens, componentPatterns } from '@/lib/tokens';

function MyComponent() {
  return (
    <div>
      <button className={componentPatterns.button.primary}>
        Primary Button
      </button>

      <div className={`${statusTokens.warning.light} ${statusTokens.warning.border} p-3 rounded-md`}>
        <p>Warning message</p>
      </div>
    </div>
  );
}
```

## Theme Customization

### User-Facing Customization

The app supports user customization through:

1. **Theme Switching** - Toggle between light/dark modes
2. **Color Theme Selection** - Choose from predefined color themes
3. **Font Settings** - Change font family, size, and line height
4. **Custom Colors** - Define custom color values for key UI elements

These settings are managed through the `ThemeSettings` component and are persisted in local storage.

### Developer Customization

To extend the theme system:

1. Add new CSS variables in `globals.css`
2. Update the Tailwind configuration in `tailwind.config.js` if needed
3. Add documentation for new tokens in `src/lib/tokens.ts`

## Common Components and Patterns

The theme system works with shadcn UI components to provide consistent styling:

1. **Button Variants**
   - Primary, Secondary, Outline, Ghost, Destructive

2. **Card Styling**
   - Use `bg-card text-card-foreground rounded-lg shadow`

3. **Dialog/Modal Styling**
   - Use shadcn AlertDialog with theme tokens

4. **Form Elements**
   - Use shadcn Form components with theme tokens

## Migration Guide

For detailed instructions on migrating components to use the theme system, see:
- [Theme Migration Guide](./theme_migration_guide.md)

## Design Philosophy

Our theme system follows these principles:

1. **Semantic over Literal** - Use `bg-primary` instead of `bg-blue-500`
2. **Consistency over Customization** - Follow established patterns
3. **Dark Mode by Default** - All components should work in both modes
4. **Accessibility First** - Ensure proper contrast and readability
