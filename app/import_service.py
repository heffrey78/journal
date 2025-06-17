"""
Service for handling document imports for journal entries.

This module provides functionality to:
1. Process different document types (text, markdown, etc.)
2. Create journal entries from imported documents
3. Track import status and failures
"""

import os
import logging
from typing import List, Tuple, Optional
from datetime import datetime
import re
import chardet

from app.models import JournalEntry
from app.storage import StorageManager

logger = logging.getLogger(__name__)


class ImportService:
    """Service for handling document imports"""

    def __init__(self, storage_manager: StorageManager):
        """Initialize with storage manager"""
        self.storage = storage_manager

    def process_file(
        self,
        file_data: bytes,
        filename: str,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        file_date: Optional[datetime] = None,
        custom_title: Optional[str] = None,
        is_multi_file_import: bool = False,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Process an individual file and create a journal entry.

        Args:
            file_data: The binary content of the file
            filename: The name of the file
            tags: List of tags to apply to the entry
            folder: Optional folder path to store the entry in
            file_date: Optional creation date of the file
            custom_title: Custom title to use for the entry
            is_multi_file_import: Whether this file is part of a multi-file import

        Returns:
            Tuple of (success, entry_id, error_message)
        """
        try:
            # Handle "None" string
            if folder == "None":
                folder = None

            # Detect encoding
            encoding_result = chardet.detect(file_data)
            encoding = encoding_result.get("encoding", "utf-8")

            # Handle cases where encoding is None or not detected
            if encoding is None:
                encoding = "utf-8"

            # Default to treating as plain text
            content = file_data.decode(encoding)

            # Determine title based on provided custom title or extracted from content
            if custom_title:
                if is_multi_file_import and file_date:
                    # Format: "{Title} - {YYYY}/{MM}/{DD}" for multi-file import
                    title = f"{custom_title} - {file_date.strftime('%Y/%m/%d')}"
                else:
                    title = custom_title
            else:
                # Extract title from filename or first line
                title = self._extract_title(content, filename)

            content = self._clean_content(content, title)

            # Create the journal entry
            entry = JournalEntry(
                title=title,
                content=content,
                tags=tags or [],
                folder=folder,
                created_at=file_date or datetime.now(),
            )

            # Add debug logging
            logger.info(
                f"Saving entry with title: {title}, created_at: {entry.created_at}"
            )

            # Save to storage
            entry_id = self.storage.save_entry(entry)

            # Log successful save
            logger.info(f"Successfully saved entry with ID: {entry_id}")

            return True, entry_id, None

        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            return False, None, str(e)

    def _extract_title(self, content: str, filename: str) -> str:
        """Extract title from content or fallback to filename"""
        # Try to find a markdown heading or first line
        heading_match = re.search(r"^#\s+(.*?)$", content, re.MULTILINE)

        if heading_match:
            return heading_match.group(1).strip()

        lines = content.split("\n")
        for line in lines:
            line_text = line.strip()
            if line_text:
                # Skip lines that look like wiki-style links or other markup
                if re.match(r"^\[\[.*\]\]$", line_text):
                    continue

                # If line is too long, truncate it
                if len(line_text) > 60:
                    return line_text[:57] + "..."
                return line_text

        # Fallback to filename without extension
        base_name = os.path.splitext(os.path.basename(filename))[0]
        # Convert snake_case or kebab-case to Title Case
        title = " ".join(word.capitalize() for word in re.split(r"[_\-]", base_name))
        return title

    def _clean_content(self, content: str, title: str) -> str:
        """
        Clean up content, possibly removing the title if it's the first line
        """
        lines = content.split("\n")

        # If first line is the title, remove it
        if lines and lines[0].strip() == title:
            return "\n".join(lines[1:]).strip()

        # If first line is a markdown heading and matches the title
        if lines and lines[0].startswith("# ") and lines[0][2:].strip() == title:
            return "\n".join(lines[1:]).strip()

        return content
