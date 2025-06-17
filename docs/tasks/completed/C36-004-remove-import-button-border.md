# C36-004: Remove Border Around Import Button

## Priority: Low
## Status: Completed
## Estimated Effort: 0.5-1 hours

## User Story
**As a** journal user
**I want** the import button to have a clean appearance without unnecessary borders
**So that** the interface looks more polished and consistent with the overall design

## Problem Description
The import button currently has a visible border that makes it stand out in an undesirable way from the rest of the interface. Removing this border will improve the visual consistency and create a cleaner, more modern appearance that aligns with the overall design system.

## Acceptance Criteria
- [x] Import button border is removed or made invisible
- [x] Button maintains proper hover and focus states
- [x] Button remains accessible and clearly clickable
- [x] Visual appearance is consistent with other similar buttons in the interface
- [x] No regression in button functionality
- [x] Change follows existing design system patterns
- [x] Button styling is consistent across different themes (light/dark)

## Technical Details
- **Components affected**:
  - Component containing the import button (likely in entries or settings area)
  - Related CSS/styling files
  - Button component styling

- **Current behavior**: Import button displays with visible border
- **Expected behavior**: Import button displays without border, maintaining clean appearance

- **Implementation approach**:
  - Locate import button component/styling
  - Remove or override border styles
  - Ensure hover/focus states remain functional
  - Test across different themes and screen sizes

## Investigation Required
1. Locate the import button in the codebase
2. Identify current styling approach (CSS classes, inline styles, etc.)
3. Determine if border is applied via base button styles or specific overrides
4. Check if change affects other buttons using similar styling

## Definition of Done
- [ ] All acceptance criteria are met
- [ ] Border removed from import button
- [ ] Button functionality preserved
- [ ] Visual consistency maintained across themes
- [ ] No impact on other button components
- [ ] Code follows project conventions
- [ ] Manual testing confirms clean appearance
- [ ] No linting errors

## Completion Summary
**Completed on:** 2025-01-06

### Changes Made:
1. Located the import button in `GlobalActions.tsx` component (both desktop and mobile versions)
2. Changed button variant from `outline` to `ghost` to remove the border
3. The `ghost` variant provides hover states without a visible border
4. Both desktop and mobile import buttons were updated for consistency

### Files Modified:
- `/journal-app-next/src/components/layout/GlobalActions.tsx`

### Verification:
- Linting passes without errors for the modified file
- The `ghost` variant maintains proper hover and focus states as defined in the button component
- Button remains accessible with proper ARIA labels (sr-only text for mobile)
- The change is consistent with the design system as `ghost` is a standard variant
