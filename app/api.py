from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Depends,
    Request,
    status,
    UploadFile,
    File,
    Form,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from typing import List, Optional, Any, Union
from datetime import datetime, date
from pydantic import BaseModel, Field

from app.models import JournalEntry, LLMConfig
from app.storage import StorageManager
from app.llm_service import LLMService, EntrySummary
from app.organization_routes import organization_router
from app.utils import get_storage, get_llm_service  # Import from utils module

app = FastAPI(
    title="Journal API", description="API for managing journal entries", version="0.1.0"
)

# Include the organization router
app.include_router(organization_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files for UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create a singleton storage manager
storage_manager = None
llm_service = None


class EntryUpdate(BaseModel):
    """Model for updating journal entries"""

    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    folder: Optional[str] = None
    favorite: Optional[bool] = None
    images: Optional[List[str]] = None


class SearchParams(BaseModel):
    """Model for advanced search parameters"""

    query: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    tags: Optional[List[str]] = None
    folder: Optional[str] = None
    favorite: Optional[bool] = None
    semantic: bool = False  # Toggle for semantic search
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    min_similarity: Optional[float] = Field(
        None, ge=0.0, le=1.0
    )  # Optional similarity threshold for semantic search


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


class SummarizeRequest(BaseModel):
    """Model for customized summarization requests"""

    prompt_type: str = Field(
        "default",
        description="Type of prompt to use (default, detailed, creative, concise)",
    )


class ProgressResponse(BaseModel):
    """Model for progress responses"""

    progress: float = Field(..., description="Progress value between 0 and 1")
    status: str = Field(..., description="Status message")


class SemanticSearchResult(BaseModel):
    """Model for semantic search results that includes similarity score"""

    entry: JournalEntry
    similarity: float
    text: Optional[str] = None  # The text chunk that matched


class BatchUpdateRequest(BaseModel):
    """Model for batch update requests"""

    entry_ids: List[str]


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


@app.get("/entries/favorites", response_model=List[JournalEntry], tags=["organization"])
async def get_favorite_entries(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    tag: Optional[str] = None,
    storage: StorageManager = Depends(get_storage),
):
    """Get favorite entries with optional filtering"""
    try:
        # Convert date to datetime if provided
        from_dt = (
            datetime.combine(date_from, datetime.min.time()) if date_from else None
        )
        to_dt = datetime.combine(date_to, datetime.max.time()) if date_to else None

        tags_filter = [tag] if tag else None

        entries = storage.get_favorite_entries(
            limit, offset, from_dt, to_dt, tags_filter
        )
        return entries
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get favorite entries: {str(e)}"
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
    include_scores: bool = False,  # Add parameter to include similarity scores
    storage: StorageManager = Depends(get_storage),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Advanced search for journal entries by text, date range, and tags.

    Set semantic=true to use semantic search powered by Ollama embeddings.
    Set include_scores=true to include similarity scores in semantic search results.
    """
    try:
        if search_params.semantic:
            # Use semantic search with LLM service with pagination
            # and minimum similarity threshold
            results = llm.semantic_search(
                search_params.query,
                limit=search_params.limit,
                offset=search_params.offset,
                min_similarity=search_params.min_similarity,
            )

            # Format results depending on whether scores should be included
            if include_scores:
                return [
                    SemanticSearchResult(
                        entry=result["entry"],
                        similarity=result["similarity"],
                        text=result.get("text", None),
                    )
                    for result in results
                ]
            else:
                # Just return the entries for backward compatibility
                return [result["entry"] for result in results if "entry" in result]
        else:
            # Regular text search - pass all filter parameters including pagination
            entries = storage.text_search(
                query=search_params.query,
                date_from=search_params.date_from,
                date_to=search_params.date_to,
                tags=search_params.tags,
                limit=search_params.limit,
                offset=search_params.offset,
            )

            # No need for manual pagination anymore since it's handled by text_search
            return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get(
    "/entries/search/",
    response_model=List[Union[JournalEntry, SemanticSearchResult]],
    tags=["search"],
)
async def simple_search(
    query: str = Query(..., min_length=1),
    semantic: bool = False,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    min_similarity: Optional[float] = Query(
        None, ge=0.0, le=1.0
    ),  # Allow None to use config default
    include_scores: bool = Query(
        False, description="Include similarity scores in semantic search results"
    ),
    storage: StorageManager = Depends(get_storage),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Simple search for journal entries by text.

    Set semantic=true to use semantic search powered by Ollama embeddings.
    Set include_scores=true to include similarity scores in semantic search results.
    """
    try:
        if semantic:
            # Use semantic search with LLM service
            # with pagination and similarity threshold
            # If min_similarity is None, the LLMService will use the default value
            results = llm.semantic_search(
                query, limit=limit, offset=offset, min_similarity=min_similarity
            )

            # Format results depending on whether scores should be included
            if include_scores:
                return [
                    SemanticSearchResult(
                        entry=result["entry"],
                        similarity=result["similarity"],
                        text=result.get("text", None),
                    )
                    for result in results
                ]
            else:
                # Just return the entries for backward compatibility
                return [result["entry"] for result in results if "entry" in result]
        else:
            # Regular text search with proper pagination
            entries = storage.text_search(
                query=query,
                # No additional filters for simple search
                date_from=None,
                date_to=None,
                tags=None,
                # Pass pagination parameters
                limit=limit,
                offset=offset,
            )

            # No need for manual pagination anymore
            return entries
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


@app.post(
    "/entries/{entry_id}/summarize/custom", response_model=EntrySummary, tags=["llm"]
)
async def summarize_entry_custom(
    entry_id: str,
    request: SummarizeRequest,
    storage: StorageManager = Depends(get_storage),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Generate a customized summary of a journal entry using LLM with prompt type.

    Args:
        entry_id: ID of the entry to summarize
        request: Contains prompt_type parameter

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

        # Use the LLM service to generate the summary with custom prompt
        summary = llm.summarize_entry(entry.content, prompt_type=request.prompt_type)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate entry summary: {str(e)}"
        )


@app.post("/entries/{entry_id}/summaries/favorite", tags=["llm"])
async def save_favorite_summary(
    entry_id: str,
    summary: EntrySummary,
    storage: StorageManager = Depends(get_storage),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Save a generated summary as a favorite for a specific entry.

    Args:
        entry_id: ID of the journal entry
        summary: EntrySummary object to save as favorite

    Returns:
        Confirmation message
    """
    try:
        # Get the entry to verify it exists
        entry = storage.get_entry(entry_id)
        if not entry:
            raise HTTPException(
                status_code=404, detail=f"Entry with ID {entry_id} not found"
            )

        # Save the summary as a favorite
        success = llm.save_favorite_summary(entry_id, summary)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to save favorite summary"
            )

        return {"status": "success", "message": "Summary saved as favorite"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save favorite summary: {str(e)}"
        )


@app.get(
    "/entries/{entry_id}/summaries/favorite",
    response_model=List[EntrySummary],
    tags=["llm"],
)
async def get_favorite_summaries(
    entry_id: str,
    storage: StorageManager = Depends(get_storage),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Retrieve all favorite summaries for a specific journal entry.

    Args:
        entry_id: ID of the journal entry

    Returns:
        List of EntrySummary objects marked as favorites
    """
    try:
        # Get the entry to verify it exists
        entry = storage.get_entry(entry_id)
        if not entry:
            raise HTTPException(
                status_code=404, detail=f"Entry with ID {entry_id} not found"
            )

        # Get favorite summaries
        summaries = llm.get_favorite_summaries(entry_id)
        return summaries
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve favorite summaries: {str(e)}"
        )


@app.get("/prompts/available", tags=["llm"])
async def get_available_prompts(llm: LLMService = Depends(get_llm_service)):
    """
    Get list of available prompt templates for summarization.

    Returns:
        Dictionary of available prompt types and their templates
    """
    try:
        return {
            "prompt_types": list(llm.PROMPT_TEMPLATES.keys()),
            "templates": llm.PROMPT_TEMPLATES,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve available prompts: {str(e)}"
        )


@app.post("/vectors/process", tags=["llm"])
async def process_vectors(
    limit: int = Query(10, ge=1, le=100),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Process entries without embeddings to update the vector database.

    Args:
        limit: Maximum number of chunks to process

    Returns:
        Status message with number of chunks processed
    """
    try:
        # Process chunks without embeddings
        processed = llm.process_entries_without_embeddings(limit)
        return {
            "status": "success",
            "message": f"Processed {processed} chunks",
            "processed_count": processed,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process vectors: {str(e)}"
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
    skip_validation: bool = Query(False, description="Skip Ollama model validation"),
):
    """Update LLM configuration settings"""
    import traceback
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Log the input config for debugging
        logger.info(f"Updating LLM config with: {config}")

        # Ensure config ID is always "default" for the single-user setup
        config.id = "default"

        # Validate model names by making a minimal test call
        # This will raise an exception if the models don't exist
        if not skip_validation:
            try:
                # Import here to avoid issues if Ollama is not installed
                import ollama
                from concurrent.futures import ThreadPoolExecutor
                import time

                logger.info("Validating models with Ollama...")
                start_time = time.time()

                # Test connection to Ollama first with a lightweight call
                try:
                    models_list = ollama.list()
                    logger.info(
                        "Ollama connection successful, found "
                        f"{len(models_list.models)} models"
                    )

                    # Check if the specified models exist in the list
                    model_names = [model.model for model in models_list.models]
                    if config.model_name not in model_names:
                        logger.warning(f"Model {config.model_name} not found in Ollama")
                    if config.embedding_model not in model_names:
                        logger.warning(
                            f"Embedding model {config.embedding_model} "
                            "not found in Ollama"
                        )

                except Exception as conn_error:
                    logger.error(f"Failed to connect to Ollama: {conn_error}")
                    raise HTTPException(
                        status_code=503,
                        detail=f"Cannot connect to Ollama service: {str(conn_error)}",
                    )

                # Use ThreadPoolExecutor to run model validation with a timeout
                with ThreadPoolExecutor() as executor:
                    # Create validation tasks
                    chat_future = executor.submit(
                        lambda: ollama.chat(
                            model=config.model_name,
                            messages=[{"role": "user", "content": "test"}],
                        )
                    )
                    embed_future = executor.submit(
                        lambda: ollama.embeddings(
                            model=config.embedding_model, prompt="test"
                        )
                    )

                    # Wait for results with timeout
                    try:
                        # Give each model 5 seconds to respond
                        chat_future.result(timeout=5)
                        logger.info(f"Chat model {config.model_name} validated")
                    except Exception as chat_error:
                        logger.error(f"Chat model validation error: {chat_error}")
                        # Continue anyway, don't block the config update

                    try:
                        embed_future.result(timeout=5)
                        logger.info(
                            f"Embedding model {config.embedding_model} validated"
                        )
                    except Exception as embed_error:
                        logger.error(f"Embedding model validation error: {embed_error}")
                        # Continue anyway, don't block the config update

                elapsed = time.time() - start_time
                logger.info(f"Model validation completed in {elapsed:.2f} seconds")

            except Exception as model_error:
                logger.error(f"Model validation error: {str(model_error)}")
                # Don't block the config update, just log the error
                # We'll save the config anyway since the user might be
                # setting up models that will be available later
        else:
            logger.info("Skipping model validation")

        # Log the prompt types for debugging
        if config.prompt_types:
            logger.info(f"Prompt types to save: {len(config.prompt_types)}")
            for i, pt in enumerate(config.prompt_types):
                logger.info(f"Prompt type {i}: id={pt.id}, name={pt.name}")

        # Save to database
        success = storage.save_llm_config(config)
        if not success:
            logger.error("Database reported failure when saving LLM config")
            raise HTTPException(
                status_code=500, detail="Failed to save LLM configuration"
            )

        # Reload configuration in LLM service
        llm.reload_config()

        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_llm_config: {str(e)}")
        logger.error(traceback.format_exc())
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


@app.post("/images/upload", tags=["images"])
async def upload_image(
    file: UploadFile = File(...),
    entry_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    storage: StorageManager = Depends(get_storage),
):
    """
    Upload an image file and optionally associate it with a journal entry.

    Args:
        file: The image file uploaded by the user
        entry_id: Optional ID of a journal entry to associate with this image
        description: Optional text description of the image

    Returns:
        Image metadata information
    """
    try:
        # Validate that this is actually an image file
        content_type = file.content_type
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"File must be an image, got {content_type}",
            )

        # Read the file data
        file_data = await file.read()

        # Save the image using the storage manager's image storage
        image_info = storage.save_image(
            file_data=file_data,
            filename=file.filename,
            mime_type=content_type,
            entry_id=entry_id,
            description=description,
        )

        return {
            "id": image_info["id"],
            "filename": image_info["filename"],
            "mime_type": image_info["mime_type"],
            "size": image_info["size"],
            "entry_id": image_info["entry_id"],
            "description": image_info["description"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


@app.get("/images/{image_id}", tags=["images"])
async def get_image(
    image_id: str,
    storage: StorageManager = Depends(get_storage),
):
    """
    Get an image by ID and serve it.

    Args:
        image_id: The ID of the image to retrieve

    Returns:
        The image file
    """
    try:
        # Get image metadata
        image_meta = storage.get_image(image_id)
        if not image_meta:
            raise HTTPException(
                status_code=404, detail=f"Image with ID {image_id} not found"
            )

        # Return the image file
        return FileResponse(
            path=image_meta["path"],
            media_type=image_meta["mime_type"],
            filename=image_meta["filename"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve image: {str(e)}"
        )


@app.get("/images/{image_id}/info", tags=["images"])
async def get_image_info(
    image_id: str,
    storage: StorageManager = Depends(get_storage),
):
    """
    Get metadata for an image by ID.

    Args:
        image_id: The ID of the image to retrieve information for

    Returns:
        Image metadata
    """
    try:
        # Get image metadata
        image_meta = storage.get_image(image_id)
        if not image_meta:
            raise HTTPException(
                status_code=404, detail=f"Image with ID {image_id} not found"
            )

        # Return the metadata without the internal file path
        return {
            "id": image_meta["id"],
            "filename": image_meta["filename"],
            "mime_type": image_meta["mime_type"],
            "size": image_meta["size"],
            "width": image_meta["width"],
            "height": image_meta["height"],
            "entry_id": image_meta["entry_id"],
            "description": image_meta["description"],
            "created_at": image_meta["created_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve image metadata: {str(e)}"
        )


@app.get("/entries/{entry_id}/images", tags=["images", "entries"])
async def get_entry_images(
    entry_id: str,
    storage: StorageManager = Depends(get_storage),
):
    """
    Get all images associated with a journal entry.

    Args:
        entry_id: The ID of the journal entry

    Returns:
        List of image metadata
    """
    try:
        # Check if entry exists
        entry = storage.get_entry(entry_id)
        if not entry:
            raise HTTPException(
                status_code=404, detail=f"Entry with ID {entry_id} not found"
            )

        # Get images for this entry
        images = storage.get_entry_images(entry_id)

        # Return all image metadata
        return [
            {
                "id": img["id"],
                "filename": img["filename"],
                "mime_type": img["mime_type"],
                "size": img["size"],
                "width": img["width"],
                "height": img["height"],
                "description": img["description"],
                "created_at": img["created_at"],
            }
            for img in images
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve entry images: {str(e)}"
        )


@app.delete("/images/{image_id}", tags=["images"])
async def delete_image(
    image_id: str,
    storage: StorageManager = Depends(get_storage),
):
    """
    Delete an image by ID.

    Args:
        image_id: The ID of the image to delete

    Returns:
        Success status
    """
    try:
        # Delete the image
        success = storage.delete_image(image_id)
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Image with ID {image_id} not found"
            )

        return {"status": "success", "message": f"Image {image_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")


@app.patch("/images/{image_id}", tags=["images"])
async def update_image_metadata(
    image_id: str,
    description: Optional[str] = Form(None),
    entry_id: Optional[str] = Form(None),
    storage: StorageManager = Depends(get_storage),
):
    """
    Update metadata for an image.

    Args:
        image_id: The ID of the image to update
        description: New description for the image
        entry_id: New journal entry association for the image

    Returns:
        Updated image metadata
    """
    try:
        # Create updates dictionary with non-None values
        updates = {}
        if description is not None:
            updates["description"] = description
        if entry_id is not None:
            updates["entry_id"] = entry_id

        # Update the image metadata
        updated_meta = storage.update_image_metadata(image_id, updates)
        if not updated_meta:
            raise HTTPException(
                status_code=404, detail=f"Image with ID {image_id} not found"
            )

        # Return the updated metadata without the internal file path
        return {
            "id": updated_meta["id"],
            "filename": updated_meta["filename"],
            "mime_type": updated_meta["mime_type"],
            "size": updated_meta["size"],
            "width": updated_meta["width"],
            "height": updated_meta["height"],
            "entry_id": updated_meta["entry_id"],
            "description": updated_meta["description"],
            "created_at": updated_meta["created_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update image metadata: {str(e)}"
        )


@app.get("/images/", tags=["images"])
async def list_images(
    entry_id: Optional[str] = None,
    orphaned: bool = False,
    storage: StorageManager = Depends(get_storage),
):
    """
    List images with optional filtering.

    Args:
        entry_id: Optional ID of journal entry to filter images by
        orphaned: If true, return only images not associated with any entry

    Returns:
        List of image metadata
    """
    try:
        if orphaned:
            # Get orphaned images
            images = storage.get_orphaned_images()
        elif entry_id:
            # Get images for specific entry
            images = storage.get_entry_images(entry_id)
        else:
            # This would be a future feature to get all images
            # For now, we can return an empty list or implement it in storage
            # This could be paginated in the future
            raise HTTPException(
                status_code=400, detail="Must specify either entry_id or orphaned=true"
            )

        # Return image metadata
        return [
            {
                "id": img["id"],
                "filename": img["filename"],
                "mime_type": img["mime_type"],
                "size": img["size"],
                "width": img["width"],
                "height": img["height"],
                "entry_id": img.get("entry_id"),
                "description": img["description"],
                "created_at": img["created_at"],
            }
            for img in images
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list images: {str(e)}")


@app.get("/folders/", response_model=List[str], tags=["organization"])
async def get_folders(storage: StorageManager = Depends(get_storage)):
    """Get all folders used in the journal"""
    try:
        return storage.get_folders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get folders: {str(e)}")


@app.get(
    "/folders/{folder}/entries",
    response_model=List[JournalEntry],
    tags=["organization"],
)
async def get_entries_by_folder(
    folder: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    storage: StorageManager = Depends(get_storage),
):
    """Get entries in a specific folder"""
    import logging
    import traceback

    logger = logging.getLogger(__name__)

    try:
        # Log that we're accessing this endpoint
        logger.info(f"Accessing entries for folder: {folder}")

        # Convert date to datetime if provided
        from_dt = (
            datetime.combine(date_from, datetime.min.time()) if date_from else None
        )
        to_dt = datetime.combine(date_to, datetime.max.time()) if date_to else None

        # Get entries from the folder (or empty list if folder is empty)
        entries = storage.get_entries_by_folder(folder, limit, offset, from_dt, to_dt)

        # Log success
        logger.info(
            f"Successfully retrieved {len(entries)} entries from folder '{folder}'"
        )

        # Always return a list (might be empty)
        return entries
    except Exception as e:
        # Log detailed error
        logger.error(f"Error getting entries for folder '{folder}': {str(e)}")
        logger.error(traceback.format_exc())

        # Re-raise with more details
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get entries by folder: "
            f"{str(e)}\n{traceback.format_exc()}",
        )


@app.put(
    "/entries/{entry_id}/favorite", response_model=JournalEntry, tags=["organization"]
)
async def toggle_entry_favorite(
    entry_id: str,
    favorite: bool = True,
    storage: StorageManager = Depends(get_storage),
):
    """Toggle favorite status for an entry"""
    try:
        # Update the entry with the new favorite status
        updated_entry = storage.update_entry(entry_id, {"favorite": favorite})
        if not updated_entry:
            raise HTTPException(
                status_code=404, detail=f"Entry with ID {entry_id} not found"
            )
        return updated_entry
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to update favorite status: {str(e)}"
        )


@app.get("/calendar/{date}", response_model=List[JournalEntry], tags=["organization"])
async def get_entries_by_date(
    date: date,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    storage: StorageManager = Depends(get_storage),
):
    """Get entries created on a specific date (for calendar view)"""
    try:
        # Convert date to datetime for storage API
        dt = datetime.combine(date, datetime.min.time())
        entries = storage.get_entries_by_date(dt, limit, offset)
        return entries
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get entries by date: {str(e)}"
        )


@app.post("/batch/update-folder", tags=["organization"])
async def batch_update_folder(
    request: BatchUpdateRequest,
    folder: Optional[str] = Query(
        None, description="New folder value (None to remove from folders)"
    ),
    storage: StorageManager = Depends(get_storage),
):
    """Update folder for multiple entries at once"""
    try:
        updated_count = storage.batch_update_folder(request.entry_ids, folder)
        return {
            "status": "success",
            "message": f"Updated folder for {updated_count} entries",
            "updated_count": updated_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to batch update folders: {str(e)}"
        )


@app.post("/batch/favorite", tags=["organization"])
async def batch_update_favorite(
    request: BatchUpdateRequest,
    favorite: bool = Query(True, description="New favorite status"),
    storage: StorageManager = Depends(get_storage),
):
    """Set favorite status for multiple entries at once"""
    try:
        updated_count = storage.batch_toggle_favorite(request.entry_ids, favorite)
        return {
            "status": "success",
            "message": f"Updated favorite status for {updated_count} entries",
            "updated_count": updated_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to batch update favorite status: {str(e)}"
        )


@app.post("/folders/", tags=["organization"])
async def create_folder(
    folder_name: str = Query(..., description="Name of the folder to create"),
    storage: StorageManager = Depends(get_storage),
):
    """Create a new folder in the journal"""
    try:
        success = storage.create_folder(folder_name)
        if not success:
            raise HTTPException(
                status_code=400, detail="Invalid folder name or folder already exists"
            )
        return {
            "status": "success",
            "message": f"Folder '{folder_name}' created successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create folder: {str(e)}"
        )
