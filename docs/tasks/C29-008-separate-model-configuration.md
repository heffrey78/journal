# C29-008: Separate Model Configuration for Different Operations

## Priority: Medium
## Status: Pending
## Estimated Effort: 2-3 hours

## User Story
**As a** journal application administrator
**I want** to configure different models for search, chat, and analysis operations
**So that** I can optimize each function with the most appropriate model for performance and accuracy

## Problem Description
Currently, the journal application uses a single model configuration (`model_name` in `LLMConfig`) for all operations including semantic search, chat interactions, and batch analysis. Different operations may benefit from different models - for example, a lightweight model for search operations and a more capable model for complex analysis or chat interactions.

## Acceptance Criteria
- [ ] Extend `LLMConfig` model to support separate model configurations
- [ ] Add configuration fields for:
  - [ ] Search model (for semantic search operations)
  - [ ] Chat model (for chat completions and conversations)
  - [ ] Analysis model (for entry summarization and batch analysis)
- [ ] Update `LLMService` to use appropriate model for each operation type
- [ ] Modify chat service to use chat-specific model
- [ ] Update analysis operations to use analysis-specific model
- [ ] Add backward compatibility to fall back to `model_name` if specific models aren't configured
- [ ] Update configuration UI to support the new model options
- [ ] Add validation to ensure configured models are available in Ollama

## Technical Details
- **Components**: LLM configuration, LLMService, ChatService, API endpoints
- **Files to modify**:
  - `app/models.py` (LLMConfig class)
  - `app/llm_service.py` (model selection logic)
  - `app/chat_service.py` (use chat model)
  - Configuration UI components
- **Database changes**: Update LLM config storage to accommodate new fields
- **API changes**: Enhanced configuration endpoints

## Implementation Plan

### Phase 1: Model Configuration Extension
1. **Update LLMConfig Model**
   ```python
   class LLMConfig(BaseModel):
       # Existing fields...
       model_name: str = "qwen3:latest"  # Default/fallback model

       # New specialized model fields
       search_model: Optional[str] = None  # For semantic search
       chat_model: Optional[str] = None    # For chat completions
       analysis_model: Optional[str] = None # For summaries and batch analysis
   ```

2. **Add Model Selection Logic**
   - Helper method in `LLMService` to determine which model to use for each operation
   - Fallback to `model_name` if specialized model not configured

### Phase 2: Service Layer Updates
1. **Update LLMService Methods**
   - `semantic_search()` - use search model
   - `chat_completion()` - use chat model
   - `summarize_entry()` - use analysis model
   - `analyze_entries_batch()` - use analysis model

2. **Update ChatService**
   - Ensure chat operations use the chat model configuration

### Phase 3: Configuration Management
1. **Update Storage Layer**
   - Modify LLM config storage to handle new fields
   - Database migration if needed

2. **Update Configuration UI**
   - Add model selection dropdowns for each operation type
   - Show available models from Ollama
   - Validation and testing for each configured model

### Phase 4: Validation and Testing
1. **Model Availability Validation**
   - Check that configured models exist in Ollama
   - Graceful fallback handling

2. **Testing**
   - Unit tests for model selection logic
   - Integration tests for each operation type
   - Performance testing with different model combinations

## Definition of Done
- LLM configuration supports separate models for search, chat, and analysis
- Each operation type uses its configured model or falls back appropriately
- Configuration UI allows selection of different models for different operations
- Model availability is validated before saving configuration
- All existing functionality continues to work with enhanced model flexibility
- Performance benefits are measurable when using optimized models for specific operations

## Notes
- Consider model performance characteristics:
  - **Search models**: Fast, good for semantic understanding (e.g., smaller embedding models)
  - **Chat models**: Conversational, good reasoning (e.g., general-purpose models)
  - **Analysis models**: Detailed analysis, structured output (e.g., larger, more capable models)
- Ensure backward compatibility with existing single-model configurations
- Document recommended model combinations for different use cases
