import json
from datetime import datetime
from typing import List, Dict, Optional

from app.models import ChatSession, ChatMessage, ChatConfig, EntryReference
from app.storage.base import BaseStorage


class ChatStorage(BaseStorage):
    """Storage manager for chat functionality."""

    def create_session(self, session: ChatSession) -> ChatSession:
        """
        Create a new chat session in the database.

        Args:
            session: The ChatSession object to create

        Returns:
            The created ChatSession with any default fields populated
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Convert datetime objects to ISO format strings for SQLite storage
            created_at = session.created_at.isoformat()
            updated_at = session.updated_at.isoformat()
            last_accessed = session.last_accessed.isoformat()

            cursor.execute(
                """
                INSERT INTO chat_sessions (
                    id, title, created_at, updated_at, last_accessed,
                    context_summary, temporal_filter, entry_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.id,
                    session.title,
                    created_at,
                    updated_at,
                    last_accessed,
                    session.context_summary,
                    session.temporal_filter,
                    session.entry_count,
                ),
            )
            conn.commit()
            return session

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def update_session(self, session: ChatSession) -> ChatSession:
        """
        Update an existing chat session.

        Args:
            session: The updated ChatSession object

        Returns:
            The updated ChatSession
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Convert datetime objects to ISO format strings for SQLite storage
            updated_at = session.updated_at.isoformat()
            last_accessed = session.last_accessed.isoformat()

            cursor.execute(
                """
                UPDATE chat_sessions
                SET title = ?, updated_at = ?, last_accessed = ?,
                    context_summary = ?, temporal_filter = ?, entry_count = ?
                WHERE id = ?
                """,
                (
                    session.title,
                    updated_at,
                    last_accessed,
                    session.context_summary,
                    session.temporal_filter,
                    session.entry_count,
                    session.id,
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(f"Chat session with ID {session.id} not found")

            conn.commit()
            return session

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Retrieve a chat session by ID.

        Args:
            session_id: The ID of the session to retrieve

        Returns:
            ChatSession if found, None otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, title, created_at, updated_at, last_accessed,
                       context_summary, temporal_filter, entry_count
                FROM chat_sessions
                WHERE id = ?
                """,
                (session_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Parse ISO format dates back to datetime objects
            return ChatSession(
                id=row[0],
                title=row[1],
                created_at=datetime.fromisoformat(row[2]),
                updated_at=datetime.fromisoformat(row[3]),
                last_accessed=datetime.fromisoformat(row[4]),
                context_summary=row[5],
                temporal_filter=row[6],
                entry_count=row[7],
            )

        finally:
            conn.close()

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session and all its messages.

        Args:
            session_id: The ID of the session to delete

        Returns:
            True if successful, False if session not found
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM chat_sessions WHERE id = ?",
                (session_id,),
            )

            success = cursor.rowcount > 0
            conn.commit()
            return success

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def list_sessions(self, limit: int = 10, offset: int = 0) -> List[ChatSession]:
        """
        List chat sessions with pagination.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of ChatSession objects
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, title, created_at, updated_at, last_accessed,
                       context_summary, temporal_filter, entry_count
                FROM chat_sessions
                ORDER BY last_accessed DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

            sessions = []
            for row in cursor.fetchall():
                sessions.append(
                    ChatSession(
                        id=row[0],
                        title=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        updated_at=datetime.fromisoformat(row[3]),
                        last_accessed=datetime.fromisoformat(row[4]),
                        context_summary=row[5],
                        temporal_filter=row[6],
                        entry_count=row[7],
                    )
                )

            return sessions

        finally:
            conn.close()

    def add_message(self, message: ChatMessage) -> ChatMessage:
        """
        Add a new message to a chat session.

        Args:
            message: The ChatMessage object to add

        Returns:
            The added ChatMessage
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Convert datetime to ISO format string
            created_at = message.created_at.isoformat()

            # Convert metadata dictionary to JSON string if it exists
            metadata_json = json.dumps(message.metadata) if message.metadata else None

            cursor.execute(
                """
                INSERT INTO chat_messages (
                    id, session_id, role, content, created_at, metadata, token_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.session_id,
                    message.role,
                    message.content,
                    created_at,
                    metadata_json,
                    message.token_count,
                ),
            )

            # Update the session's last_accessed timestamp
            cursor.execute(
                """
                UPDATE chat_sessions
                SET last_accessed = ?, updated_at = ?
                WHERE id = ?
                """,
                (created_at, created_at, message.session_id),
            )

            conn.commit()
            return message

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """
        Retrieve all messages for a chat session.

        Args:
            session_id: The ID of the session

        Returns:
            List of ChatMessage objects in chronological order
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, role, content, created_at, metadata, token_count
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            )

            messages = []
            for row in cursor.fetchall():
                # Parse metadata JSON if it exists
                metadata = json.loads(row[4]) if row[4] else None

                messages.append(
                    ChatMessage(
                        id=row[0],
                        session_id=session_id,
                        role=row[1],
                        content=row[2],
                        created_at=datetime.fromisoformat(row[3]),
                        metadata=metadata,
                        token_count=row[5],
                    )
                )

            return messages

        finally:
            conn.close()

    def add_message_entry_references(
        self, message_id: str, references: List[EntryReference]
    ) -> None:
        """
        Add entry references for a message.

        Args:
            message_id: The message ID
            references: List of EntryReference objects
        """
        if not references:
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            for ref in references:
                cursor.execute(
                    """
                    INSERT INTO chat_message_entries (
                        message_id, entry_id, similarity_score, chunk_index
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (message_id, ref.entry_id, ref.similarity_score, ref.chunk_index),
                )

            # Update the entry_count in the session
            cursor.execute(
                """
                UPDATE chat_sessions
                SET entry_count = (
                    SELECT COUNT(DISTINCT entry_id)
                    FROM chat_message_entries
                    WHERE message_id IN (
                        SELECT id FROM chat_messages WHERE session_id = (
                            SELECT session_id FROM chat_messages WHERE id = ?
                        )
                    )
                )
                WHERE id = (SELECT session_id FROM chat_messages WHERE id = ?)
                """,
                (message_id, message_id),
            )

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_message_entry_references(self, message_id: str) -> List[EntryReference]:
        """
        Get entry references for a specific message.

        Args:
            message_id: The message ID

        Returns:
            List of EntryReference objects
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT cme.entry_id, cme.similarity_score, cme.chunk_index,
                       e.title, substr(e.content, 1, 100) as snippet
                FROM chat_message_entries cme
                JOIN entries e ON cme.entry_id = e.id
                WHERE cme.message_id = ?
                ORDER BY cme.similarity_score DESC
                """,
                (message_id,),
            )

            references = []
            for row in cursor.fetchall():
                references.append(
                    EntryReference(
                        message_id=message_id,
                        entry_id=row[0],
                        similarity_score=row[1],
                        chunk_index=row[2],
                        entry_title=row[3],
                        entry_snippet=row[4],
                    )
                )

            return references

        finally:
            conn.close()

    def get_session_entry_references(
        self, session_id: str
    ) -> Dict[str, List[EntryReference]]:
        """
        Get all entry references for a chat session grouped by message ID.

        Args:
            session_id: The session ID

        Returns:
            Dictionary mapping message IDs to lists of EntryReference objects
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT cme.message_id, cme.entry_id, cme.similarity_score,
                       cme.chunk_index, e.title, substr(e.content, 1, 100) as snippet
                FROM chat_message_entries cme
                JOIN chat_messages cm ON cme.message_id = cm.id
                JOIN entries e ON cme.entry_id = e.id
                WHERE cm.session_id = ?
                ORDER BY cme.similarity_score DESC
                """,
                (session_id,),
            )

            references_by_message = {}
            for row in cursor.fetchall():
                message_id = row[0]
                if message_id not in references_by_message:
                    references_by_message[message_id] = []

                references_by_message[message_id].append(
                    EntryReference(
                        message_id=message_id,
                        entry_id=row[1],
                        similarity_score=row[2],
                        chunk_index=row[3],
                        entry_title=row[4],
                        entry_snippet=row[5],
                    )
                )

            return references_by_message

        finally:
            conn.close()

    def get_chat_config(self) -> ChatConfig:
        """
        Get the chat configuration.

        Returns:
            ChatConfig object with current settings
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT system_prompt, max_context_tokens, temperature,
                       retrieval_limit, chunk_size, conversation_summary_threshold
                FROM chat_config
                WHERE id = 'default'
                """
            )

            row = cursor.fetchone()
            if not row:
                # Return default config if none exists in the database
                return ChatConfig()

            return ChatConfig(
                system_prompt=row[0],
                max_context_tokens=row[1],
                temperature=row[2],
                retrieval_limit=row[3],
                chunk_size=row[4],
                conversation_summary_threshold=row[5],
            )

        finally:
            conn.close()

    def update_chat_config(self, config: ChatConfig) -> None:
        """
        Update the chat configuration.

        Args:
            config: ChatConfig object with new settings
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE chat_config
                SET system_prompt = ?, max_context_tokens = ?,
                    temperature = ?, retrieval_limit = ?,
                    chunk_size = ?, conversation_summary_threshold = ?
                WHERE id = 'default'
                """,
                (
                    config.system_prompt,
                    config.max_context_tokens,
                    config.temperature,
                    config.retrieval_limit,
                    config.chunk_size,
                    config.conversation_summary_threshold,
                ),
            )

            if cursor.rowcount == 0:
                # Insert if update didn't affect any rows
                cursor.execute(
                    """
                    INSERT INTO chat_config (
                        id, system_prompt, max_context_tokens, temperature,
                        retrieval_limit, chunk_size, conversation_summary_threshold
                    ) VALUES ('default', ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        config.system_prompt,
                        config.max_context_tokens,
                        config.temperature,
                        config.retrieval_limit,
                        config.chunk_size,
                        config.conversation_summary_threshold,
                    ),
                )

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
