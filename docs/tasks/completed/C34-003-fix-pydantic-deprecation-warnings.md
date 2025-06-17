# C34-003: Fix Pydantic V2 Deprecation Warnings

## Priority: Medium
## Status: Pending
## Estimated Effort: 1-2 hours

## User Story
**As a** developer maintaining the journal application
**I want** to eliminate deprecation warnings from dependencies
**So that** the codebase remains maintainable and warnings don't clutter the logs

## Problem Description
The application is generating Pydantic deprecation warnings during startup and operation:

```
/home/jeffwikstrom/.pyenv/versions/3.12.4/lib/python3.12/site-packages/pydantic/_internal/_config.py:373: UserWarning: Valid config keys have changed in V2:
* 'schema_extra' has been renamed to 'json_schema_extra'
  warnings.warn(message, UserWarning)
```

This indicates that the codebase is using outdated Pydantic configuration that was deprecated in V2. While not breaking functionality, these warnings clutter the logs and indicate technical debt that should be addressed.

## Acceptance Criteria
- [x] All Pydantic deprecation warnings are eliminated
- [x] `schema_extra` configurations updated to `json_schema_extra`
- [x] Pydantic models follow V2 best practices
- [x] No breaking changes to API response schemas
- [x] All existing tests continue to pass
- [x] Documentation updated if schema generation patterns change
- [x] Clean startup logs without deprecation warnings

## Technical Details
- **Components affected**:
  - `app/models.py` (Pydantic model definitions)
  - Any other files with Pydantic model configurations
- **Current behavior**: Deprecation warnings appear in logs during startup/operation
- **Expected behavior**: Clean logs without Pydantic warnings
- **Change required**: Replace `schema_extra` with `json_schema_extra` in model configurations

## Implementation Plan
### Phase 1: Identify Affected Models
1. Search codebase for all instances of `schema_extra`
2. Review Pydantic model configurations
3. Check for other V2 migration issues

### Phase 2: Update Configurations
1. Replace `schema_extra` with `json_schema_extra`
2. Verify schema generation still works correctly
3. Test API documentation generation
4. Ensure no breaking changes to client code

### Phase 3: Validation
1. Run full test suite to ensure compatibility
2. Verify API schemas match previous behavior
3. Check that OpenAPI documentation is unchanged
4. Confirm warnings are eliminated

## Dependencies
- None identified

## Definition of Done
- [ ] All acceptance criteria are met
- [ ] No Pydantic deprecation warnings in logs
- [ ] All tests passing with updated configurations
- [ ] API schemas remain functionally identical
- [ ] Code follows Pydantic V2 best practices
- [ ] Documentation updated if needed
- [ ] Code has been reviewed
- [ ] No linting errors
- [ ] Clean application startup without warnings
