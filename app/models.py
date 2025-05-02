from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class JournalEntry(BaseModel):
    """
    Represents a journal entry with metadata and content.

    Attributes:
        id: Unique identifier for the entry (defaults to timestamp-based)
        title: Title of the journal entry
        content: Main content of the journal entry in markdown format
        created_at: Timestamp when the entry was created
        updated_at: Timestamp when the entry was last updated (optional)
        tags: List of tags associated with the entry
    """

    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    tags: List[str] = []

    def update_content(self, new_content: str) -> None:
        """Updates the content and sets updated_at timestamp"""
        self.content = new_content
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Add a tag if it doesn't already exist"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag if it exists, returns True if successful"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
            return True
        return False

    class Config:
        """Pydantic config options"""

        json_schema_extra = {
            "example": {
                "title": "My first journal entry",
                "content": (
                    "# Today's Thoughts\n\n"
                    "This is my first journal entry. It was a good day."
                ),
                "tags": ["daily", "thoughts"],
            }
        }
