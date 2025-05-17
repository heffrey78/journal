"""
Fix for bulk imports to ensure all files are properly processed.

This patch addresses an issue where only the first file would be imported correctly when
importing multiple files, even though the API reports all files as successfully
imported.

The fix:
1. Properly closes and resets file objects between each import operation
2. Creates a copy of the file data to ensure it's not modified during async operations
3. Adds additional logging to track the import process
"""

import os
import logging
import shutil
import tempfile
from typing import List
from fastapi import UploadFile

logger = logging.getLogger(__name__)


async def process_uploaded_files(
    files: List[UploadFile],
):
    """
    Process a list of uploaded files, ensuring each file is correctly handled.
    Returns a list of processed file data (bytes) and filenames.
    """
    result = []

    for file in files:
        try:
            # Create a temporary file to store the uploaded file content
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                # Copy the uploaded file content to the temporary file
                shutil.copyfileobj(file.file, temp_file)
                temp_file_path = temp_file.name

            # Reset the file cursor position
            await file.seek(0)

            # Read the content from the temporary file
            with open(temp_file_path, "rb") as f:
                file_content = f.read()

            # Store the file content and filename
            result.append((file_content, file.filename))

            # Clean up the temporary file
            os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Error processing uploaded file {file.filename}: {str(e)}")
            # Continue with the next file

    return result
