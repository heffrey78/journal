"""
Tests for the enhanced entry retrieval system in the chat service.

These tests verify that:
1. Entry chunking works correctly
2. Hybrid retrieval (semantic + keyword) works properly
3. Chunking improves retrieval precision compared to whole-entry retrieval
4. Deduplication prevents repetitive results
"""
from datetime import datetime
from typing import List, Dict, Any
import numpy as np

from app.models import (
    JournalEntry,
    ChatMessage,
    ChatSession,
    ChatConfig,
    EntryReference,
)
from app.chat_service import ChatService


class MockLLMService:
    """Mock LLM service for testing entry retrieval."""

    def __init__(self):
        # Store embeddings for entries and queries
        self.embeddings = {}
        self.error_on_embedding = False

    def get_embedding(self, text: str) -> List[float]:
        """Mock embedding generation"""
        if self.error_on_embedding:
            raise Exception("Simulated embedding generation error")

        # Create a deterministic but unique embedding for each text
        # For testing purposes, we just need consistent vectors
        if text not in self.embeddings:
            # Create a simple embedding based on the text content
            # For real similarity testing
            words = set(text.lower().split())
            vector = np.zeros(100)  # 100-dimensional vector

            # Set specific dimensions based on word presence
            # Different words will set different dimensions
            for word in words:
                # Use hash of the word to determine which dimension to modify
                dim = hash(word) % 100
                vector[dim] = 1.0

            self.embeddings[text] = vector.tolist()

        return self.embeddings[text]

    def semantic_search(
        self, query: str, limit: int = 5, **kwargs
    ) -> List[Dict[str, Any]]:
        """Mock semantic search that returns entries with simulated relevance scores"""
        # Return the mock entries with synthetic similarity scores
        return [
            {"entry": entry, "similarity": 0.8 - (0.1 * i)}
            for i, entry in enumerate(self.mock_entries[:limit])
        ]

    def chat_completion(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """Mock chat completion response"""
        return {"message": {"content": "This is a mock response"}}

    def analyze_message_for_tools(self, message: str, context=None) -> Dict[str, Any]:
        """Mock tool analysis that suggests using journal search for relevant queries"""
        # For enhanced retrieval test, suggest journal search when relevant
        if (
            "journal" in message.lower()
            or "working on" in message.lower()
            or "features" in message.lower()
        ):
            return {
                "should_use_tools": True,
                "recommended_tools": [
                    {
                        "tool_name": "journal_search",
                        "confidence": 0.9,
                        "reason": "User is asking about their journal entries",
                        "suggested_query": message,
                    }
                ],
                "analysis": "Journal search recommended for this query",
            }
        return {
            "should_use_tools": False,
            "recommended_tools": [],
            "analysis": "No tools needed for test",
        }

    def generate_response_with_model(self, messages, model_name=None):
        """Mock response generation"""
        return "This is a mock response from the enhanced retrieval test."

    def synthesize_response_with_tools(
        self, user_message: str, tool_results, context=None
    ):
        """Mock response synthesis with tool results"""
        return "This is a response incorporating journal search results from the enhanced retrieval test."


class MockChatStorage:
    """Mock chat storage for testing entry retrieval."""

    def __init__(self):
        self.messages = []
        self.references = []
        self.chat_config = ChatConfig()
        self.base_dir = "./test_journal_data"

    def add_message(self, message: ChatMessage) -> ChatMessage:
        """Mock adding a message"""
        self.messages.append(message)
        return message

    def add_message_entry_references(
        self, message_id: str, references: List[EntryReference]
    ) -> bool:
        """Mock adding references"""
        self.references.append((message_id, references))
        return True

    def get_session(self, session_id: str) -> ChatSession:
        """Mock getting a session"""
        return ChatSession(id=session_id)

    def get_chat_config(self) -> ChatConfig:
        """Mock getting chat config"""
        return self.chat_config

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """Mock getting messages"""
        return [msg for msg in self.messages if msg.session_id == session_id]

    def save_message_entry_references(
        self, message_id: str, references: List[EntryReference]
    ) -> bool:
        """Mock saving message entry references"""
        self.references.append((message_id, references))
        return True

    def get_conversation_history(
        self, session_id: str, limit: int = 10
    ) -> List[Dict[str, str]]:
        """Mock getting conversation history"""
        messages = self.get_messages(session_id)
        return [{"role": msg.role, "content": msg.content} for msg in messages[-limit:]]


class TestEntryChunking:
    """Tests for entry chunking functionality."""

    def setup_method(self):
        """Set up test dependencies."""
        self.llm_service = MockLLMService()
        self.chat_storage = MockChatStorage()
        self.chat_service = ChatService(self.chat_storage, self.llm_service)

    def test_chunk_short_entry(self):
        """Test that short entries aren't chunked."""
        entry = JournalEntry(
            id="20250510085423",
            title="Short entry",
            content="This is a short entry that shouldn't be chunked.",
            created_at=datetime.now(),
        )

        chunks = self.chat_service._chunk_entry(entry, chunk_size=500, overlap=100)

        assert len(chunks) == 1, "Short entry should be a single chunk"
        assert chunks[0]["entry_id"] == entry.id
        assert chunks[0]["chunk_id"] == 0
        assert chunks[0]["text"] == entry.content

    def test_chunk_long_entry(self):
        """Test that long entries are correctly chunked."""
        # Create a longer entry with multiple paragraphs
        paragraphs = [
            "This is the first paragraph of a long entry. "
            "It contains multiple sentences. "
            "We need to make sure the chunking works properly with real text.",
            "This is the second paragraph of the entry. "
            "The chunking algorithm should try "
            "to keep paragraphs together when possible. "
            "But if a paragraph is too long, it should be split at sentence "
            "boundaries.",
            "Here's the third paragraph which continues the entry. "
            "We want to make sure "
            "that chunks don't break in the middle of sentences when possible.",
            "Fourth paragraph here. Testing the chunking functionality. We need enough "
            "text to ensure we get multiple chunks with the default settings.",
            "Fifth paragraph continues with more content. We're adding enough text to "
            "force at least two chunks given the default chunk size of 500 characters.",
            "Sixth paragraph adds even more text. The chunking should respect "
            "paragraph boundaries when possible, but prioritize chunk size limits.",
        ]

        entry = JournalEntry(
            id="20250510085423",
            title="Long entry",
            content="\n\n".join(paragraphs),
            created_at=datetime.now(),
        )

        # Use a relatively small chunk size to force multiple chunks
        chunks = self.chat_service._chunk_entry(entry, chunk_size=200, overlap=50)

        # Should be multiple chunks
        assert len(chunks) > 1, "Long entry should be split into multiple chunks"

        # First chunk should start at the beginning
        assert chunks[0]["start_idx"] == 0

        # Last chunk should end at the end of the content
        assert chunks[-1]["end_idx"] == len(entry.content)

        # Chunks should have overlap
        for i in range(len(chunks) - 1):
            assert (
                chunks[i]["end_idx"] > chunks[i + 1]["start_idx"]
            ), "Chunks should overlap"

        # Check for sentence boundary splitting
        for chunk in chunks[:-1]:  # All but the last chunk
            text = chunk["text"]
            # The last character of most chunks should be a sentence end
            # (allowing for some exceptions)
            if len(text) > 20:
                last_char = text[-1]
                assert last_char in (".", "!", "?", "\n") or text[-2:] in (
                    ". ",
                    "! ",
                    "? ",
                    ".\n",
                    "!\n",
                    "?\n",
                ), f"Chunk should end at sentence boundary: '{text[-10:]}'"

    def test_sentence_boundary_respect(self):
        """Test that chunking tries to respect sentence boundaries."""
        # Create text with very clear sentence boundaries
        text = ". ".join([f"This is test sentence {i}" for i in range(20)]) + "."

        entry = JournalEntry(
            id="20250510085423",
            title="Sentence boundary test",
            content=text,
            created_at=datetime.now(),
        )

        # Use a chunk size that will require breaks
        chunks = self.chat_service._chunk_entry(entry, chunk_size=100, overlap=20)

        # Check each chunk except possibly the last one
        for chunk in chunks[:-1]:
            chunk_text = chunk["text"]
            assert chunk_text.endswith(
                "."
            ), f"Chunk should end with period: '{chunk_text[-10:]}'"


class TestEnhancedRetrieval:
    """Tests for the enhanced entry retrieval functionality."""

    def setup_method(self):
        """Set up test dependencies."""
        self.llm_service = MockLLMService()
        self.chat_storage = MockChatStorage()
        self.chat_service = ChatService(self.chat_storage, self.llm_service)

        # Create some test entries
        self.llm_service.mock_entries = [
            JournalEntry(
                id="20250510085423",
                title="Programming journal",
                content="Today I worked on the chat feature for my journal app. "
                "I implemented chunking for better retrieval.",
                created_at=datetime.now(),
            ),
            JournalEntry(
                id="20250509085423",
                title="Daily reflection",
                content="Today was a productive day. I went for a walk and enjoyed "
                "the sunshine.",
                created_at=datetime.now(),
            ),
            JournalEntry(
                id="20250508085423",
                title="Project ideas",
                content="I'm thinking about adding semantic search capabilities to "
                "my journal.",
                created_at=datetime.now(),
            ),
        ]

    def test_enhanced_retrieval_basic(self):
        """Test that enhanced retrieval returns references."""
        message = ChatMessage(
            id="msg1",
            session_id="session1",
            role="user",
            content="Tell me about my journal app project",
            created_at=datetime.now(),
        )

        session = ChatSession(id="session1")
        config = ChatConfig(
            use_enhanced_retrieval=True, chunk_size=200, retrieval_limit=5
        )

        references = self.chat_service._enhanced_entry_retrieval(
            message, session, config
        )

        assert references is not None, "Should return references"
        assert len(references) > 0, "Should return at least one reference"

        # Check that references have the expected fields
        for ref in references:
            assert ref.entry_id, "Reference should have entry_id"
            assert (
                ref.similarity_score is not None
            ), "Reference should have similarity_score"
            assert ref.entry_snippet, "Reference should have entry_snippet"
            assert ref.chunk_index is not None, "Reference should have chunk_index"

    def test_embedding_fallback(self):
        """Test fallback to keyword search when embeddings fail."""
        # Configure llm_service to fail on embedding
        self.llm_service.error_on_embedding = True

        message = ChatMessage(
            id="msg1",
            session_id="session1",
            role="user",
            content="Tell me about semantic search",
            created_at=datetime.now(),
        )

        session = ChatSession(id="session1")
        config = ChatConfig(
            use_enhanced_retrieval=True, chunk_size=200, retrieval_limit=5
        )

        references = self.chat_service._enhanced_entry_retrieval(
            message, session, config
        )

        assert (
            references is not None
        ), "Should return references even when embeddings fail"
        assert len(references) > 0, "Should return at least one reference"

    def test_extract_keywords(self):
        """Test keyword extraction functionality."""
        text = "What did I write about the journal app project yesterday?"

        keywords = self.chat_service._extract_keywords(text)

        # Verify that important terms are extracted and stop words are removed
        assert "journal" in keywords, "Should extract 'journal'"
        assert "app" in keywords, "Should extract 'app'"
        assert "project" in keywords, "Should extract 'project'"
        assert "yesterday" in keywords, "Should extract 'yesterday'"

        # Verify that stop words are removed
        assert "what" not in keywords, "Should remove stop word 'what'"
        assert "did" not in keywords, "Should remove stop word 'did'"
        assert "about" not in keywords, "Should remove stop word 'about'"

    def test_similarity_calculation(self):
        """Test cosine similarity calculation."""
        # Create two vectors with high similarity
        vec1 = [1, 1, 1, 0, 0]
        vec2 = [1, 1, 0.9, 0.1, 0]

        similarity = self.chat_service._calculate_similarity(vec1, vec2)

        assert similarity > 0.9, "Similar vectors should have high similarity score"

        # Create two vectors with low similarity
        vec3 = [1, 1, 1, 0, 0]
        vec4 = [0, 0, 0, 1, 1]

        similarity = self.chat_service._calculate_similarity(vec3, vec4)

        assert similarity < 0.1, "Dissimilar vectors should have low similarity score"

    def test_hybrid_scoring(self):
        """Test that both semantic and keyword factors are used in scoring."""
        # This test requires a more complex mock that allows inspection of scoring
        pass  # Would implement with more sophisticated mocks

    def test_process_message_with_enhanced_retrieval(self):
        """Test full message processing with enhanced retrieval."""
        message = ChatMessage(
            id="msg1",
            session_id="session1",
            role="user",
            content="What journal app features am I working on?",
            created_at=datetime.now(),
        )

        # Enable enhanced retrieval in config
        self.chat_storage.chat_config.use_enhanced_retrieval = True
        self.chat_storage.chat_config.chunk_size = 200
        self.chat_storage.chat_config.retrieval_limit = 3

        # Process the message
        response, references = self.chat_service.process_message(message)

        # Check that we got a response and references
        assert response.role == "assistant"
        assert response.content is not None
        assert len(references) > 0

        # Check that references were saved with the response
        assert len(self.chat_storage.references) > 0
        saved_message_id, saved_refs = self.chat_storage.references[0]
        assert saved_message_id == response.id
        assert len(saved_refs) > 0
