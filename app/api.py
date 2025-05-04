from fastapi import FastAPI, HTTPException, Query, Depends, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List, Optional, Any
from datetime import datetime, date
from pydantic import BaseModel, Field

from app.models import JournalEntry, LLMConfig
from app.storage import StorageManager
from app.llm_service import LLMService, EntrySummary

app = FastAPI(
    title="Journal API", description="API for managing journal entries", version="0.1.0"
)

# Mount static files for UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create a singleton storage manager
storage_manager = None
llm_service = None


def get_storage() -> StorageManager:
    """Dependency to get the storage manager instance"""
    global storage_manager
    if storage_manager is None:
        storage_manager = StorageManager()
    return storage_manager


def get_llm_service() -> LLMService:
    """Dependency to get the LLM service instance"""
    global llm_service, storage_manager
    if llm_service is None:
        if storage_manager is None:
            storage_manager = StorageManager()
        llm_service = LLMService(storage_manager=storage_manager)
    return llm_service


class EntryUpdate(BaseModel):
    """Model for updating journal entries"""

    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class SearchParams(BaseModel):
    """Model for advanced search parameters"""

    query: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    tags: Optional[List[str]] = None
    semantic: bool = False  # Toggle for semantic search
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class TagCount(BaseModel):
    """Model for tag counts in stats"""

    tag: str
    count: int


class EntryStats(BaseModel):
    """Model for journal statistics"""

    total_entries: int
    oldest_entry: Optional[str] = None
    newest_entry: Optional[str] = None
    total_tags: int
    most_used_tags: List[TagCount] = []

    class Config:
        schema_extra = {
            "example": {
                "total_entries": 5,
                "oldest_entry": "2025-05-01T20:31:52",
                "newest_entry": "2025-05-02T07:58:55",
                "total_tags": 5,
                "most_used_tags": [
                    {"tag": "test", "count": 3},
                    {"tag": "api", "count": 2},
                ],
            }
        }


class ErrorResponse(BaseModel):
    """Model for structured error responses"""

    status_code: int
    message: str
    details: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Setup exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom handler for HTTP exceptions"""
    error = ErrorResponse(
        status_code=exc.status_code,
        message=str(exc.detail),
        details=getattr(exc, "details", None),
    )
    return JSONResponse(status_code=exc.status_code, content=error.dict())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors"""
    error = ErrorResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation error on request data",
        details=[{"loc": err["loc"], "msg": err["msg"]} for err in exc.errors()],
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions"""
    error = ErrorResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        details=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error.dict()
    )


@app.get("/", tags=["root"])
async def read_root():
    """Root endpoint that returns API information"""
    from fastapi.responses import FileResponse

    return FileResponse("static/home.html")


@app.get("/api/info", tags=["root"])
async def api_info():
    """API information endpoint"""
    return {
        "name": "Journal API",
        "version": "0.1.0",
        "description": "API for managing journal entries",
    }


@app.post("/entries/", response_model=JournalEntry, tags=["entries"])
async def create_entry(
    entry: JournalEntry, storage: StorageManager = Depends(get_storage)
) -> Optional[JournalEntry]:
    """Create a new journal entry"""
    try:
        entry_id = storage.save_entry(entry)
        return storage.get_entry(entry_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create entry: {str(e)}")


@app.get("/entries/", response_model=List[JournalEntry], tags=["entries"])
async def list_entries(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    tag: Optional[str] = None,
    storage: StorageManager = Depends(get_storage),
):
    """
    List journal entries with pagination and optional filtering by date range and tag
    """
    try:
        # Convert date to datetime if provided
        from_dt = (
            datetime.combine(date_from, datetime.min.time()) if date_from else None
        )
        to_dt = datetime.combine(date_to, datetime.max.time()) if date_to else None

        # If a specific tag is requested, use the tag-specific method
        if tag:
            entries = storage.get_entries_by_tag(tag, limit, offset)
        else:
            tags_filter = None
            entries = storage.get_entries(
                limit=limit,
                offset=offset,
                date_from=from_dt,
                date_to=to_dt,
                tags=tags_filter,
            )
        return entries
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve entries: {str(e)}"
        )


@app.get("/entries/{entry_id}", response_model=JournalEntry, tags=["entries"])
async def get_entry(entry_id: str, storage: StorageManager = Depends(get_storage)):
    """Get a specific journal entry by ID"""
    entry = storage.get_entry(entry_id)
    if not entry:
        raise HTTPException(
            status_code=404, detail=f"Entry with ID {entry_id} not found"
        )
    return entry


@app.patch("/entries/{entry_id}", response_model=JournalEntry, tags=["entries"])
async def update_entry(
    entry_id: str,
    update_data: EntryUpdate,
    storage: StorageManager = Depends(get_storage),
):
    """Update a journal entry"""
    try:
        updated_entry = storage.update_entry(
            entry_id, update_data.dict(exclude_unset=True)
        )
        if not updated_entry:
            raise HTTPException(
                status_code=404, detail=f"Entry with ID {entry_id} not found"
            )
        return updated_entry
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update entry: {str(e)}")


@app.delete("/entries/{entry_id}", tags=["entries"])
async def delete_entry(entry_id: str, storage: StorageManager = Depends(get_storage)):
    """Delete a journal entry by ID"""
    success = storage.delete_entry(entry_id)
    if not success:
        raise HTTPException(
            status_code=404, detail=f"Entry with ID {entry_id} not found"
        )
    return {"status": "success", "message": f"Entry {entry_id} deleted"}


@app.post("/entries/search/", tags=["search"])
async def advanced_search(
    search_params: SearchParams,
    storage: StorageManager = Depends(get_storage),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Advanced search for journal entries by text, date range, and tags.

    Set semantic=true to use semantic search powered by Ollama embeddings.
    """
    try:
        if search_params.semantic:
            # Use semantic search with LLM service with pagination
            results = llm.semantic_search(
                search_params.query,
                limit=search_params.limit,
                offset=search_params.offset,
            )

            # Results already contain the full entries
            return [result["entry"] for result in results if "entry" in result]
        else:
            # Regular text search
            entries = storage.text_search(
                query=search_params.query,
                date_from=search_params.date_from,
                date_to=search_params.date_to,
                tags=search_params.tags,
            )
            # Apply manual pagination for consistency
            # fmt: off
            return_entries = entries[
                search_params.offset: search_params.offset + search_params.limit
            ]
            # fmt: on
            # Return the paginated entries
            return return_entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/entries/search/", response_model=List[JournalEntry], tags=["search"])
async def simple_search(
    query: str = Query(..., min_length=1),
    semantic: bool = False,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    storage: StorageManager = Depends(get_storage),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Simple search for journal entries by text.

    Set semantic=true to use semantic search powered by Ollama embeddings.
    """
    try:
        if semantic:
            # Use semantic search with LLM service with pagination
            results = llm.semantic_search(query, limit=limit, offset=offset)

            # Results already contain the full entries
            return [result["entry"] for result in results if "entry" in result]
        else:
            # Regular text search
            entries = storage.text_search(query)
            # Apply manual pagination for consistency
            # fmt: off
            return_entries = entries[
                offset: offset + limit
            ]
            # fmt: on
            return return_entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/tags/", response_model=List[str], tags=["tags"])
async def get_tags(storage: StorageManager = Depends(get_storage)):
    """Get all unique tags used in the journal"""
    try:
        return storage.get_all_tags()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tags: {str(e)}")


@app.post("/entries/{entry_id}/summarize", response_model=EntrySummary, tags=["llm"])
async def summarize_entry(
    entry_id: str,
    storage: StorageManager = Depends(get_storage),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Generate a structured summary of a journal entry using LLM.

    Returns:
        An EntrySummary object containing a summary, key topics, and detected mood
    """
    try:
        # Get the entry from storage
        entry = storage.get_entry(entry_id)
        if not entry:
            raise HTTPException(
                status_code=404, detail=f"Entry with ID {entry_id} not found"
            )

        # Use the LLM service to generate the summary
        summary = llm.summarize_entry(entry.content)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate entry summary: {str(e)}"
        )


@app.get("/tags/{tag}/entries", response_model=List[JournalEntry], tags=["tags"])
async def get_entries_by_tag(
    tag: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    storage: StorageManager = Depends(get_storage),
):
    """Get entries by tag"""
    try:
        entries = storage.get_entries_by_tag(tag, limit, offset)
        return entries
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get entries by tag: {str(e)}"
        )


@app.get("/stats/", tags=["stats"])
async def get_stats(storage: StorageManager = Depends(get_storage)):
    """Get statistics about journal entries"""
    try:
        raw_stats = storage.get_stats()

        # Convert the most_used_tags from list of tuples to list of dicts
        tag_counts = [
            {"tag": tag, "count": count} for tag, count in raw_stats["most_used_tags"]
        ]

        # Construct the response with the proper structure
        stats = {
            "total_entries": raw_stats["total_entries"],
            "oldest_entry": raw_stats["oldest_entry"],
            "newest_entry": raw_stats["newest_entry"],
            "total_tags": raw_stats["total_tags"],
            "most_used_tags": tag_counts,
        }

        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


@app.get("/config/llm", response_model=LLMConfig, tags=["config"])
async def get_llm_config(storage: StorageManager = Depends(get_storage)):
    """Get LLM configuration settings"""
    try:
        config = storage.get_llm_config()
        if not config:
            # This shouldn't happen as we initialize a default config
            raise HTTPException(status_code=404, detail="LLM configuration not found")
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve LLM configuration: {str(e)}"
        )


@app.put("/config/llm", response_model=LLMConfig, tags=["config"])
async def update_llm_config(
    config: LLMConfig,
    storage: StorageManager = Depends(get_storage),
    llm: LLMService = Depends(get_llm_service),
):
    """Update LLM configuration settings"""
    try:
        # Ensure config ID is always "default" for the single-user setup
        config.id = "default"

        # Validate model names by making a minimal test call
        # This will raise an exception if the models don't exist
        try:
            # Test new model configs with minimal prompts
            import ollama

            ollama.chat(
                model=config.model_name, messages=[{"role": "user", "content": "test"}]
            )
            ollama.embeddings(model=config.embedding_model, prompt="test")
        except Exception as model_error:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model configuration. Error: {str(model_error)}",
            )

        # Save to database
        success = storage.save_llm_config(config)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to save LLM configuration"
            )

        # Reload configuration in LLM service
        llm.reload_config()

        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update LLM configuration: {str(e)}"
        )


@app.get("/config/available-models", tags=["config"])
async def get_available_models():
    """Get list of available Ollama models"""
    try:
        import ollama

        # The Ollama Python library returns a ListResponse object
        response = ollama.list()

        # Extract model names using the correct attributes
        model_names = []
        for model in response.models:
            # The model name is in the 'model' attribute, not 'name'
            model_names.append(model.model)

        return {"models": model_names}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve available models: {str(e)}"
        )
