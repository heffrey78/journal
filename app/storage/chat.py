import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from app.models import ChatSession, ChatMessage, ChatConfig, EntryReference
from app.storage.base import BaseStorage

# Configure logging
logger = logging.getLogger(__name__)


class ChatStorage(BaseStorage):
    """Storage manager for chat functionality."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize the chat storage with database setup.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        super().__init__(base_dir)
        self._init_tables()

    def _init_tables(self):
        """Initialize the chat tables."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Create chat_sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    context_summary TEXT,
                    temporal_filter TEXT,
                    entry_count INTEGER DEFAULT 0,
                    model_name TEXT,
                    persona_id TEXT
                )
                """
            )

            # Add persona_id column if it doesn't exist (for migration)
            cursor.execute("PRAGMA table_info(chat_sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            if "persona_id" not in columns:
                cursor.execute("ALTER TABLE chat_sessions ADD COLUMN persona_id TEXT")

            # Create chat_messages table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT,
                    token_count INTEGER,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                )
                """
            )

            # Create chat_message_entries table for entry references
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

            # Create indexes for performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_message_entries_message_id ON chat_message_entries(message_id)"
            )

            # Create FTS (Full-Text Search) tables for search functionality
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS chat_sessions_fts USING fts5(
                    session_id UNINDEXED,
                    title,
                    context_summary
                )
                """
            )

            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS chat_messages_fts USING fts5(
                    message_id UNINDEXED,
                    session_id UNINDEXED,
                    content,
                    role UNINDEXED
                )
                """
            )

            # Create triggers to keep FTS tables in sync
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS chat_sessions_fts_insert AFTER INSERT ON chat_sessions BEGIN
                    INSERT INTO chat_sessions_fts(session_id, title, context_summary)
                    VALUES (new.id, new.title, new.context_summary);
                END
                """
            )

            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS chat_sessions_fts_update AFTER UPDATE ON chat_sessions BEGIN
                    UPDATE chat_sessions_fts
                    SET title = new.title, context_summary = new.context_summary
                    WHERE session_id = new.id;
                END
                """
            )

            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS chat_sessions_fts_delete AFTER DELETE ON chat_sessions BEGIN
                    DELETE FROM chat_sessions_fts WHERE session_id = old.id;
                END
                """
            )

            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS chat_messages_fts_insert AFTER INSERT ON chat_messages BEGIN
                    INSERT INTO chat_messages_fts(message_id, session_id, content, role)
                    VALUES (new.id, new.session_id, new.content, new.role);
                END
                """
            )

            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS chat_messages_fts_update AFTER UPDATE ON chat_messages BEGIN
                    UPDATE chat_messages_fts
                    SET content = new.content
                    WHERE message_id = new.id;
                END
                """
            )

            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS chat_messages_fts_delete AFTER DELETE ON chat_messages BEGIN
                    DELETE FROM chat_messages_fts WHERE message_id = old.id;
                END
                """
            )

            conn.commit()
        finally:
            conn.close()

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
                    context_summary, temporal_filter, entry_count, persona_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    session.persona_id,
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
                    context_summary = ?, temporal_filter = ?, entry_count = ?, persona_id = ?
                WHERE id = ?
                """,
                (
                    session.title,
                    updated_at,
                    last_accessed,
                    session.context_summary,
                    session.temporal_filter,
                    session.entry_count,
                    session.persona_id,
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
                       context_summary, temporal_filter, entry_count, persona_id
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
                persona_id=row[8],
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

    def count_sessions(self) -> int:
        """
        Get the total number of chat sessions.

        Returns:
            Total count of chat sessions
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM chat_sessions")
            count = cursor.fetchone()[0]
            return count

        finally:
            conn.close()

    def list_sessions(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "last_accessed",
        sort_order: str = "desc",
    ) -> List[ChatSession]:
        """
        List chat sessions with pagination and sorting options.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            sort_by: Field to sort by (
            'last_accessed',
            'updated_at',
            'created_at',
            'title')
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            List of ChatSession objects
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Validate sort parameters to prevent SQL injection
        allowed_sort_fields = [
            "last_accessed",
            "updated_at",
            "created_at",
            "title",
            "entry_count",
        ]
        if sort_by not in allowed_sort_fields:
            sort_by = "last_accessed"  # Default to last_accessed if invalid

        sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"

        try:
            cursor.execute(
                f"""
                SELECT id, title, created_at, updated_at, last_accessed,
                       context_summary, temporal_filter, entry_count, persona_id
                FROM chat_sessions
                ORDER BY {sort_by} {sort_direction}
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
                        persona_id=row[8],
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

            # Define all possible fields with their values
            field_mappings = [
                ("system_prompt", config.system_prompt),
                ("temperature", config.temperature),
                ("max_tokens", config.max_tokens),
                ("retrieval_limit", config.retrieval_limit),
                ("chunk_size", config.chunk_size),
                ("chunk_overlap", config.chunk_overlap),
                ("max_history", config.max_history),
                ("use_enhanced_retrieval", config.use_enhanced_retrieval),
                # Migration script fields
                ("max_context_tokens", config.max_context_tokens),
                (
                    "conversation_summary_threshold",
                    config.conversation_summary_threshold,
                ),
                ("context_window_size", config.context_window_size),
                ("use_context_windowing", config.use_context_windowing),
                ("min_messages_for_summary", config.min_messages_for_summary),
                ("summary_prompt", config.summary_prompt),
            ]

            # Only update fields that exist in the current table schema
            for field, value in field_mappings:
                if field in columns:
                    update_fields.append(f"{field} = ?")
                    params.append(value)

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

                # Add all fields for insert - include ALL fields that might exist from migration
                field_mappings = [
                    ("system_prompt", config.system_prompt),
                    ("temperature", config.temperature),
                    ("max_tokens", config.max_tokens),
                    ("retrieval_limit", config.retrieval_limit),
                    ("chunk_size", config.chunk_size),
                    ("chunk_overlap", config.chunk_overlap),
                    ("max_history", config.max_history),
                    ("use_enhanced_retrieval", config.use_enhanced_retrieval),
                    # Migration script fields
                    ("max_context_tokens", config.max_context_tokens),
                    (
                        "conversation_summary_threshold",
                        config.conversation_summary_threshold,
                    ),
                    ("context_window_size", config.context_window_size),
                    ("use_context_windowing", config.use_context_windowing),
                    ("min_messages_for_summary", config.min_messages_for_summary),
                    ("summary_prompt", config.summary_prompt),
                ]

                # Only add fields that exist in the current table schema
                for field, value in field_mappings:
                    if field in columns:
                        insert_fields.append(field)
                        insert_values.append(value)

                placeholders = ", ".join(["?" for _ in insert_fields])
                insert_query = f"INSERT INTO chat_config ({', '.join(insert_fields)}) VALUES ({placeholders})"
                cursor.execute(insert_query, tuple(insert_values))

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update chat config: {str(e)}")
            raise e
        finally:
            conn.close()

    def get_message(self, message_id: str) -> Optional[ChatMessage]:
        """
        Get a specific chat message by ID.

        Args:
            message_id: The ID of the message to retrieve

        Returns:
            ChatMessage object if found, None otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, session_id, role, content, created_at, metadata, token_count
                FROM chat_messages
                WHERE id = ?
                """,
                (message_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Parse the row data
            (
                id,
                session_id,
                role,
                content,
                created_at,
                metadata_json,
                token_count,
            ) = row

            # Parse metadata
            metadata = {}
            if metadata_json:
                try:
                    metadata = json.loads(metadata_json)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid metadata JSON for message {id}")
                    metadata = {}

            # Parse created_at
            created_at_obj = datetime.fromisoformat(created_at)

            return ChatMessage(
                id=id,
                session_id=session_id,
                role=role,
                content=content,
                created_at=created_at_obj,
                metadata=metadata,
                token_count=token_count,
            )

        except Exception as e:
            logger.error(f"Failed to get message {message_id}: {str(e)}")
            return None

        finally:
            conn.close()

    def update_message_content(self, message_id: str, content: str) -> bool:
        """
        Update the content of an existing chat message.

        This is especially useful for streaming responses where the message
        content is built up over time.

        Args:
            message_id: The ID of the message to update
            content: The new content for the message

        Returns:
            True if successful, False otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE chat_messages
                SET content = ?
                WHERE id = ?
                """,
                (content, message_id),
            )

            success = cursor.rowcount > 0
            conn.commit()
            return success

        except Exception as e:
            logger.error(f"Failed to update message content: {str(e)}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific chat session.

        Args:
            session_id: The chat session ID

        Returns:
            Dictionary with message count, unique entry references, etc.
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Get total message count
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM chat_messages
                WHERE session_id = ?
                """,
                (session_id,),
            )
            total_count = cursor.fetchone()[0]

            # Get message counts by role
            cursor.execute(
                """
                SELECT role, COUNT(*)
                FROM chat_messages
                WHERE session_id = ?
                GROUP BY role
                """,
                (session_id,),
            )

            role_counts = {role: count for role, count in cursor.fetchall()}
            user_count = role_counts.get("user", 0)
            assistant_count = role_counts.get("assistant", 0)

            # Get reference count
            cursor.execute(
                """
                SELECT COUNT(DISTINCT e.entry_id)
                FROM chat_message_entries e
                JOIN chat_messages m ON e.message_id = m.id
                WHERE m.session_id = ?
                """,
                (session_id,),
            )
            reference_count = cursor.fetchone()[0]

            # Get the last message preview
            cursor.execute(
                """
                SELECT content
                FROM chat_messages
                WHERE session_id = ? AND role = 'assistant'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (session_id,),
            )
            last_message_row = cursor.fetchone()
            last_message = last_message_row[0] if last_message_row else ""

            # Create preview (first ~100 chars)
            message_preview = last_message[:100] + (
                "..." if len(last_message) > 100 else ""
            )

            return {
                "message_count": total_count,
                "user_message_count": user_count,
                "assistant_message_count": assistant_count,
                "reference_count": reference_count,
                "last_message_preview": message_preview,
            }

        except Exception as e:
            logger.error(f"Failed to get session stats: {str(e)}")
            return {
                "message_count": 0,
                "user_message_count": 0,
                "assistant_message_count": 0,
                "reference_count": 0,
                "last_message_preview": "",
            }
        finally:
            conn.close()

    def update_message(
        self, message_id: str, content: str, edited: bool = True
    ) -> bool:
        """
        Update the content of an existing chat message and track edit history.

        Args:
            message_id: The ID of the message to update
            content: The new content for the message
            edited: Whether to mark this message as edited

        Returns:
            True if successful, False otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # First get the original message to preserve edit history
            cursor.execute(
                """
                SELECT content, metadata
                FROM chat_messages
                WHERE id = ?
                """,
                (message_id,),
            )

            row = cursor.fetchone()
            if not row:
                return False

            original_content = row[0]
            metadata = json.loads(row[1]) if row[1] else {}

            # Update metadata to track edit history
            if edited:
                if "edit_history" not in metadata:
                    metadata["edit_history"] = []

                metadata["edit_history"].append(
                    {
                        "content": original_content,
                        "edited_at": datetime.now().isoformat(),
                    }
                )
                metadata["edited"] = True
                metadata["last_edited_at"] = datetime.now().isoformat()

            metadata_json = json.dumps(metadata)

            # Update the message
            cursor.execute(
                """
                UPDATE chat_messages
                SET content = ?, metadata = ?
                WHERE id = ?
                """,
                (content, metadata_json, message_id),
            )

            # Update session's updated_at timestamp
            cursor.execute(
                """
                UPDATE chat_sessions
                SET updated_at = ?
                WHERE id = (SELECT session_id FROM chat_messages WHERE id = ?)
                """,
                (datetime.now().isoformat(), message_id),
            )

            success = cursor.rowcount > 0
            conn.commit()
            return success

        except Exception as e:
            logger.error(f"Failed to update message: {str(e)}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def delete_message(self, message_id: str) -> bool:
        """
        Delete a chat message from the database.

        Args:
            message_id: The ID of the message to delete

        Returns:
            True if successful, False otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # First get the session_id before deleting the message
            cursor.execute(
                "SELECT session_id FROM chat_messages WHERE id = ?",
                (message_id,),
            )
            session_row = cursor.fetchone()

            if not session_row:
                # Message doesn't exist
                return False

            session_id = session_row[0]

            # Delete associated entry references first
            cursor.execute(
                "DELETE FROM chat_message_entries WHERE message_id = ?",
                (message_id,),
            )

            # Delete the message
            cursor.execute(
                "DELETE FROM chat_messages WHERE id = ?",
                (message_id,),
            )

            message_deleted = cursor.rowcount > 0

            # Update session's updated_at timestamp using the retrieved session_id
            cursor.execute(
                """
                UPDATE chat_sessions
                SET updated_at = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), session_id),
            )

            conn.commit()
            return message_deleted

        except Exception as e:
            logger.error(f"Failed to delete message: {str(e)}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def delete_messages_range(
        self, session_id: str, start_index: int, end_index: int
    ) -> bool:
        """
        Delete a range of messages from a chat session.

        Args:
            session_id: The ID of the chat session
            start_index: The starting index (inclusive)
            end_index: The ending index (inclusive)

        Returns:
            True if successful, False otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Get message IDs in the range
            cursor.execute(
                """
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) - 1 as idx
                    FROM chat_messages
                    WHERE session_id = ?
                ) WHERE idx >= ? AND idx <= ?
                """,
                (session_id, start_index, end_index),
            )

            message_ids = [row[0] for row in cursor.fetchall()]

            if not message_ids:
                return False

            # Delete entry references
            placeholders = ",".join("?" * len(message_ids))
            cursor.execute(
                f"DELETE FROM chat_message_entries WHERE message_id IN ({placeholders})",
                message_ids,
            )

            # Delete messages
            cursor.execute(
                f"DELETE FROM chat_messages WHERE id IN ({placeholders})",
                message_ids,
            )

            # Update session's updated_at timestamp
            cursor.execute(
                """
                UPDATE chat_sessions
                SET updated_at = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), session_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to delete message range: {str(e)}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def cleanup_empty_sessions(self) -> int:
        """
        Remove chat sessions that have no messages (0-length sessions).

        This method is used to clean up sessions that were created but never used,
        which can happen when users navigate to a new chat but don't send any messages.

        Returns:
            Number of empty sessions that were deleted
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Find sessions with no messages
            cursor.execute(
                """
                SELECT id FROM chat_sessions
                WHERE id NOT IN (
                    SELECT DISTINCT session_id FROM chat_messages
                )
                """
            )

            empty_session_ids = [row[0] for row in cursor.fetchall()]

            if not empty_session_ids:
                return 0

            # Delete empty sessions
            placeholders = ",".join("?" * len(empty_session_ids))
            cursor.execute(
                f"DELETE FROM chat_sessions WHERE id IN ({placeholders})",
                empty_session_ids,
            )

            deleted_count = cursor.rowcount
            conn.commit()

            logger.info(f"Cleaned up {deleted_count} empty chat sessions")
            return deleted_count

        except Exception as e:
            conn.rollback()
            logger.error(f"Error cleaning up empty sessions: {str(e)}")
            raise e
        finally:
            conn.close()

    def search_sessions(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "relevance",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[ChatSession]:
        """
        Search chat sessions using full-text search.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            sort_by: Sort order ('relevance', 'date', 'title')
            date_from: Start date filter (ISO format)
            date_to: End date filter (ISO format)

        Returns:
            List of matching ChatSession objects
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Build the search query
            params = []

            # Add text search using FTS
            if query.strip():
                # Search sessions by title and get sessions with matching messages
                combined_query = """
                    SELECT DISTINCT s.id, s.title, s.created_at, s.updated_at, s.last_accessed,
                           s.context_summary, s.temporal_filter, s.entry_count, s.persona_id,
                           'session_title' as match_type, 0 as rank
                    FROM chat_sessions s
                    WHERE s.title LIKE ? OR s.id IN (
                        SELECT DISTINCT m.session_id
                        FROM chat_messages m
                        WHERE m.content LIKE ?
                    )
                """
                params.extend([f"%{query}%", f"%{query}%"])
            else:
                # If no search query, just get all sessions
                combined_query = """
                    SELECT id, title, created_at, updated_at, last_accessed,
                           context_summary, temporal_filter, entry_count, persona_id,
                           'all' as match_type, 0 as rank
                    FROM chat_sessions
                """

            # Add date filtering
            where_conditions = []
            if date_from:
                where_conditions.append("last_accessed >= ?")
                params.append(date_from)
            if date_to:
                where_conditions.append("last_accessed <= ?")
                params.append(date_to)

            if where_conditions:
                if query.strip():
                    # Wrap the union query and add WHERE clause
                    combined_query = f"""
                        SELECT * FROM ({combined_query})
                        WHERE {' AND '.join(where_conditions)}
                    """
                else:
                    combined_query += f" WHERE {' AND '.join(where_conditions)}"

            # Add sorting
            if sort_by == "relevance" and query.strip():
                combined_query += " ORDER BY rank DESC"
            elif sort_by == "date":
                combined_query += " ORDER BY last_accessed DESC"
            elif sort_by == "title":
                combined_query += " ORDER BY title ASC"
            else:
                combined_query += " ORDER BY last_accessed DESC"

            # Add pagination
            combined_query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(combined_query, params)

            sessions = []
            seen_ids = set()  # Avoid duplicates from union

            for row in cursor.fetchall():
                session_id = row[0]
                if session_id not in seen_ids:
                    seen_ids.add(session_id)
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
                            persona_id=row[8],
                        )
                    )

            return sessions

        finally:
            conn.close()

    def count_search_results(
        self, query: str, date_from: Optional[str] = None, date_to: Optional[str] = None
    ) -> int:
        """
        Count total number of search results for pagination.

        Args:
            query: Search query string
            date_from: Start date filter (ISO format)
            date_to: End date filter (ISO format)

        Returns:
            Total count of matching sessions
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            params = []

            if query.strip():
                # Count distinct sessions that match in either title or messages
                fts_query = f"'{query}'"

                count_query = f"""
                    SELECT COUNT(DISTINCT session_id) FROM (
                        SELECT sf.session_id FROM chat_sessions_fts sf WHERE chat_sessions_fts MATCH {fts_query}
                        UNION
                        SELECT mf.session_id FROM chat_messages_fts mf WHERE chat_messages_fts MATCH {fts_query}
                    ) as matches
                """

                # Add date filtering if needed
                if date_from or date_to:
                    count_query = f"""
                        SELECT COUNT(DISTINCT s.id) FROM chat_sessions s
                        WHERE s.id IN (
                            SELECT sf.session_id FROM chat_sessions_fts sf WHERE chat_sessions_fts MATCH {fts_query}
                            UNION
                            SELECT mf.session_id FROM chat_messages_fts mf WHERE chat_messages_fts MATCH {fts_query}
                        )
                    """

                    where_conditions = []
                    if date_from:
                        where_conditions.append("s.last_accessed >= ?")
                        params.append(date_from)
                    if date_to:
                        where_conditions.append("s.last_accessed <= ?")
                        params.append(date_to)

                    if where_conditions:
                        count_query += f" AND {' AND '.join(where_conditions)}"
            else:
                # Count all sessions with date filtering
                count_query = "SELECT COUNT(*) FROM chat_sessions"
                where_conditions = []

                if date_from:
                    where_conditions.append("last_accessed >= ?")
                    params.append(date_from)
                if date_to:
                    where_conditions.append("last_accessed <= ?")
                    params.append(date_to)

                if where_conditions:
                    count_query += f" WHERE {' AND '.join(where_conditions)}"

            cursor.execute(count_query, params)
            return cursor.fetchone()[0]

        finally:
            conn.close()

    def search_messages_in_session(
        self, session_id: str, query: str, limit: int = 50
    ) -> List[ChatMessage]:
        """
        Search within a specific chat session's messages.

        Args:
            session_id: The session to search within
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching ChatMessage objects
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            if not query.strip():
                # Return recent messages if no query
                return self.get_messages(session_id)

            fts_query = f"'{query}'"

            cursor.execute(
                f"""
                SELECT m.id, m.session_id, m.role, m.content, m.created_at, m.metadata, m.token_count
                FROM chat_messages m
                JOIN chat_messages_fts mf ON m.id = mf.message_id
                WHERE m.session_id = ? AND chat_messages_fts MATCH {fts_query}
                ORDER BY m.created_at ASC
                LIMIT ?
                """,
                (session_id, limit),
            )

            messages = []
            for row in cursor.fetchall():
                # Parse metadata JSON if it exists
                metadata = json.loads(row[5]) if row[5] else None

                messages.append(
                    ChatMessage(
                        id=row[0],
                        session_id=row[1],
                        role=row[2],
                        content=row[3],
                        created_at=datetime.fromisoformat(row[4]),
                        metadata=metadata,
                        token_count=row[6],
                    )
                )

            return messages

        finally:
            conn.close()

    def rebuild_search_index(self):
        """
        Rebuild the FTS search index from existing data.
        This should be called if the FTS tables get out of sync.
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Clear existing FTS data
            cursor.execute("DELETE FROM chat_sessions_fts")
            cursor.execute("DELETE FROM chat_messages_fts")

            # Rebuild sessions FTS
            cursor.execute(
                """
                INSERT INTO chat_sessions_fts(session_id, title, context_summary)
                SELECT id, title, context_summary FROM chat_sessions
                """
            )

            # Rebuild messages FTS
            cursor.execute(
                """
                INSERT INTO chat_messages_fts(message_id, session_id, content, role)
                SELECT id, session_id, content, role FROM chat_messages
                """
            )

            conn.commit()
            logger.info("Successfully rebuilt chat search index")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to rebuild search index: {str(e)}")
            raise e
        finally:
            conn.close()
