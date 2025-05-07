from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, date
from app.storage import StorageManager
from app.models import JournalEntry
from app.utils import get_storage

# Create a router for organization features
organization_router = APIRouter(prefix="/organization", tags=["organization"])

# This file contains dedicated endpoints for organization features
# We'll use /organization prefix to avoid conflicts with other routes


@organization_router.get("/favorites", response_model=List[JournalEntry])
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


@organization_router.get("/folders", response_model=List[str])
async def get_folders(storage: StorageManager = Depends(get_storage)):
    """Get all folders used in the journal"""
    try:
        return storage.get_folders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get folders: {str(e)}")


@organization_router.get("/folders/{folder}/entries", response_model=List[JournalEntry])
async def get_entries_by_folder(
    folder: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    storage: StorageManager = Depends(get_storage),
):
    """Get entries in a specific folder"""
    try:
        # Convert date to datetime if provided
        from_dt = (
            datetime.combine(date_from, datetime.min.time()) if date_from else None
        )
        to_dt = datetime.combine(date_to, datetime.max.time()) if date_to else None

        entries = storage.get_entries_by_folder(folder, limit, offset, from_dt, to_dt)
        return entries
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get entries by folder: {str(e)}"
        )


@organization_router.get("/calendar/{date}", response_model=List[JournalEntry])
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


@organization_router.put("/entries/{entry_id}/favorite", response_model=JournalEntry)
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


@organization_router.post("/batch/update-folder")
async def batch_update_folder(
    entry_ids: List[str],
    folder: Optional[str] = Query(
        None, description="New folder value (None to remove from folders)"
    ),
    storage: StorageManager = Depends(get_storage),
):
    """Update folder for multiple entries at once"""
    try:
        updated_count = storage.batch_update_folder(entry_ids, folder)
        return {
            "status": "success",
            "message": f"Updated folder for {updated_count} entries",
            "updated_count": updated_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to batch update folders: {str(e)}"
        )


@organization_router.post("/batch/favorite")
async def batch_update_favorite(
    entry_ids: List[str],
    favorite: bool = Query(True, description="New favorite status"),
    storage: StorageManager = Depends(get_storage),
):
    """Set favorite status for multiple entries at once"""
    try:
        updated_count = storage.batch_toggle_favorite(entry_ids, favorite)
        return {
            "status": "success",
            "message": f"Updated favorite status for {updated_count} entries",
            "updated_count": updated_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to batch update favorite status: {str(e)}"
        )
