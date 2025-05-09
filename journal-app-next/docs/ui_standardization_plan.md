# UI Standardization Plan

## Overview

This document outlines the inconsistencies in UI components and styling across the journal application and proposes a standardization plan to create visual consistency between components like BatchAnalysisDialog, EntryAnalysis, EntryList, and others.

## Current Style Inconsistencies

### 1. Button Components
- **Inconsistent Imports:**
  - Some components use `Button` from `@/components/ui/Button.tsx` (capital B)
  - Others use `button` from `@/components/ui/button.tsx` (lowercase b)

- **Style Differences:**
  - EntryAnalysis: Custom button styles with various props like `size="md"`, `variant="outline"`
  - BatchAnalysisResults: Uses shadcn UI consistent button variants (`variant="destructive"`, `size="sm"`)
  - BatchAnalysisDialog: Uses direct Tailwind classes without component abstraction
  - EntryList: Uses direct Tailwind classes for styling buttons

### 2. Card & Container Components
- **Component Discrepancies:**
  - EntryAnalysis: Uses direct div elements with Tailwind classes `bg-card text-card-foreground rounded-lg shadow-md p-6`
  - BatchAnalysisResults: Uses shadcn UI Card components (`Card`, `CardContent`, `CardHeader`, `CardTitle`)
  - EntryList: Uses a custom Card component from `@/components/ui/Card.tsx`

- **Alert/Notification Styles:**
  - EntryAnalysis: Custom alert styles with color-specific classes
  - BatchAnalysisResults: More consistent uses of shadcn UI components
  - BatchAnalysisDialog: Direct Tailwind styling

### 3. Dialog/Modal Components
- **Dialog Implementation:**
  - BatchAnalysisResults: Uses shadcn UI `AlertDialog` components with proper structure
  - BatchAnalysisDialog: Uses Headless UI's Dialog component with different API
  - MoveEntriesDialog: Likely uses a third implementation

### 4. Dark Mode Implementation
- **Approach Differences:**
  - EntryAnalysis: Manual dark mode classes with explicit colors (e.g., `text-gray-700 dark:text-gray-300`)
  - BatchAnalysisResults: Uses design tokens and CSS variables (more maintainable)
  - BatchAnalysisDialog: Uses direct dark mode Tailwind classes

### 5. Badge/Tag Styling
- **Implementation Variances:**
  - EntryAnalysis: Custom badge styles with explicit colors
  - BatchAnalysisResults: Uses shadcn UI `Badge` component
  - EntryList: Custom badge styles with different color palette

### 6. Theme Handling & Custom Colors
- **Inconsistencies:**
  - Proper CSS variables used in some components
  - Hardcoded color values in others
  - Inconsistent application of theme tokens

### 7. Layout & Spacing
- Inconsistent padding, margin values across components
- Different grid/flexbox patterns for similar layouts

## Recommended Standard (Based on BatchAnalysisResults)

Based on the more modern approach used in BatchAnalysisResults, we recommend the following standards:

### 1. UI Component Library
- **Standard:** Use shadcn UI components consistently across the application
- **Components to Standardize:**
  - Button: Use `@/components/ui/button.tsx` everywhere
  - Card: Use shadcn Card components (`Card`, `CardContent`, `CardHeader`, `CardTitle`)
  - Dialog: Use shadcn AlertDialog for confirmations
  - Badge: Use shadcn Badge for tags and status indicators

### 2. Design Tokens & Theming
- **Standard:** Use semantic class names and CSS variables instead of hardcoded colors
- **Examples:**
  - Use `bg-primary` instead of `bg-blue-600`
  - Use `text-foreground` instead of `text-gray-900 dark:text-white`

### 3. Dark Mode Implementation
- **Standard:** Use shadcn UI's theme approach with CSS variables
- **Avoid:** Directly using `dark:` classes with hardcoded colors

### 4. Layout Patterns
- **Standard:** Define consistent spacing and layout patterns
  - Card padding: Use consistent padding (`p-6`)
  - Margins between elements: Use consistent spacing scale
  - Grid/flex layouts: Standardize common patterns

## Implementation Plan

### Phase 1: Component Normalization
1. Standardize Button usage
2. Standardize Card usage
3. Standardize Dialog/Modal usage
4. Standardize Badge/Tag styling

### Phase 2: Theme Token Migration
1. Replace hardcoded colors with semantic class names
2. Ensure dark mode consistency
3. Update custom color implementation to use CSS variables

### Phase 3: Layout Standardization
1. Normalize spacing and layout patterns
2. Create reusable layout components for common patterns

### Phase 4: Documentation
1. Create a component style guide
2. Document theme customization approach

## Components to Refactor (Priority Order)

1. EntryAnalysis.tsx - Update to use shadcn UI components
2. EntryList.tsx - Standardize button and card styling
3. BatchAnalysisDialog.tsx - Update to use shadcn AlertDialog
4. Any remaining components with custom styling

## Next Steps

1. Conduct a complete inventory of all UI components
2. Create a standardized component library with examples
3. Begin migration of high-priority components
4. Test for visual consistency across light/dark modes and with custom colors
