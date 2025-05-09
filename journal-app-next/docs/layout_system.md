# Layout Standardization System

This document describes the standardized layout system implemented as part of Phase 3 of the UI standardization plan. It provides guidelines for creating consistent layouts across the application.

## Core Layout Components

### Container

A responsive container with standardized horizontal padding and max-width options.

```tsx
import { Container } from '@/components/layout';

// Basic usage
<Container>
  Content goes here
</Container>

// With custom max width
<Container maxWidth="lg">
  Content constrained to large width
</Container>

// Available maxWidth options: 'sm', 'md', 'lg', 'xl', '2xl', 'full'
```

### Stack

For vertical arrangement of elements with consistent spacing.

```tsx
import { Stack } from '@/components/layout';

<Stack gap="md">
  <div>First item</div>
  <div>Second item</div>
  <div>Third item</div>
</Stack>

// Available gap options: 'none', 'xs', 'sm', 'md', 'lg', 'xl'
// Available align options: 'start', 'center', 'end', 'stretch'
```

### Cluster

For horizontal arrangement of elements with consistent spacing.

```tsx
import { Cluster } from '@/components/layout';

<Cluster gap="sm" align="center" justify="between">
  <div>Left content</div>
  <div>Right content</div>
</Cluster>

// Available gap options: 'none', 'xs', 'sm', 'md', 'lg', 'xl'
// Available align options: 'start', 'center', 'end', 'stretch'
// Available justify options: 'start', 'center', 'end', 'between', 'around', 'evenly'
```

### Grid

For grid-based layouts with responsive column configurations.

```tsx
import { Grid } from '@/components/layout';

// Simple fixed column grid
<Grid columns={3} gap="md">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
  <div>Item 4</div>
  <div>Item 5</div>
</Grid>

// Responsive grid
<Grid
  columns={{
    initial: 1,
    sm: 2,
    md: 3,
    lg: 4
  }}
  gap="md"
>
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</Grid>
```

### ContentPadding

A utility component for consistent internal padding.

```tsx
import { ContentPadding } from '@/components/layout';

<ContentPadding size="md">
  Content with standardized padding
</ContentPadding>

// Available size options: 'none', 'xs', 'sm', 'md', 'lg', 'xl'
```

## Page Structure Components

### PageLayout

Extends MainLayout for consistent page structure.

```tsx
import { PageLayout } from '@/components/layout';

<PageLayout
  header={<h1>Page Title</h1>}
  maxWidth="xl"
>
  Page content
</PageLayout>
```

### PageSection

For consistent page sections with title and content areas.

```tsx
import { PageSection } from '@/components/layout';

<PageSection
  title="Section Title"
  description="Optional section description text"
  divider
>
  Section content
</PageSection>
```

### SplitLayout

For side-by-side content with responsive behavior.

```tsx
import { SplitLayout } from '@/components/layout';

<SplitLayout
  sidebar={<div>Sidebar content</div>}
  sidebarPosition="left"
  sidebarWidth="300px"
  stackBelowBreakpoint="md"
>
  Main content
</SplitLayout>
```

### ResponsiveLayout

Advanced component for standard responsive layout patterns.

```tsx
import { ResponsiveLayout } from '@/components/layout';

<ResponsiveLayout
  sidebar={<div>Sidebar content</div>}
  type="sidebar-content"
  collapseBelow="md"
>
  Main content
</ResponsiveLayout>

// Available type options:
// - 'sidebar-content' (default)
// - 'equal-columns'
// - 'content-sidebar-sidebar'
```

## Content Organization Components

### CardGrid

For grid-based card layouts with responsive options.

```tsx
import { CardGrid } from '@/components/layout';

<CardGrid minWidth="320px" gap="md">
  <Card>Card 1</Card>
  <Card>Card 2</Card>
  <Card>Card 3</Card>
</CardGrid>
```

### CardList

For vertical lists of cards with optional dividers.

```tsx
import { CardList } from '@/components/layout';

<CardList gap="md" dividers>
  <Card>Card 1</Card>
  <Card>Card 2</Card>
  <Card>Card 3</Card>
</CardList>
```

## Spacing System

The layout system uses a standardized spacing scale:

| Token | Value | Tailwind | Description |
|-------|-------|----------|-------------|
| none  | 0px   | gap-0    | No spacing  |
| xs    | 0.5rem | gap-2   | Extra small spacing (8px) |
| sm    | 1rem  | gap-4    | Small spacing (16px) |
| md    | 1.5rem | gap-6   | Medium spacing (24px) |
| lg    | 2rem  | gap-8    | Large spacing (32px) |
| xl    | 2.5rem | gap-10  | Extra large spacing (40px) |

Import the spacing system for direct use:

```tsx
import { spacing } from '@/lib/spacing';

// In inline styles
<div style={{ marginTop: spacing.md }}>Content</div>

// With utility functions
import { getSpacing, getSpacingPx } from '@/lib/spacing';
<div style={{ padding: getSpacing('md') }}>Content</div>
```

## Responsive Behavior

The layout system uses consistent breakpoints aligned with Tailwind's defaults:

| Breakpoint | Width  | Description        |
|------------|--------|--------------------|
| sm         | 640px  | Small screens      |
| md         | 768px  | Medium screens     |
| lg         | 1024px | Large screens      |
| xl         | 1280px | Extra large screens|
| 2xl        | 1536px | 2x large screens   |

Import the breakpoint system for direct use:

```tsx
import { minWidth, maxWidth, between } from '@/lib/breakpoints';

// In CSS-in-JS
const styles = {
  container: {
    width: '100%',
    [minWidth('md')]: {
      width: '80%',
    },
    [minWidth('lg')]: {
      width: '70%',
    }
  }
};
```

## Best Practices

1. **Use layout components instead of direct Tailwind classes** for consistent spacing and structure
2. **Follow the mobile-first approach** when building responsive layouts
3. **Use semantic tokens** instead of hardcoded values for colors and spacing
4. **Compose layouts from smaller components** rather than building monolithic layouts
5. **Use Container for width constraints** instead of arbitrary max-width values
6. **Use Stack and Cluster** for common flex-based layouts
7. **Use Grid for multi-column layouts** instead of custom grid implementations
8. **PageSection for consistent page sections** with standardized title and content areas
