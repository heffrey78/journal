from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any


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
        folder: Path for organizing entries into folders/notebooks
        favorite: Boolean indicating whether entry is marked as favorite
        images: List of image IDs associated with this entry
    """

    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    tags: List[str] = []
    folder: Optional[str] = None
    favorite: bool = False
    images: List[str] = []

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

    def toggle_favorite(self) -> None:
        """Toggle favorite status and update timestamp"""
        self.favorite = not self.favorite
        self.updated_at = datetime.now()

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
                "folder": "personal/thoughts",
                "favorite": False,
            }
        }


class PromptType(BaseModel):
    """
    Represents an analysis prompt type for journal entries.

    Attributes:
        id: Unique identifier for the prompt type
        name: Display name for the prompt type
        prompt: The actual prompt template to use
    """

    id: str
    name: str
    prompt: str


class LLMConfig(BaseModel):
    """
    Configuration settings for LLM service.

    Attributes:
        id: Unique identifier (always "default" for single-user setup)
        model_name: Ollama model to use for text generation
        embedding_model: Ollama model to use for embeddings
        max_retries: Maximum number of retries for Ollama API calls
        retry_delay: Delay between retries in seconds
        temperature: Controls randomness in generation (0-1)
        max_tokens: Maximum tokens to generate in responses
        system_prompt: Optional system prompt for chat completions
        min_similarity: Minimum similarity threshold for semantic search (0-1)
        prompt_types: List of available prompt types for entry analysis
    """

    id: str = "default"
    model_name: str = "qwen3:latest"
    embedding_model: str = "nomic-embed-text:latest"
    max_retries: int = 2
    retry_delay: float = 1.0
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: Optional[str] = None
    min_similarity: float = 0.5  # Default to 0.5 for more relevant results
    prompt_types: List[PromptType] = [
        PromptType(
            id="default",
            name="Default Summary",
            prompt="Summarize this journal entry. Extract key topics and mood. "
            "Return as JSON:",
        ),
        PromptType(
            id="detailed",
            name="Detailed Analysis",
            prompt="Provide a detailed analysis of this journal entry. "
            "Identify key themes, emotional states, and important insights. "
            "Extract key topics and mood. Return as JSON:",
        ),
        PromptType(
            id="creative",
            name="Creative Insights",
            prompt="Read this journal entry and create an insightful, "
            "reflective summary that captures the essence of the writing. "
            "Extract key topics and mood. Return as JSON:",
        ),
        PromptType(
            id="concise",
            name="Concise Summary",
            prompt="Create a very brief summary of this journal "
            "entry in 2-3 sentences. Extract key topics and mood. Return as JSON:",
        ),
    ]

    class Config:
        """Pydantic config options"""

        json_schema_extra = {
            "example": {
                "model_name": "qwen3:latest",
                "embedding_model": "nomic-embed-text:latest",
                "max_retries": 2,
                "retry_delay": 1.0,
                "temperature": 0.7,
                "max_tokens": 1000,
                "system_prompt": "You are a helpful journaling assistant.",
                "min_similarity": 0.5,
                "prompt_types": [
                    {
                        "id": "default",
                        "name": "Default Summary",
                        "prompt": "Summarize this journal entry. "
                        "Extract key topics and mood. Return as JSON:",
                    }
                ],
            }
        }


class BatchAnalysisRequest(BaseModel):
    """
    Request model for batch analysis of multiple journal entries.

    Attributes:
        entry_ids: List of entry IDs to analyze
        title: Optional title for the batch analysis
        prompt_type: Type of analysis to perform (weekly, monthly, topic, etc.)
    """

    entry_ids: List[str]
    title: Optional[str] = None
    prompt_type: str = "weekly"


class BatchAnalysis(BaseModel):
    """
    Model for batch analysis of multiple journal entries.

    Attributes:
        id: Unique identifier for the batch analysis
        title: Title for the batch analysis
        entry_ids: List of entry IDs included in the analysis
        date_range: Optional string representing the date range of included entries
        created_at: Timestamp when the analysis was created
        summary: Main summary text of the batch analysis
        key_themes: List of key themes identified across entries
        mood_trends: Dictionary mapping mood categories to their frequency
        notable_insights: List of notable insights extracted from entries
        prompt_type: Type of analysis that was performed
    """

    id: str = Field(
        default_factory=lambda: f"ba-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    title: str
    entry_ids: List[str]
    date_range: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    summary: str
    key_themes: List[str]
    mood_trends: Dict[str, int]
    notable_insights: List[str]
    prompt_type: Optional[str] = None

    class Config:
        """Pydantic config options"""

        json_schema_extra = {
            "example": {
                "title": "Weekly Analysis: May 1-7, 2025",
                "entry_ids": ["20250501121957", "20250503110841", "20250507121957"],
                "date_range": "2025-05-01 to 2025-05-07",
                "summary": "This week focused on the journal app development "
                "with significant progress on batch operations.",
                "key_themes": ["coding", "productivity", "planning"],
                "mood_trends": {"focused": 2, "creative": 1, "determined": 3},
                "notable_insights": [
                    "Breaking work into small commits improves progress tracking",
                    "Regular journaling helps organize thoughts",
                ],
                "prompt_type": "weekly",
            }
        }


class ChatSession(BaseModel):
    """
    Represents a chat session with metadata.

    Attributes:
        id: Unique identifier for the chat session
        title: Optional title for the chat session (auto-generated if not provided)
        created_at: Timestamp when the session was created
        updated_at: Timestamp when the session was last updated
        last_accessed: Timestamp when the session was last accessed
        context_summary: Optional summary of earlier conversation for context windowing
        temporal_filter: Optional temporal filter applied to this session
        entry_count: Number of unique entries referenced in this session
    """

    id: str = Field(
        default_factory=lambda: f"chat-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    context_summary: Optional[str] = None
    temporal_filter: Optional[str] = None
    entry_count: int = 0

    class Config:
        """Pydantic config options"""

        json_schema_extra = {
            "example": {
                "id": "chat-20250509123456",
                "title": "Reflection on recent coding progress",
                "created_at": "2025-05-09T12:34:56",
                "updated_at": "2025-05-09T12:45:30",
                "last_accessed": "2025-05-09T12:45:30",
                "context_summary": "Discussion about journal app development progress",
                "temporal_filter": "past_week",
                "entry_count": 3,
            }
        }


class ChatMessage(BaseModel):
    """
    Represents a message in a chat session.

    Attributes:
        id: Unique identifier for the message
        session_id: ID of the parent chat session
        role: Role of the message sender ('user' or 'assistant')
        content: Text content of the message
        created_at: Timestamp when the message was created
        metadata: Optional metadata for the message (citations, tokens, etc.)
        token_count: Optional count of tokens in the message
    """

    id: str = Field(
        default_factory=lambda: f"msg-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    )
    session_id: str
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    token_count: Optional[int] = None

    class Config:
        """Pydantic config options"""

        json_schema_extra = {
            "example": {
                "id": "msg-20250509123456789",
                "session_id": "chat-20250509123456",
                "role": "user",
                "content": "What did I write about coding yesterday?",
                "created_at": "2025-05-09T12:34:56",
                "metadata": {"intent": "temporal_query"},
                "token_count": 8,
            }
        }


class EntryReference(BaseModel):
    """
    Represents a reference to a journal entry from a chat message.

    Attributes:
        message_id: ID of the message referencing the entry
        entry_id: ID of the referenced entry
        similarity_score: Similarity score between query and entry
        chunk_index: Index of the chunk within the entry (if chunking is used)
        entry_title: Title of the referenced entry (for display purposes)
        entry_snippet: Short snippet of the entry content
    """

    message_id: str
    entry_id: str
    similarity_score: float
    chunk_index: Optional[int] = None
    entry_title: Optional[str] = None
    entry_snippet: Optional[str] = None

    class Config:
        """Pydantic config options"""

        json_schema_extra = {
            "example": {
                "message_id": "msg-20250509123456789",
                "entry_id": "20250508223326",
                "similarity_score": 0.85,
                "chunk_index": 2,
                "entry_title": "Making progress on the journal app",
                "entry_snippet": "Today I implemented the chat feature with "
                "streaming responses...",
            }
        }


class ChatConfig(BaseModel):
    """
    Configuration settings for the chat feature.

    Attributes:
        id: Unique identifier (always "default" for single-user setup)
        system_prompt: System prompt for chat completions
        max_context_tokens: Maximum tokens to include in context window
        temperature: Controls randomness in generation (0-1)
        retrieval_limit: Maximum number of entries to retrieve for context
        chunk_size: Size of chunks for entry splitting
        conversation_summary_threshold: Token threshold for summarizing conversation
    """

    id: str = "default"
    system_prompt: str = "You are a helpful assistant that helps users explore their "
    "journal entries. Always cite specific entries when making claims about the "
    "user's experiences."
    max_context_tokens: int = 4096
    temperature: float = 0.7
    retrieval_limit: int = 10
    chunk_size: int = 500
    conversation_summary_threshold: int = 2000

    temporal_prompts: Dict[str, str] = {
        "recent": "focusing on the user's most recent journal entries "
        "from the past week",
        "last_week": "looking at entries from last week",
        "last_month": "reviewing entries from the past month",
        "specific_date": "examining entries from {date}",
    }

    class Config:
        """Pydantic config options"""

        json_schema_extra = {
            "example": {
                "id": "default",
                "system_prompt": "You are a helpful assistant that helps users "
                "explore their journal entries...",
                "max_context_tokens": 4096,
                "temperature": 0.7,
                "retrieval_limit": 10,
                "chunk_size": 500,
                "conversation_summary_threshold": 2000,
            }
        }


class ChatResponse(BaseModel):
    """
    Response model for streaming chat responses.

    Attributes:
        type: Type of response ('chunk', 'complete', 'error')
        content: Text content of the response chunk
        citations: List of entry references (only for 'complete' type)
        full_response: Complete response text (only for 'complete' type)
        error: Error message (only for 'error' type)
    """

    type: str
    content: Optional[str] = None
    citations: Optional[List[EntryReference]] = None
    full_response: Optional[str] = None
    error: Optional[str] = None

    class Config:
        """Pydantic config options"""

        json_schema_extra = {
            "example": {
                "type": "chunk",
                "content": "Based on your journal entry from yesterday...",
            }
        }
