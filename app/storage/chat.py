import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

from app.models import ChatSession, ChatMessage, ChatConfig, EntryReference
from app.storage.base import BaseStorage

# Configure logging
logger = logging.getLogger(__name__)


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
    ) -> bool:
        """
        Add entry references for a specific message.

        Args:
            message_id: The message ID
            references: List of entry references

        Returns:
            True if successful
        """
        if not references:
            return True

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Ensure the table exists
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_message_entries (
                    message_id TEXT NOT NULL,
                    entry_id TEXT NOT NULL,
                    similarity_score REAL NOT NULL,
                    chunk_index INTEGER,
                    PRIMARY KEY (message_id, entry_id, chunk_index)
                )
                """
            )

            # Insert references with chunk index info
            for reference in references:
                chunk_index = (
                    reference.chunk_index if reference.chunk_index is not None else 0
                )

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO chat_message_entries
                    (message_id, entry_id, similarity_score, chunk_index)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        reference.message_id,
                        reference.entry_id,
                        reference.similarity_score,
                        chunk_index,
                    ),
                )

            # Update entry_count for the session
            # Get the session_id from the message first
            cursor.execute(
                """
                SELECT session_id FROM chat_messages
                WHERE id = ?
                """,
                (message_id,),
            )
            result = cursor.fetchone()

            if result:
                session_id = result[0]

                # Count unique entries referenced in this session
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT e.entry_id)
                    FROM chat_message_entries e
                    JOIN chat_messages m ON e.message_id = m.id
                    WHERE m.session_id = ?
                    """,
                    (session_id,),
                )

                entry_count = cursor.fetchone()[0]

                # Update the session's entry_count
                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET entry_count = ?
                    WHERE id = ?
                    """,
                    (
                        entry_count,
                        session_id,
                    ),
                )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to add message entry references: {str(e)}")
            conn.rollback()
            return False

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
                SELECT COUNT(*) FROM chat_message_entries
                WHERE message_id = ?
                """,
                (message_id,),
            )

            if cursor.fetchone()[0] == 0:
                # No references for this message
                return []

            # Try a query that joins with the entries table to get title and content
            try:
                cursor.execute(
                    """
                    SELECT cme.entry_id, cme.similarity_score, cme.chunk_index,
                           e.title, substr(e.content, 1, 200) as snippet
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

            except Exception:
                # Fallback if the join query fails
                cursor.execute(
                    """
                    SELECT entry_id, similarity_score, chunk_index
                    FROM chat_message_entries
                    WHERE message_id = ?
                    ORDER BY similarity_score DESC
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
                        )
                    )

                # Now try to get additional info from entries table if it exists
                try:
                    # Only proceed if we have references to enrich
                    if references:
                        for ref in references:
                            cursor.execute(
                                """
                                SELECT title, substr(content, 1, 200) as snippet
                                FROM entries
                                WHERE id = ?
                                """,
                                (ref.entry_id,),
                            )
                            row = cursor.fetchone()
                            if row:
                                ref.entry_title = row[0]
                                ref.entry_snippet = row[1]
                except Exception:
                    # If this fails, it's OK - we just won't have title/snippet info
                    pass

                return references

        except Exception as e:
            logger.error(f"Failed to get message entry references: {str(e)}")
            return []

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
            # Check if the table exists and has the current schema
            cursor.execute("PRAGMA table_info(chat_config)")
            columns = [column[1] for column in cursor.fetchall()]

            if not columns:
                # Table doesn't exist, return default config
                return ChatConfig()

            # Create query based on existing columns
            query = "SELECT "
            fields = []

            if "system_prompt" in columns:
                fields.append("system_prompt")
            if "max_tokens" in columns:
                fields.append("max_tokens")
            elif "max_context_tokens" in columns:  # Handle legacy column name
                fields.append("max_context_tokens as max_tokens")
            if "temperature" in columns:
                fields.append("temperature")
            if "retrieval_limit" in columns:
                fields.append("retrieval_limit")
            if "chunk_size" in columns:
                fields.append("chunk_size")
            if "chunk_overlap" in columns:
                fields.append("chunk_overlap")
            if "use_enhanced_retrieval" in columns:
                fields.append("use_enhanced_retrieval")

            if not fields:
                # No recognized columns, return default config
                return ChatConfig()

            query += ", ".join(fields)
            query += " FROM chat_config WHERE id = 'default'"

            cursor.execute(query)
            row = cursor.fetchone()

            if not row:
                # No config found, return default
                return ChatConfig()

            # Create a dict to hold the config values
            config_data = {"id": "default"}

            # Add values from the database
            for i, field in enumerate(fields):
                # Extract the actual field name if it was aliased
                field_name = field.split(" as ")[-1]
                config_data[field_name] = row[i]

            # Create ChatConfig from the data
            return ChatConfig(**config_data)

        except Exception as e:
            logger.error(f"Error getting chat config: {str(e)}")
            # Return default config on error
            return ChatConfig()
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
            # Check if the table exists
            cursor.execute("PRAGMA table_info(chat_config)")
            columns = [column[1] for column in cursor.fetchall()]

            if not columns:
                # Create the table with the current schema
                cursor.execute(
                    """
                CREATE TABLE chat_config (
                    id TEXT PRIMARY KEY,
                    system_prompt TEXT,
                    temperature REAL,
                    max_tokens INTEGER,
                    retrieval_limit INTEGER,
                    chunk_size INTEGER,
                    chunk_overlap INTEGER,
                    max_history INTEGER,
                    use_enhanced_retrieval BOOLEAN
                )
                """
                )
            else:
                # Add any missing columns that exist in the current model
                if "system_prompt" not in columns:
                    cursor.execute(
                        "ALTER TABLE chat_config ADD COLUMN system_prompt TEXT"
                    )

                if "max_tokens" not in columns:
                    # Handle migration from old schema
                    if "max_context_tokens" in columns:
                        cursor.execute(
                            "ALTER TABLE chat_config ADD COLUMN max_tokens INTEGER"
                        )
                        cursor.execute(
                            "UPDATE chat_config SET max_tokens = max_context_tokens"
                        )
                    else:
                        cursor.execute(
                            "ALTER TABLE chat_config ADD COLUMN max_tokens INTEGER"
                        )

                if "temperature" not in columns:
                    cursor.execute(
                        "ALTER TABLE chat_config ADD COLUMN temperature REAL"
                    )

                if "retrieval_limit" not in columns:
                    cursor.execute(
                        "ALTER TABLE chat_config ADD COLUMN retrieval_limit INTEGER"
                    )

                if "chunk_size" not in columns:
                    cursor.execute(
                        "ALTER TABLE chat_config ADD COLUMN chunk_size INTEGER"
                    )

                if "chunk_overlap" not in columns:
                    cursor.execute(
                        "ALTER TABLE chat_config ADD COLUMN chunk_overlap INTEGER"
                    )

                if "max_history" not in columns:
                    cursor.execute(
                        "ALTER TABLE chat_config ADD COLUMN max_history INTEGER"
                    )

                if "use_enhanced_retrieval" not in columns:
                    cursor.execute(
                        "ALTER TABLE chat_config "
                        "ADD COLUMN use_enhanced_retrieval BOOLEAN"
                    )

            # Construct update fields and parameters based on existing columns
            update_fields = []
            params = []

            # Always include these core fields
            update_fields.append("system_prompt = ?")
            params.append(config.system_prompt)

            update_fields.append("temperature = ?")
            params.append(config.temperature)

            update_fields.append("max_tokens = ?")
            params.append(config.max_tokens)

            update_fields.append("retrieval_limit = ?")
            params.append(config.retrieval_limit)

            update_fields.append("chunk_size = ?")
            params.append(config.chunk_size)

            update_fields.append("chunk_overlap = ?")
            params.append(config.chunk_overlap)

            update_fields.append("max_history = ?")
            params.append(config.max_history)

            update_fields.append("use_enhanced_retrieval = ?")
            params.append(config.use_enhanced_retrieval)

            # Add legacy field if it exists
            if "conversation_summary_threshold" in columns:
                update_fields.append("conversation_summary_threshold = ?")
                params.append(0)  # Default value

            # Construct the update query
            update_query = (
                "UPDATE chat_config SET "
                + ", ".join(update_fields)
                + " WHERE id = 'default'"
            )

            cursor.execute(update_query, tuple(params))

            # Insert if update didn't affect any rows
            if cursor.rowcount == 0:
                insert_fields = ["id"]
                insert_values = ["default"]

                # Add all fields for insert
                for field, value in zip(
                    [
                        "system_prompt",
                        "temperature",
                        "max_tokens",
                        "retrieval_limit",
                        "chunk_size",
                        "chunk_overlap",
                        "max_history",
                        "use_enhanced_retrieval",
                    ],
                    [
                        config.system_prompt,
                        config.temperature,
                        config.max_tokens,
                        config.retrieval_limit,
                        config.chunk_size,
                        config.chunk_overlap,
                        config.max_history,
                        config.use_enhanced_retrieval,
                    ],
                ):
                    insert_fields.append(field)
                    insert_values.append(value)

                # Add legacy field if it exists
                if "conversation_summary_threshold" in columns:
                    insert_fields.append("conversation_summary_threshold")
                    insert_values.append(0)

                placeholders = ", ".join(["?" for _ in insert_fields])
                insert_query = f"INSERT INTO chat_config ({', '.join(insert_fields)}) "
                f"VALUES ({placeholders})"
                cursor.execute(insert_query, tuple(insert_values))

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update chat config: {str(e)}")
            raise e
        finally:
            conn.close()
