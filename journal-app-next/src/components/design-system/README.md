# Design System Documentation

This document outlines the unified design system for Llens, providing consistent components, patterns, and guidelines for maintaining a cohesive user experience.

## Core Principles

1. **Consistency**: All components follow the same design patterns and behaviors
2. **Accessibility**: Components are built with accessibility best practices
3. **Theme Support**: Full light/dark mode compatibility
4. **Responsive**: Mobile-first design that scales to all screen sizes
5. **Performance**: Optimized components with minimal overhead

## Component Library

### Importing Components

```typescript
// Import individual components
import { Button, Card, Input } from '@/components/design-system';

// Or import everything
import * as DS from '@/components/design-system';
```

### Core Components

#### Button
Unified button component with consistent styling and behavior.

```typescript
import { Button } from '@/components/design-system';

// Basic usage
<Button>Click me</Button>

// With variants
<Button variant="outline">Secondary action</Button>
<Button variant="destructive">Delete</Button>

// With sizes
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>

// With loading state
<Button isLoading>Processing...</Button>
```

**Available Props:**
- `variant`: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
- `size`: "default" | "sm" | "lg" | "icon"
- `isLoading`: boolean
- `asChild`: boolean (for composition with other elements)

#### Card Components
Flexible card layout system with consistent styling.

```typescript
import { Card, CardHeader, CardTitle, CardContent } from '@/components/design-system';

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Supporting text</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Card content goes here</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

#### Input
Themed input component with consistent styling.

```typescript
import { Input } from '@/components/design-system';

<Input
  type="text"
  placeholder="Enter text..."
  value={value}
  onChange={(e) => setValue(e.target.value)}
/>
```

#### Pagination
Unified pagination component for consistent navigation.

```typescript
import { Pagination } from '@/components/design-system';

<Pagination
  currentPage={currentPage}
  hasMore={hasMore}
  onPrevious={() => setCurrentPage(prev => prev - 1)}
  onNext={() => setCurrentPage(prev => prev + 1)}
/>

// With total pages (when known)
<Pagination
  currentPage={currentPage}
  totalPages={totalPages}
  onPrevious={() => setCurrentPage(prev => prev - 1)}
  onNext={() => setCurrentPage(prev => prev + 1)}
  showFirstLast={true}
/>
```

**Available Props:**
- `currentPage`: number (0-based)
- `totalPages?`: number
- `hasMore?`: boolean (for infinite scroll)
- `onPrevious`: () => void
- `onNext`: () => void
- `onFirst?`: () => void
- `onLast?`: () => void
- `showFirstLast?`: boolean
- `showPageNumbers?`: boolean
- `size?`: "sm" | "md" | "lg"

### Layout Components

#### Container
Responsive container with consistent max-widths.

```typescript
import { Container } from '@/components/design-system';

<Container maxWidth="4xl">
  <ContentPadding size="md">
    {/* Page content */}
  </ContentPadding>
</Container>
```

**Available Props:**
- `maxWidth`: "sm" | "md" | "lg" | "xl" | "2xl" | "3xl" | "4xl" | "5xl" | "6xl" | "7xl" | "full"
- `className?`: string

#### ContentPadding
Consistent spacing for page content.

```typescript
import { ContentPadding } from '@/components/design-system';

<ContentPadding size="md">
  {/* Content with consistent padding */}
</ContentPadding>
```

**Available Props:**
- `size`: "none" | "xs" | "sm" | "md" | "lg" | "xl"

#### Layout Utilities

```typescript
import { Stack, Cluster, Grid } from '@/components/design-system';

// Vertical stack with consistent spacing
<Stack gap="md">
  <div>Item 1</div>
  <div>Item 2</div>
</Stack>

// Horizontal cluster with auto-wrapping
<Cluster gap="sm" justify="between">
  <div>Left content</div>
  <div>Right content</div>
</Cluster>

// CSS Grid with responsive columns
<Grid columns={{ base: 1, md: 2, lg: 3 }} gap="md">
  <div>Grid item</div>
  <div>Grid item</div>
</Grid>
```

## Design Standards

### Page Layout Pattern

All pages should follow this consistent layout structure:

```typescript
import { MainLayout, Container, ContentPadding } from '@/components/design-system';

export default function MyPage() {
  return (
    <MainLayout>
      <Container maxWidth="4xl" className="mx-auto">
        <ContentPadding size="md">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold">Page Title</h1>
          </div>

          {/* Page content */}

          {/* Pagination at bottom if needed */}
          <Pagination
            currentPage={currentPage}
            hasMore={hasMore}
            onPrevious={handlePrevious}
            onNext={handleNext}
            className="mt-6"
          />
        </ContentPadding>
      </Container>
    </MainLayout>
  );
}
```

### Button Placement Standards

1. **Page Actions**: Top-right of the page header
2. **Form Actions**: Bottom-right of forms, primary action on the right
3. **Card Actions**: Card footer, aligned right
4. **Pagination**: Bottom of content area, full-width with space-between

### Spacing Scale

Use Tailwind's spacing scale consistently:

- `gap-1` (4px): Very tight spacing
- `gap-2` (8px): Tight spacing
- `gap-4` (16px): Normal spacing
- `gap-6` (24px): Loose spacing
- `gap-8` (32px): Very loose spacing

### Color Usage

Rely on Tailwind's semantic color tokens for theme compatibility:

- `text-foreground`: Primary text
- `text-muted-foreground`: Secondary text
- `bg-background`: Page background
- `bg-card`: Card background
- `border-border`: Standard borders
- `text-primary`: Brand/accent color

## Global Features

### Header Actions

Import and "New Entry" actions are globally available in the header across all pages. Page-specific action buttons should be removed to avoid duplication.

### Responsive Behavior

All components are designed mobile-first:

- Stack buttons vertically on mobile
- Hide non-essential elements on small screens
- Use icon-only buttons on mobile when space is limited
- Ensure touch targets are at least 44px

## Migration Guide

When updating existing components:

1. **Replace imports**: Use `@/components/design-system` instead of individual UI imports
2. **Update layouts**: Use Container + ContentPadding pattern
3. **Standardize pagination**: Replace custom pagination with unified component
4. **Remove duplicate actions**: Remove page-specific import/new entry buttons
5. **Use design tokens**: Replace hardcoded styles with theme-aware classes

## Best Practices

1. **Import from design system**: Always prefer design system components over direct UI imports
2. **Consistent spacing**: Use the spacing scale consistently
3. **Semantic HTML**: Use proper HTML elements for accessibility
4. **Theme compatibility**: Test in both light and dark modes
5. **Mobile testing**: Verify responsive behavior on mobile devices

## Contributing

When adding new components to the design system:

1. Follow existing patterns and conventions
2. Ensure full theme support (light/dark)
3. Include proper TypeScript types
4. Add component to the main index.ts export
5. Update this documentation with usage examples
6. Test across different screen sizes

## Examples

See the following pages for reference implementations:

- `/entries` - Standard list page with pagination
- `/search` - Form-heavy page with cards
- `/analyses` - Grid layout with cards
- `/settings` - Settings page layout

Each page demonstrates proper use of the design system components and patterns.
