"""
Chat service for handling LLM interactions and message processing.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple

from app.models import (
    ChatMessage,
    ChatSession,
    EntryReference,
    ChatConfig,
    JournalEntry,
)
from app.storage.chat import ChatStorage
from app.llm_service import LLMService

# Configure logging
logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for generating chat responses using the LLM service.

    This class is responsible for:
    1. Processing user messages
    2. Finding relevant journal entries for context
    3. Generating LLM responses
    4. Tracking citations to journal entries
    """

    def __init__(self, chat_storage: ChatStorage, llm_service: LLMService):
        """
        Initialize the chat service.

        Args:
            chat_storage: Storage manager for chat data
            llm_service: LLM service for generating responses
        """
        self.chat_storage = chat_storage
        self.llm_service = llm_service

    def process_message(
        self, message: ChatMessage
    ) -> Tuple[ChatMessage, List[EntryReference]]:
        """
        Process a user message and generate a response.

        This function:
        1. Retrieves relevant entries based on message content
        2. Constructs context from conversation history
        3. Generates a response using the LLM
        4. Saves the response and references

        Args:
            message: The user message to process

        Returns:
            Tuple containing (assistant_response, references)
        """
        session_id = message.session_id

        # Get session to check for temporal filters
        session = self.chat_storage.get_session(session_id)
        if not session:
            raise ValueError(f"Chat session {session_id} not found")

        # Get chat configuration
        config = self.chat_storage.get_chat_config()

        # Find relevant entries for this message using enhanced retrieval
        references = self._enhanced_entry_retrieval(message, session, config)

        # Get conversation history
        conversation_history = self._prepare_conversation_history(session_id, config)

        # Add the new message to history
        conversation_history.append({"role": "user", "content": message.content})

        # Generate response using LLM
        response_text = self._generate_response(
            conversation_history, references, session, config
        )

        # Create and save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response_text,
            created_at=datetime.now(),
            metadata={"has_references": len(references) > 0},
        )

        # Save the assistant message
        saved_message = self.chat_storage.add_message(assistant_message)

        # Save references for citation tracking if there are any
        if references:
            # Update the references with the message ID
            for ref in references:
                ref.message_id = saved_message.id

            # Save the references
            self.chat_storage.add_message_entry_references(saved_message.id, references)

        return saved_message, references

    def _find_relevant_entries(
        self, message: ChatMessage, session: ChatSession, config: ChatConfig
    ) -> List[EntryReference]:
        """
        Find journal entries relevant to the message.

        Args:
            message: The message to find entries for
            session: The chat session
            config: Chat configuration

        Returns:
            List of entry references
        """
        try:
            # Get date filter if available
            date_filter = self._get_date_filter(session)

            # Try semantic search with date filter first
            try:
                search_results = self.llm_service.semantic_search(
                    message.content,
                    limit=config.retrieval_limit,
                    date_filter=date_filter,
                )
            except TypeError:
                # If date_filter is not supported, fall back to basic semantic search
                logger.info(
                    "Date filter not supported by semantic_search, "
                    "falling back to basic search"
                )
                search_results = self.llm_service.semantic_search(
                    message.content, limit=config.retrieval_limit
                )

            # Apply date filter manually if available
            if date_filter:
                # Convert filter dates to datetime objects if they're strings
                date_from = date_filter.get("date_from")
                date_to = date_filter.get("date_to")

                # Filter results based on dates
                filtered_results = []
                for result in search_results:
                    if "entry" in result:
                        entry = result["entry"]
                        # Skip if the entry doesn't have a created_at date
                        if not hasattr(entry, "created_at"):
                            continue

                        # Apply date filter
                        entry_date = entry.created_at
                        passes_filter = True

                        if date_from and entry_date < date_from:
                            passes_filter = False

                        if date_to and entry_date > date_to:
                            passes_filter = False

                        if passes_filter:
                            filtered_results.append(result)

                # Use filtered results
                search_results = filtered_results

            # Convert search results to EntryReference objects
            references = []
            for result in search_results:
                if "entry" in result and "similarity" in result:
                    entry = result["entry"]
                    similarity = result["similarity"]

                    # Check if entry is a proper JournalEntry object or a dict
                    if hasattr(entry, "id"):
                        entry_id = entry.id
                        entry_title = entry.title if hasattr(entry, "title") else None
                        entry_content = (
                            entry.content if hasattr(entry, "content") else ""
                        )
                    else:
                        # If it's a dict, extract the fields directly
                        entry_id = entry.get("id", "unknown")
                        entry_title = entry.get("title")
                        entry_content = entry.get("content", "")

                    # Create a snippet from the entry content
                    if entry_content and len(entry_content) > 100:
                        entry_snippet = entry_content[:100] + "..."
                    else:
                        entry_snippet = entry_content

                    # Create a reference (message_id will be set later)
                    reference = EntryReference(
                        message_id="",
                        entry_id=entry_id,
                        similarity_score=similarity,
                        entry_title=entry_title,
                        entry_snippet=entry_snippet,
                    )
                    references.append(reference)

            return references

        except Exception as e:
            logger.error(f"Error finding relevant entries: {str(e)}")
            return []

    def _prepare_conversation_history(
        self, session_id: str, config: ChatConfig
    ) -> List[Dict[str, str]]:
        """
        Prepare conversation history for the LLM.

        Args:
            session_id: The chat session ID
            config: Chat configuration

        Returns:
            List of message dictionaries in the format expected by the LLM
        """
        # Get recent messages from the session
        messages = self.chat_storage.get_messages(session_id)

        # Start with system message
        conversation = [{"role": "system", "content": config.system_prompt}]

        # Add messages from history
        for msg in messages:
            conversation.append({"role": msg.role, "content": msg.content})

        return conversation

    def _generate_response(
        self,
        conversation: List[Dict[str, str]],
        references: List[EntryReference],
        session: ChatSession,
        config: ChatConfig,
    ) -> str:
        """
        Generate a response using the LLM.

        Args:
            conversation: Conversation history
            references: Relevant entry references
            session: Current chat session
            config: Chat configuration

        Returns:
            Generated response text
        """
        try:
            # Add reference context to the system message if there are references
            if references and len(references) > 0:
                # Find the system message
                for message in conversation:
                    if message["role"] == "system":
                        # Add reference context
                        reference_context = self._format_references_for_context(
                            references
                        )
                        message["content"] += (
                            f"\nHere are some relevant journal entries to reference:\n"
                            f"{reference_context}"
                        )
                        break

            # Generate response using the LLM service
            response = self.llm_service.chat_completion(
                messages=conversation, temperature=config.temperature
            )

            # Extract the response text
            if isinstance(response, dict) and "choices" in response:
                # Format like the OpenAI API
                response_text = response["choices"][0]["message"]["content"]
            elif isinstance(response, dict) and "content" in response:
                # Direct content format
                response_text = response["content"]
            elif isinstance(response, str):
                # Plain text response
                response_text = response
            else:
                # Fallback
                response_text = str(response)

            return response_text

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I encountered an error while generating a response."

    def _format_references_for_context(self, references: List[EntryReference]) -> str:
        """
        Format entry references for inclusion in LLM context.

        Args:
            references: List of entry references

        Returns:
            Formatted reference text
        """
        if not references:
            return ""

        formatted_refs = []
        for i, ref in enumerate(references, 1):
            entry_date = ref.entry_id[:8]  # Extract date from ID format YYYYMMDD...
            try:
                # Try to format the date nicely if it's a valid date
                date_obj = datetime.strptime(entry_date, "%Y%m%d")
                date_str = date_obj.strftime("%B %d, %Y")
            except ValueError:
                # Fallback if date parsing fails
                date_str = entry_date

            # Add chunk information if available
            chunk_info = (
                f" (chunk {ref.chunk_index})" if ref.chunk_index is not None else ""
            )

            # Format each reference with relevance score and chunk info
            ref_text = (
                f"[{i}] Entry ID: {ref.entry_id}{chunk_info} - Date: {date_str} "
                f"(Relevance: {ref.similarity_score:.2f})\n"
                f"Title: {ref.entry_title or 'Untitled'}\n"
                f"Excerpt: {ref.entry_snippet or 'No content available'}\n"
            )
            formatted_refs.append(ref_text)

        # Join all references with a separator
        return "\n".join(formatted_refs)

    def _get_date_filter(self, session: ChatSession) -> Optional[Dict[str, Any]]:
        """
        Create a date filter based on session temporal filter.

        Args:
            session: The chat session

        Returns:
            Date filter dictionary or None
        """
        if not session.temporal_filter:
            return None

        now = datetime.now()

        if session.temporal_filter == "past_week":
            # Entries from the past week
            return {"date_from": now - timedelta(days=7), "date_to": now}
        elif session.temporal_filter == "past_month":
            # Entries from the past month
            return {"date_from": now - timedelta(days=30), "date_to": now}
        elif session.temporal_filter == "past_year":
            # Entries from the past year
            return {"date_from": now - timedelta(days=365), "date_to": now}
        elif session.temporal_filter.startswith("date:"):
            # Specific date in format "date:YYYY-MM-DD"
            try:
                date_str = session.temporal_filter[5:]  # Remove "date:" prefix
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return {
                    "date_from": date_obj,
                    "date_to": date_obj + timedelta(days=1),  # Include the whole day
                }
            except ValueError:
                logger.error(
                    f"Invalid date format in temporal filter: {session.temporal_filter}"
                )

        return None

    def _chunk_entry(
        self, entry: JournalEntry, chunk_size: int = 500, overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Split a journal entry into smaller chunks for more precise retrieval.

        Args:
            entry: The journal entry to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of chunks with their metadata
        """
        if not entry.content or len(entry.content) <= chunk_size:
            # Entry is small enough to be a single chunk
            return [
                {
                    "entry_id": entry.id,
                    "chunk_id": 0,
                    "text": entry.content,
                    "title": entry.title,
                    "created_at": entry.created_at,
                    "start_idx": 0,
                    "end_idx": len(entry.content) if entry.content else 0,
                }
            ]

        chunks = []
        content = entry.content

        # Split into chunks with overlap
        i = 0
        chunk_id = 0
        while i < len(content):
            # Calculate end of this chunk
            end = min(i + chunk_size, len(content))

            # Adjust end to avoid cutting in the middle of a sentence if possible
            if end < len(content):
                # Try to find sentence ending (., !, ?)
                sentence_end = max(
                    content.rfind(". ", i, end),
                    content.rfind("! ", i, end),
                    content.rfind("? ", i, end),
                    content.rfind(".\n", i, end),
                    content.rfind("!\n", i, end),
                    content.rfind("?\n", i, end),
                )

                # If found a sentence end, use that as the chunk end
                if (
                    sentence_end > i + chunk_size // 2
                ):  # Only if we've captured at least half a chunk
                    end = sentence_end + 1  # Include the sentence end character

            # Create the chunk
            chunks.append(
                {
                    "entry_id": entry.id,
                    "chunk_id": chunk_id,
                    "text": content[i:end],
                    "title": entry.title,
                    "created_at": entry.created_at,
                    "start_idx": i,
                    "end_idx": end,
                }
            )

            # Move to next chunk with overlap
            i = end - overlap if end < len(content) else len(content)
            chunk_id += 1

        return chunks

    def _enhanced_entry_retrieval(
        self, message: ChatMessage, session: ChatSession, config: ChatConfig
    ) -> List[EntryReference]:
        """
        Enhanced method to find relevant journal entries.

        This method:
        1. Applies date filtering based on session settings
        2. Gets candidate entries through semantic search
        3. Chunks long entries for more precise retrieval
        4. Performs hybrid search (semantic + keyword)
        5. Deduplicates results to avoid repetitive context
        6. Reranks results based on relevance score

        Args:
            message: The message to find entries for
            session: The chat session
            config: Chat configuration

        Returns:
            List of entry references sorted by relevance
        """
        try:
            # Get date filter if available
            date_filter = self._get_date_filter(session)

            # Step 1: Get candidate entries through semantic search
            candidate_results = []
            try:
                # Try with date filter if available
                if date_filter:
                    candidate_results = self.llm_service.semantic_search(
                        message.content,
                        limit=config.retrieval_limit
                        * 2,  # Get more candidates for chunking
                        date_filter=date_filter,
                    )
                else:
                    candidate_results = self.llm_service.semantic_search(
                        message.content, limit=config.retrieval_limit * 2
                    )
            except Exception as e:
                logger.warning(
                    f"Error in semantic search: {str(e)}, proceeding with empty results"
                )

            # Extract entries from results
            candidate_entries = []
            for result in candidate_results:
                if "entry" in result:
                    entry = result["entry"]
                    # Convert dict to JournalEntry if needed
                    if not isinstance(entry, JournalEntry):
                        try:
                            entry = JournalEntry(
                                id=entry.get("id"),
                                title=entry.get("title"),
                                content=entry.get("content"),
                                created_at=entry.get("created_at"),
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to convert dict to JournalEntry: {e}"
                            )
                            continue

                    candidate_entries.append(entry)

            # Step 2: Chunk longer entries
            all_chunks = []
            for entry in candidate_entries:
                chunks = self._chunk_entry(entry, chunk_size=config.chunk_size)
                all_chunks.extend(chunks)

            # Step 3: Score chunks using semantic similarity and keyword matching
            query = message.content.lower()
            query_terms = set(self._extract_keywords(query))

            scored_chunks = []
            # Generate embedding for query once
            try:
                query_embedding = self.llm_service.get_embedding(query)
                has_embeddings = True
            except Exception as e:
                logger.warning(f"Error generating query embedding: {e}")
                has_embeddings = False

            for chunk in all_chunks:
                # Base score
                score = 0.0

                # Semantic similarity scoring (if embeddings available)
                if has_embeddings:
                    try:
                        # Get embedding for the chunk
                        chunk_embedding = self.llm_service.get_embedding(chunk["text"])
                        # Calculate cosine similarity
                        semantic_score = self._calculate_similarity(
                            query_embedding, chunk_embedding
                        )
                        # Weight semantic score (60% of total)
                        score += semantic_score * 0.6
                    except Exception as e:
                        logger.warning(f"Error calculating semantic similarity: {e}")

                # Keyword matching scoring (40% of total or 100% if no embeddings)
                weight = 1.0 if not has_embeddings else 0.4
                chunk_text = chunk["text"].lower()

                # Count keyword matches
                contained_terms = 0
                for term in query_terms:
                    if term in chunk_text:
                        contained_terms += 1

                # Calculate keyword score based on percentage of query terms present
                keyword_score = contained_terms / max(1, len(query_terms))
                score += keyword_score * weight

                # Add to scored chunks
                chunk["relevance_score"] = score
                scored_chunks.append(chunk)

            # Step 4: Sort by relevance score
            scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)

            # Step 5: Deduplicate chunks from the same entry
            # Keep track of entries we've seen
            seen_entries = set()
            unique_chunks = []

            for chunk in scored_chunks:
                entry_id = chunk["entry_id"]
                # If we haven't seen this entry yet, or it's a highly relevant chunk
                if entry_id not in seen_entries or chunk["relevance_score"] > 0.8:
                    unique_chunks.append(chunk)
                    seen_entries.add(entry_id)

            # Step 6: Apply limit
            top_chunks = unique_chunks[: config.retrieval_limit]

            # Step 7: Create EntryReference objects from top chunks
            references = []
            for i, chunk in enumerate(top_chunks):
                # Extract the most relevant part of the chunk as snippet
                entry_snippet = chunk["text"]
                if len(entry_snippet) > 200:
                    entry_snippet = entry_snippet[:200] + "..."

                reference = EntryReference(
                    message_id="",  # Will be set later
                    entry_id=chunk["entry_id"],
                    similarity_score=chunk["relevance_score"],
                    chunk_index=chunk["chunk_id"],
                    entry_title=chunk["title"],
                    entry_snippet=entry_snippet,
                )
                references.append(reference)

            return references

        except Exception as e:
            logger.error(f"Error in enhanced entry retrieval: {str(e)}")
            # Fall back to basic retrieval method if enhanced method fails
            return self._find_relevant_entries(message, session, config)

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text, removing common stop words.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Simple stop words list
        stop_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "because",
            "as",
            "what",
            "when",
            "where",
            "how",
            "why",
            "which",
            "who",
            "whom",
            "this",
            "that",
            "these",
            "those",
            "i",
            "me",
            "my",
            "mine",
            "you",
            "your",
            "yours",
            "he",
            "him",
            "his",
            "she",
            "her",
            "hers",
            "it",
            "its",
            "we",
            "us",
            "our",
            "ours",
            "they",
            "them",
            "their",
            "theirs",
            "be",
            "been",
            "being",
            "am",
            "is",
            "are",
            "was",
            "were",
            "to",
            "of",
            "in",
            "on",
            "at",
            "by",
            "for",
            "with",
            "about",
            "against",
            "between",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "from",
            "up",
            "down",
            "in",
            "out",
            "on",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "all",
            "any",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "s",
            "t",
            "can",
            "will",
            "just",
            "don",
            "should",
            "now",
            "d",
            "ll",
            "m",
            "o",
            "re",
            "ve",
            "y",
            "ain",
            "aren",
            "couldn",
            "didn",
            "doesn",
            "hadn",
            "hasn",
            "haven",
            "isn",
            "ma",
            "mightn",
            "mustn",
            "needn",
            "shan",
            "shouldn",
            "wasn",
            "weren",
            "won",
            "wouldn",
            "my",
            "tell",
            "about",
            "would",
            "could",
            "find",
            "did",
            "get",
            "do",
            "does",
        }

        # Simple tokenization and filtering
        words = (
            text.lower()
            .replace("'", "")
            .replace('"', "")
            .replace(".", " ")
            .replace(",", " ")
        )
        word_list: list[str] = (
            words.replace("!", " ")
            .replace("?", " ")
            .replace(":", " ")
            .replace(";", " ")
            .split()
        )

        # Filter out stop words and short words
        keywords = [
            word for word in word_list if word not in stop_words and len(word) > 2
        ]
        return keywords

    def _calculate_similarity(self, vec1, vec2) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score between 0 and 1
        """
        import numpy as np

        # Convert to numpy arrays if they aren't already
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Calculate dot product and magnitudes
        dot_product = np.dot(v1, v2)
        mag1 = np.linalg.norm(v1)
        mag2 = np.linalg.norm(v2)

        # Calculate cosine similarity
        if mag1 > 0 and mag2 > 0:
            return dot_product / (mag1 * mag2)
        else:
            return 0.0
