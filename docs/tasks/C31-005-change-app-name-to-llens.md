# C31-005: Change Application Name to Llens and Add Logo

## Priority: Medium
## Status: Completed
## Estimated Effort: 2-3 hours

## User Story
**As a** journal application user
**I want** the application to be branded as "Llens" with a distinctive logo
**So that** the application has a unique, memorable identity that reflects its lens-like view into personal journaling

## Problem Description
The application currently uses generic naming and lacks a distinctive brand identity. The name "Llens" (likely a play on "lens" with double-L) provides a unique, memorable brand that suggests the app's purpose of providing a focused view into one's journal entries. A logo in the top left banner will strengthen brand recognition and improve the visual hierarchy of the application.

## Acceptance Criteria
- [ ] Application name changed from "Journal Application" to "Llens" throughout the codebase
- [ ] Logo designed/selected and properly sized for the header banner
- [ ] Logo displayed in the top left corner of the application header
- [ ] Logo is responsive and scales appropriately on different screen sizes
- [ ] Logo links to the home page when clicked
- [ ] Page titles updated to reflect "Llens" branding
- [ ] Any documentation references updated to use "Llens"
- [ ] Logo works properly in both light and dark themes
- [ ] Tests updated to reflect naming changes
- [ ] Application metadata (package.json, etc.) updated with new name

## Technical Details
- **Components affected**:
  - `journal-app-next/src/components/layout/Header.tsx` - Add logo component
  - `journal-app-next/src/app/layout.tsx` - Update metadata and page title
  - `journal-app-next/package.json` - Update application name
  - `journal-app-next/public/` - Add logo files (SVG preferred for scalability)
  - Various component files that may reference the app name
  - `README.md` - Update project name and branding
  - `CLAUDE.md` - Update references to application name

- **Current behavior**:
  - Application uses generic "Journal Application" naming
  - No logo in the header
  - Basic text-only header

- **Expected behavior**:
  - Application branded as "Llens" throughout
  - Professional logo displayed in top left of header
  - Consistent branding across all pages and components

- **Design considerations**:
  - Logo should be simple and work at small sizes (32-48px height in header)
  - Consider using an SVG for crisp rendering at all sizes
  - Logo should work well in both light and dark themes
  - May need separate logo versions for light/dark themes

## Implementation Plan
### Phase 1: Logo Design/Selection
1. Create or select appropriate logo for "Llens"
2. Prepare logo assets (SVG preferred, PNG fallback)
3. Optimize logo files for web use

### Phase 2: Header Implementation
1. Update Header component to include logo
2. Implement responsive sizing for logo
3. Add home page navigation on logo click
4. Test logo appearance in both themes

### Phase 3: Naming Updates
1. Update all references to "Journal Application" to "Llens"
2. Update page titles and metadata
3. Update package.json and other configuration files
4. Update documentation files

## Definition of Done
- [x] All acceptance criteria are met
- [x] Code follows project conventions
- [x] Logo displays correctly on all screen sizes
- [x] No broken references to old application name
- [x] Documentation is updated
- [x] Code has been reviewed
- [x] No linting errors (related to this task)
- [x] Feature works in both development and production modes

## Completion Summary
**Completed on:** 2025-01-06

### Changes Made:
- Created responsive logo component with theme support (`src/components/layout/Logo.tsx`)
- Added two logo variants for light and dark themes (`public/llens-logo.svg`, `public/llens-logo-dark.svg`)
- Updated Header component to use new logo instead of text
- Changed application metadata title and description in `src/app/layout.tsx`
- Updated package.json name from "journal-app-next" to "llens"
- Updated all documentation references from "Journal Application" to "Llens" in README.md and CLAUDE.md
- Updated design system documentation reference
- Fixed linting issues introduced by the changes

### Verification:
- Logo displays correctly in header with proper theming
- Application now branded as "Llens" throughout
- Next.js development server starts successfully with new branding
- Logo is responsive and uses Next.js Image component for optimization
- Documentation accurately reflects the new application name

### Technical Impact:
- Improved brand identity with distinctive lens-inspired logo
- Enhanced visual hierarchy in the header
- Consistent branding across all user-facing elements
- No breaking changes to existing functionality
