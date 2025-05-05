import os
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.storage.base import BaseStorage


class ImageStorage(BaseStorage):
    """Handles image storage and retrieval."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize image storage with database setup.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        super().__init__(base_dir)
        self._init_table()

    def _init_table(self):
        """Initialize images table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                entry_id TEXT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                size INTEGER NOT NULL,
                width INTEGER,
                height INTEGER,
                created_at TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (entry_id) REFERENCES entries(id)
            )
            """
        )
        # Create index for images
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_images_entry_id ON images(entry_id)"
        )
        conn.commit()
        conn.close()

    def save_image(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        entry_id: Optional[str] = None,
        description: str = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Save an image file to the filesystem and record its metadata in the database.

        Args:
            file_data: The binary image data
            filename: Original filename of the image
            mime_type: MIME type of the image (e.g., 'image/jpeg')
            entry_id: Optional ID of the journal entry this image is associated with
            description: Optional description of the image
            width: Optional width of the image in pixels
            height: Optional height of the image in pixels

        Returns:
            Dictionary with image metadata including the ID and path
        """
        # Generate a unique ID for the image
        image_id = str(uuid.uuid4())

        # Extract file extension from the original filename or mime type
        ext = os.path.splitext(filename)[1]
        if not ext:
            # If no extension in filename, try to get from mime type
            if mime_type == "image/jpeg" or mime_type == "image/jpg":
                ext = ".jpg"
            elif mime_type == "image/png":
                ext = ".png"
            elif mime_type == "image/gif":
                ext = ".gif"
            elif mime_type == "image/webp":
                ext = ".webp"
            else:
                ext = ".bin"  # Default extension if unable to determine

        # Create a sanitized filename that includes the ID to ensure uniqueness
        new_filename = f"{image_id}{ext}"
        file_path = os.path.join(self.images_dir, new_filename)

        # Save the file to disk
        with open(file_path, "wb") as f:
            f.write(file_data)

        # Calculate the file size
        file_size = len(file_data)

        # Record in database
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO images (
                    id, entry_id, filename, file_path, mime_type,
                    size, width, height, created_at, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    image_id,
                    entry_id,
                    filename,  # Original filename
                    file_path,  # System path
                    mime_type,
                    file_size,
                    width,
                    height,
                    datetime.now().isoformat(),
                    description,
                ),
            )
            conn.commit()

            # Return image metadata
            return {
                "id": image_id,
                "filename": filename,
                "path": file_path,
                "mime_type": mime_type,
                "size": file_size,
                "width": width,
                "height": height,
                "entry_id": entry_id,
                "description": description,
            }
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving image: {e}")
            # If database insertion fails, delete the file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
        finally:
            conn.close()

    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an image by its ID.

        Args:
            image_id: The ID of the image to retrieve

        Returns:
            Dictionary with image metadata if found, None otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, entry_id, filename, file_path, mime_type,
                       size, width, height, created_at, description
                FROM images
                WHERE id = ?
                """,
                (image_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            # Extract values
            (
                id,
                entry_id,
                filename,
                file_path,
                mime_type,
                size,
                width,
                height,
                created_at,
                description,
            ) = row

            # Check if file exists
            if not os.path.exists(file_path):
                logger = logging.getLogger(__name__)
                logger.error(f"Image file not found: {file_path}")
                return None

            return {
                "id": id,
                "entry_id": entry_id,
                "filename": filename,
                "path": file_path,
                "mime_type": mime_type,
                "size": size,
                "width": width,
                "height": height,
                "created_at": created_at,
                "description": description,
            }
        finally:
            conn.close()

    def get_image_data(self, image_id: str) -> Optional[bytes]:
        """
        Get the binary data for an image by its ID.

        Args:
            image_id: The ID of the image to retrieve

        Returns:
            Binary image data if found, None otherwise
        """
        image_meta = self.get_image(image_id)
        if not image_meta:
            return None

        try:
            with open(image_meta["path"], "rb") as f:
                return f.read()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error reading image file: {e}")
            return None

    def delete_image(self, image_id: str) -> bool:
        """
        Delete an image by its ID.

        Args:
            image_id: The ID of the image to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        # Get image metadata to find the file path
        image_meta = self.get_image(image_id)
        if not image_meta:
            return False

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Delete from database
            cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
            conn.commit()

            # Delete the file if it exists
            if os.path.exists(image_meta["path"]):
                os.remove(image_meta["path"])

            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error deleting image: {e}")
            return False
        finally:
            conn.close()

    def get_entry_images(self, entry_id: str) -> List[Dict[str, Any]]:
        """
        Get all images associated with a specific journal entry.

        Args:
            entry_id: The ID of the journal entry

        Returns:
            List of dictionaries with image metadata
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, filename, file_path, mime_type,
                       size, width, height, created_at, description
                FROM images
                WHERE entry_id = ?
                ORDER BY created_at ASC
                """,
                (entry_id,),
            )

            images = []
            for row in cursor.fetchall():
                (
                    id,
                    filename,
                    file_path,
                    mime_type,
                    size,
                    width,
                    height,
                    created_at,
                    description,
                ) = row

                # Only include if the file exists
                if os.path.exists(file_path):
                    images.append(
                        {
                            "id": id,
                            "filename": filename,
                            "path": file_path,
                            "mime_type": mime_type,
                            "size": size,
                            "width": width,
                            "height": height,
                            "created_at": created_at,
                            "description": description,
                        }
                    )

            return images
        finally:
            conn.close()

    def update_image_metadata(
        self, image_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update metadata for an image.

        Args:
            image_id: The ID of the image to update
            updates: Dictionary containing fields to update

        Returns:
            Updated image metadata dictionary if successful, None otherwise
        """
        # Check if image exists
        image_meta = self.get_image(image_id)
        if not image_meta:
            return None

        # Validate updatable fields
        valid_fields = {"entry_id", "description", "width", "height"}

        # Filter to only valid fields
        updates = {k: v for k, v in updates.items() if k in valid_fields}

        if not updates:
            return image_meta  # No valid updates

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Build update query dynamically
            set_parts = []
            params = []

            for field, value in updates.items():
                set_parts.append(f"{field} = ?")
                params.append(value)

            # Add image_id at the end for the WHERE clause
            params.append(image_id)

            query = f"""
                UPDATE images
                SET {', '.join(set_parts)}
                WHERE id = ?
            """

            cursor.execute(query, tuple(params))
            conn.commit()

            # Return updated metadata
            return self.get_image(image_id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating image metadata: {e}")
            return None
        finally:
            conn.close()

    def get_orphaned_images(self) -> List[Dict[str, Any]]:
        """
        Get all images that are not associated with any journal entry.

        Returns:
            List of dictionaries with image metadata
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, filename, file_path, mime_type,
                       size, width, height, created_at, description
                FROM images
                WHERE entry_id IS NULL
                ORDER BY created_at DESC
                """
            )

            images = []
            for row in cursor.fetchall():
                (
                    id,
                    filename,
                    file_path,
                    mime_type,
                    size,
                    width,
                    height,
                    created_at,
                    description,
                ) = row

                # Only include if the file exists
                if os.path.exists(file_path):
                    images.append(
                        {
                            "id": id,
                            "filename": filename,
                            "path": file_path,
                            "mime_type": mime_type,
                            "size": size,
                            "width": width,
                            "height": height,
                            "created_at": created_at,
                            "description": description,
                        }
                    )

            return images
        finally:
            conn.close()

    def assign_image_to_entry(self, image_id: str, entry_id: str) -> bool:
        """
        Associate an existing image with a journal entry.

        Args:
            image_id: The ID of the image
            entry_id: The ID of the journal entry

        Returns:
            True if successful, False otherwise
        """
        # Check if the image exists
        image_meta = self.get_image(image_id)
        if not image_meta:
            return False

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE images SET entry_id = ? WHERE id = ?", (entry_id, image_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error assigning image to entry: {e}")
            return False
        finally:
            conn.close()
