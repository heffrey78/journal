# Task Tracking System How-To Guide

This guide explains how to use the markdown-based task tracking system for the Journal Application project.

## Overview

The task tracking system uses markdown files to document and track development tasks. Each task represents a specific feature, bug fix, or improvement, organized by commit/sprint numbers.

## Task File Naming Convention

All task files follow this naming pattern:
```
CXX-NNN-description.md
```

- **CXX**: Commit/Sprint number (e.g., C29, C30, C31)
- **NNN**: Three-digit task number (001, 002, 003)
- **description**: Kebab-case description (e.g., fix-semantic-search, add-user-settings)

Examples:
- `C29-001-fix-semantic-search-sql-error.md`
- `C30-001-unify-frontend-design-system.md`

## Creating a New Task

### Step 1: Determine Task Number

1. Check existing tasks in the current commit/sprint
2. Use the next available number (e.g., if C31-003 exists, create C31-004)
3. If starting a new commit/sprint, begin with 001

### Step 2: Create Task File

Use this template for all new tasks:

```markdown
# CXX-NNN: Task Title Here

## Priority: [High/Medium/Low]
## Status: Pending
## Estimated Effort: X-Y hours

## User Story
**As a** [user type]
**I want** [goal/feature]
**So that** [benefit/value]

## Problem Description
[Detailed description of the issue or feature need. Include context,
current limitations, and why this task is important.]

## Acceptance Criteria
- [ ] Criterion 1 (specific and testable)
- [ ] Criterion 2
- [ ] Criterion 3
- [ ] Tests are written and passing
- [ ] Documentation is updated

## Technical Details
- **Components affected**:
  - `path/to/file1.py`
  - `path/to/component.tsx`
- **Current behavior**: [What happens now]
- **Expected behavior**: [What should happen after implementation]
- **Database changes**: [If applicable]
- **API changes**: [If applicable]

## Implementation Plan (optional for complex tasks)
### Phase 1: [Description]
1. Step 1
2. Step 2

### Phase 2: [Description]
1. Step 1
2. Step 2

## Dependencies (optional)
- Depends on: CXX-NNN (if applicable)
- Blocks: CXX-NNN (if applicable)

## Definition of Done
- [ ] All acceptance criteria are met
- [ ] Code follows project conventions
- [ ] Tests provide adequate coverage
- [ ] Documentation is updated
- [ ] Code has been reviewed
- [ ] No linting errors
- [ ] Feature works in both development and production modes
```

### Step 3: Set Appropriate Priority

- **High**: Critical bugs, security issues, or features blocking other work
- **Medium**: Important features or significant improvements
- **Low**: Nice-to-have features, minor improvements, or technical debt

### Step 4: Estimate Effort

Provide realistic time estimates:
- Simple tasks: 1-2 hours
- Moderate tasks: 2-4 hours
- Complex tasks: 4-8 hours
- Very complex tasks: 8-12 hours

If a task requires more than 12 hours, consider breaking it into smaller tasks.

## Working on a Task

### Starting Work

1. Update status to "In Progress":
   ```markdown
   ## Status: In Progress
   ```

2. If working on multiple tasks, update the summary file to reflect current status

### During Development

- Check off acceptance criteria as you complete them:
  ```markdown
  - [x] Criterion 1 (specific and testable)
  - [ ] Criterion 2
  ```

- Add notes if you discover additional considerations:
  ```markdown
  ## Notes
  - Discovered that X also needs to be updated
  - Consider Y for future improvement
  ```

### Completing a Task

1. Update status to "Completed":
   ```markdown
   ## Status: Completed
   ```

2. Add completion summary at the end of the file:
   ```markdown
   ## Completion Summary
   **Completed on:** 2024-01-15

   ### Changes Made:
   - Implemented X feature in `app/api.py`
   - Added Y component to `journal-app-next/src/components/`
   - Updated database schema to include Z
   - Added comprehensive tests in `test_feature.py`

   ### Verification:
   - All tests passing (pytest test_feature.py)
   - Manual testing completed for scenarios A, B, and C
   - Verified feature works in both light and dark themes
   - Performance impact minimal (tested with 1000+ entries)

   ### Technical Impact:
   - Improved query performance by 40%
   - Reduced API response time from 200ms to 120ms
   - Added reusable component that can be used in other features
   ```

3. Update the summary file to show task as completed

## Creating Summary Files

For each commit/sprint, create a summary file (e.g., `C31-summary.md`):

```markdown
# Commit 31: [Theme/Focus] - Task Summary

## Overview
[Brief description of what this commit/sprint aims to achieve]

## Tasks

### High Priority
- [ ] [C31-001: Task Title](./C31-001-task-name.md) - **Status: Pending** (4-6 hours)
  - Brief description of what this task accomplishes

### Medium Priority
- [ ] [C31-002: Task Title](./C31-002-task-name.md) - **Status: Pending** (2-4 hours)
  - Brief description

### Low Priority
- [ ] [C31-003: Task Title](./C31-003-task-name.md) - **Status: Pending** (1-2 hours)
  - Brief description

## Total Estimated Effort
- High Priority: X hours
- Medium Priority: Y hours
- Low Priority: Z hours
- **Total: N hours**

## Implementation Order
1. C31-001 (establishes foundation)
2. C31-002 (builds on C31-001)
3. C31-003 (nice-to-have addition)

## Dependencies
- C31-002 depends on C31-001 completion
- C31-003 can be done independently

## Success Metrics
- [Metric 1: e.g., Search performance improved by 30%]
- [Metric 2: e.g., User satisfaction with new feature]
```

## Best Practices

### Writing Good User Stories
- Focus on the user's perspective, not technical implementation
- Be specific about the user type (journal writer, power user, admin)
- Clearly articulate the value/benefit

### Creating Acceptance Criteria
- Make them specific and testable
- Include both functional and non-functional requirements
- Consider edge cases and error scenarios
- Always include testing and documentation requirements

### Technical Details
- List specific files that will be modified
- Include code examples when helpful
- Document API/database changes explicitly
- Consider performance implications

### Task Sizing
- Keep tasks small and focused
- If a task has more than 5-6 acceptance criteria, consider splitting it
- Complex features should be broken into multiple tasks
- Each task should deliver value independently when possible

### Documentation
- Update documentation as part of the task, not separately
- Include both code comments and user documentation
- Update CLAUDE.md if introducing new patterns or dependencies

## Task Status Workflow

```
Pending → In Progress → Completed
```

Tasks should move through these statuses sequentially. If a task is blocked or needs to be revisited:
- Add a note explaining the blockage
- Consider creating a new task for the remaining work
- Update the summary file to reflect the current situation

## Finding Tasks

### By Status
Look at summary files to quickly see task statuses

### By Topic
Use grep or search for keywords in task descriptions

### By Priority
Summary files organize tasks by priority level

## Example Task Lifecycle

1. **Identify Need**: User reports search is broken
2. **Create Task**: `C29-001-fix-semantic-search-sql-error.md`
3. **Set Priority**: High (search is critical functionality)
4. **Estimate**: 2-4 hours
5. **Work**: Update status to "In Progress"
6. **Complete**: Fix issue, add tests, update status
7. **Document**: Add completion summary with changes
8. **Update Summary**: Mark as completed in `C29-summary.md`

## Tips for Success

1. **Be Specific**: Vague tasks lead to scope creep
2. **Think User-First**: Always start with the user story
3. **Document Decisions**: Use the Notes section for important decisions
4. **Test Everything**: Include testing in acceptance criteria
5. **Stay Organized**: Keep summary files up to date
6. **Communicate Progress**: Regular status updates help team coordination

## Conclusion

This task tracking system provides a simple yet powerful way to manage development work. By following these guidelines, you'll create clear, actionable tasks that drive the project forward while maintaining excellent documentation for future reference.
