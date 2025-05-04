# Journal App Enhancement Plan - Phase 2

This incremental plan outlines the next phase of enhancements for the Journal App, building on the completed MVP. The focus areas include markdown editing support, LLM service configuration, image storage, and user experience improvements.

## Phase 8: Enhanced Markdown Support

### Commit 18: Markdown Editor Integration
```
git commit -m "Integrate EasyMDE markdown editor for improved writing experience"
```
- Add EasyMDE library to the project
- Implement EasyMDE in entry creation form
- Update entry editing form with markdown editor
- Add basic preview functionality
- Ensure compatibility with existing markdown processing

### Commit 19: Enhanced Markdown Rendering
```
git commit -m "Enhance markdown rendering with improved library and features"
```
- Replace basic markdown rendering with marked.js
- Add support for advanced markdown features (tables, task lists, etc.)
- Implement syntax highlighting for code blocks using highlight.js
- Add custom styling for markdown elements
- Test rendering with various markdown examples

## Phase 9: LLM Configuration UI

### Commit 20: LLM Configuration Data Model
```
git commit -m "Add LLM configuration data models and storage"
```
- Create LLMConfig model in models.py
- Add configuration table to SQLite database
- Implement methods to save/load LLM configurations
- Create API endpoints for retrieving/updating configurations
- Add default configuration values

### Commit 21: Settings Page Development
```
git commit -m "Develop settings page UI for LLM configuration"
```
- Create settings.html view
- Add model selection dropdown
- Implement temperature/creativity controls
- Add maximum token limit settings
- Create form validation
- Connect UI to configuration API endpoints

### Commit 22: Enhanced LLM Features with Configuration
```
git commit -m "Update LLM service to use user configurations"
```
- Modify LLMService to read from configuration
- Add customizable prompts for different analysis types
- Implement progress indicators for long-running operations
- Add option to save/favorite generated summaries
- Test with different configuration options

## Phase 10: Image Storage & Management

### Commit 23: Backend Image Storage Implementation
```
git commit -m "Add image storage functionality to backend"
```
- Extend StorageManager to handle image files
- Create images directory structure
- Add images table to database schema
- Create API endpoints for image upload/retrieval/deletion
- Implement image metadata tracking

### Commit 24: Image Upload UI
```
git commit -m "Add image upload functionality to UI"
```
- Create image upload component
- Add drag-and-drop support
- Implement file type validation
- Add progress indicator for uploads
- Create image browser component

### Commit 25: Markdown Image Integration
```
git commit -m "Integrate images with markdown editor"
```
- Add image insertion tools to markdown editor
- Implement markdown image syntax handling
- Create relative path handling for images
- Update entry display to render embedded images
- Test image functionality in various entry contexts

## Phase 11: User Experience Improvements

### Commit 26: Theme Support
```
git commit -m "Add light/dark mode and theme customization"
```
- Implement light/dark mode toggle
- Add theme preference storage
- Create custom color variables in CSS
- Add font size and type configurations
- Ensure consistent styling across themes

### Commit 27: Journal Organization
```
git commit -m "Implement journal organization features"
```
- Add folder/notebook structure for entries
- Update database schema for organizational features
- Implement favorites/pinning functionality
- Create calendar view for browsing entries by date
- Add batch operations for entries

### Commit 28: Export/Import Features
```
git commit -m "Add export and import functionality"
```
- Create entry export functionality (PDF, HTML, markdown)
- Implement backup and restore capabilities
- Add batch operations for tags
- Create import from text/markdown functionality
- Test data portability features

## Phase 12: Advanced Search Enhancements

### Commit 29: Extended Search Capabilities
```
git commit -m "Enhance search with advanced filtering and history"
```
- Add filters for entries with images
- Implement saved searches
- Create visual search history
- Add date-based search visualization
- Improve search results interface

### Commit 30: Search Analytics
```
git commit -m "Add search analytics and insights"
```
- Implement search trends visualization
- Add related entries suggestions
- Create "On This Day" feature for past entries
- Implement topic clustering for search results
- Test advanced search features with large datasets

## Phase 13: Final Refinements

### Commit 31: Performance Optimizations
```
git commit -m "Optimize performance for images and rich content"
```
- Add image compression/resizing
- Implement lazy loading for images
- Optimize markdown rendering for large documents
- Add caching for frequently accessed content
- Conduct performance testing with large datasets

### Commit 32: Comprehensive Testing
```
git commit -m "Add comprehensive tests for new features"
```
- Create tests for markdown editor functionality
- Add tests for image storage and retrieval
- Implement tests for configuration management
- Add UI tests for new features
- Update documentation with new features

### Commit 33: User Documentation Update
```
git commit -m "Update documentation with new features and guides"
```
- Update README with new features
- Create detailed usage guides for new functionality
- Add screenshot examples for new features
- Create video tutorials for complex workflows
- Update API documentation

## Implementation Considerations

### Libraries to Add
- EasyMDE (or SimpleMDE): `npm install easymde --save` or include via CDN
- marked.js: For enhanced markdown rendering
- highlight.js: For code syntax highlighting
- html2pdf.js: For PDF export functionality
- date-fns: For advanced date manipulation

### Database Updates
- Add images table with foreign key to entries
- Add configurations table for LLM settings
- Add folders/notebooks organizational structure
- Update vectors table to handle images (if implementing image search)

### Security Considerations
- Implement file type validation for uploads
- Add file size limitations for images
- Consider sanitization of markdown content
- Add CSRF protection for forms

### Testing Strategy
- Unit tests for new storage methods
- Integration tests for markdown and image functionality
- Visual regression tests for theme changes
- Performance tests for large entries with images
