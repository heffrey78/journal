from fastapi import FastAPI, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from app.models import JournalEntry
from app.storage import StorageManager

app = FastAPI(
    title="Journal API", description="API for managing journal entries", version="0.1.0"
)

# Create a singleton storage manager
storage_manager = None


def get_storage() -> StorageManager:
    """Dependency to get the storage manager instance"""
    global storage_manager
    if storage_manager is None:
        storage_manager = StorageManager()
    return storage_manager


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


@app.get("/", tags=["root"])
async def read_root():
    """Root endpoint that returns API information"""
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


@app.post("/entries/search/", response_model=List[JournalEntry], tags=["search"])
async def advanced_search(
    search_params: SearchParams, storage: StorageManager = Depends(get_storage)
):
    """
    Advanced search for journal entries by text, date range, and tags
    """
    try:
        entries = storage.text_search(
            query=search_params.query,
            date_from=search_params.date_from,
            date_to=search_params.date_to,
            tags=search_params.tags,
        )
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/entries/search/", response_model=List[JournalEntry], tags=["search"])
async def simple_search(
    query: str = Query(..., min_length=1),
    storage: StorageManager = Depends(get_storage),
):
    """Simple search for journal entries by text (GET method)"""
    try:
        entries = storage.text_search(query)
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
