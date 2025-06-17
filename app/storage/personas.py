import logging
from datetime import datetime
from typing import List, Optional

from app.models import Persona, PersonaCreate, PersonaUpdate
from app.storage.base import BaseStorage

# Configure logging
logger = logging.getLogger(__name__)


class PersonaStorage(BaseStorage):
    """Storage manager for chat personas."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize the persona storage with database setup.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        super().__init__(base_dir)
        self._init_tables()
        self._seed_default_personas()

    def _init_tables(self):
        """Initialize the personas table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Create personas table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS personas (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    icon TEXT DEFAULT '🤖',
                    is_default BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
                """
            )

            # Create indexes for performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_personas_is_default ON personas(is_default)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_personas_name ON personas(name)"
            )

            conn.commit()
        finally:
            conn.close()

    def _seed_default_personas(self):
        """Seed default personas if they don't exist, or update them if they need tool awareness."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if default personas already exist
            cursor.execute("SELECT COUNT(*) FROM personas WHERE is_default = 1")
            default_count = cursor.fetchone()[0]

            if default_count > 0:
                # Check if personas need updating (look for tool awareness)
                cursor.execute(
                    "SELECT system_prompt FROM personas WHERE is_default = 1 LIMIT 1"
                )
                sample_prompt = cursor.fetchone()[0]
                if "search tools" not in sample_prompt:
                    # Update existing personas with tool awareness
                    self._update_default_personas(cursor)
                    conn.commit()
                return

            # Define default personas
            default_personas = [
                {
                    "id": "persona-journal",
                    "name": "Journaling Assistant",
                    "description": "A supportive companion for personal reflection and writing prompts",
                    "system_prompt": "You are a thoughtful journaling assistant with access to search tools. Help users explore their thoughts, feelings, and experiences through gentle questioning and supportive reflection. You can search through their journal entries to find relevant past experiences and search the web for current information when needed. Encourage deeper self-awareness and provide writing prompts when helpful. Be empathetic, non-judgmental, and focused on personal growth. When referencing search results, cite them appropriately.",
                    "icon": "📖",
                },
                {
                    "id": "persona-coach",
                    "name": "Coach",
                    "description": "A motivational coach focused on goal achievement and personal development",
                    "system_prompt": "You are an encouraging life coach with access to search tools. Help users set and achieve their goals through motivation, accountability, and strategic thinking. You can search through their journal entries to track progress and patterns, and search the web for current strategies, research, and resources. Focus on action-oriented advice, progress tracking, and overcoming obstacles. Be direct but supportive, and always push for growth and improvement. When referencing search results, cite them appropriately.",
                    "icon": "🎯",
                },
                {
                    "id": "persona-storyteller",
                    "name": "Story Teller",
                    "description": "A creative companion for storytelling and narrative development",
                    "system_prompt": "You are a creative storytelling assistant with access to search tools. Help users craft compelling narratives, develop characters, and explore creative writing. You can search through their journal entries for story inspiration and past writing, and search the web for writing techniques, character development resources, and creative inspiration. Encourage imagination, provide plot suggestions, and assist with creative challenges. Be inspiring, artistic, and focused on the craft of storytelling. When referencing search results, cite them appropriately.",
                    "icon": "📚",
                },
                {
                    "id": "persona-therapist",
                    "name": "Therapist",
                    "description": "An empathetic listener focused on emotional support and understanding",
                    "system_prompt": "You are a compassionate therapeutic listener with access to search tools. Provide emotional support through active listening, validation, and gentle guidance. You can search through their journal entries to understand patterns and past experiences, and search the web for therapeutic techniques and emotional support resources when appropriate. Help users process their feelings and thoughts without judgment. Focus on understanding rather than fixing, and encourage self-discovery and emotional awareness. When referencing search results, cite them appropriately.",
                    "icon": "💙",
                },
                {
                    "id": "persona-productivity",
                    "name": "Productivity Partner",
                    "description": "An organized assistant focused on task management and efficiency",
                    "system_prompt": "You are a productivity-focused assistant with access to search tools. Help users organize their tasks, manage their time, and optimize their workflows. You can search through their journal entries to track productivity patterns and past approaches, and search the web for current productivity techniques, tools, and research. Provide practical advice on planning, prioritization, and efficiency. Be systematic, organized, and focused on achieving maximum productivity. When referencing search results, cite them appropriately.",
                    "icon": "⚡",
                },
            ]

            # Insert default personas
            now = datetime.now().isoformat()
            for persona_data in default_personas:
                cursor.execute(
                    """
                    INSERT INTO personas (
                        id, name, description, system_prompt, icon, is_default, created_at
                    ) VALUES (?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        persona_data["id"],
                        persona_data["name"],
                        persona_data["description"],
                        persona_data["system_prompt"],
                        persona_data["icon"],
                        now,
                    ),
                )

            conn.commit()
            logger.info(f"Seeded {len(default_personas)} default personas")

        except Exception as e:
            logger.error(f"Failed to seed default personas: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

    def _update_default_personas(self, cursor):
        """Update existing default personas with tool awareness."""
        # Define updated personas with tool awareness
        updated_personas = [
            {
                "id": "persona-journal",
                "system_prompt": "You are a thoughtful journaling assistant with access to search tools. Help users explore their thoughts, feelings, and experiences through gentle questioning and supportive reflection. You can search through their journal entries to find relevant past experiences and search the web for current information when needed. Encourage deeper self-awareness and provide writing prompts when helpful. Be empathetic, non-judgmental, and focused on personal growth. When referencing search results, cite them appropriately.",
            },
            {
                "id": "persona-coach",
                "system_prompt": "You are an encouraging life coach with access to search tools. Help users set and achieve their goals through motivation, accountability, and strategic thinking. You can search through their journal entries to track progress and patterns, and search the web for current strategies, research, and resources. Focus on action-oriented advice, progress tracking, and overcoming obstacles. Be direct but supportive, and always push for growth and improvement. When referencing search results, cite them appropriately.",
            },
            {
                "id": "persona-storyteller",
                "system_prompt": "You are a creative storytelling assistant with access to search tools. Help users craft compelling narratives, develop characters, and explore creative writing. You can search through their journal entries for story inspiration and past writing, and search the web for writing techniques, character development resources, and creative inspiration. Encourage imagination, provide plot suggestions, and assist with creative challenges. Be inspiring, artistic, and focused on the craft of storytelling. When referencing search results, cite them appropriately.",
            },
            {
                "id": "persona-therapist",
                "system_prompt": "You are a compassionate therapeutic listener with access to search tools. Provide emotional support through active listening, validation, and gentle guidance. You can search through their journal entries to understand patterns and past experiences, and search the web for therapeutic techniques and emotional support resources when appropriate. Help users process their feelings and thoughts without judgment. Focus on understanding rather than fixing, and encourage self-discovery and emotional awareness. When referencing search results, cite them appropriately.",
            },
            {
                "id": "persona-productivity",
                "system_prompt": "You are a productivity-focused assistant with access to search tools. Help users organize their tasks, manage their time, and optimize their workflows. You can search through their journal entries to track productivity patterns and past approaches, and search the web for current productivity techniques, tools, and research. Provide practical advice on planning, prioritization, and efficiency. Be systematic, organized, and focused on achieving maximum productivity. When referencing search results, cite them appropriately.",
            },
        ]

        # Update each persona
        now = datetime.now().isoformat()
        for persona_data in updated_personas:
            cursor.execute(
                "UPDATE personas SET system_prompt = ?, updated_at = ? WHERE id = ?",
                (persona_data["system_prompt"], now, persona_data["id"]),
            )

        logger.info("Updated default personas with tool awareness")

    def create_persona(self, persona_data: PersonaCreate) -> Persona:
        """
        Create a new persona.

        Args:
            persona_data: The PersonaCreate object with persona details

        Returns:
            The created Persona object
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Create Persona object
            persona = Persona(
                name=persona_data.name,
                description=persona_data.description,
                system_prompt=persona_data.system_prompt,
                icon=persona_data.icon,
                is_default=False,  # User-created personas are never default
            )

            # Insert into database
            cursor.execute(
                """
                INSERT INTO personas (
                    id, name, description, system_prompt, icon, is_default, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    persona.id,
                    persona.name,
                    persona.description,
                    persona.system_prompt,
                    persona.icon,
                    persona.is_default,
                    persona.created_at.isoformat(),
                ),
            )

            conn.commit()
            return persona

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create persona: {str(e)}")
            raise e
        finally:
            conn.close()

    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """
        Retrieve a persona by ID.

        Args:
            persona_id: The ID of the persona to retrieve

        Returns:
            Persona if found, None otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, name, description, system_prompt, icon, is_default,
                       created_at, updated_at
                FROM personas
                WHERE id = ?
                """,
                (persona_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Parse row data
            (
                id,
                name,
                description,
                system_prompt,
                icon,
                is_default,
                created_at,
                updated_at,
            ) = row

            return Persona(
                id=id,
                name=name,
                description=description,
                system_prompt=system_prompt,
                icon=icon,
                is_default=bool(is_default),
                created_at=datetime.fromisoformat(created_at),
                updated_at=datetime.fromisoformat(updated_at) if updated_at else None,
            )

        finally:
            conn.close()

    def list_personas(self, include_default: bool = True) -> List[Persona]:
        """
        List all personas.

        Args:
            include_default: Whether to include default personas

        Returns:
            List of Persona objects
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            if include_default:
                cursor.execute(
                    """
                    SELECT id, name, description, system_prompt, icon, is_default,
                           created_at, updated_at
                    FROM personas
                    ORDER BY is_default DESC, name ASC
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT id, name, description, system_prompt, icon, is_default,
                           created_at, updated_at
                    FROM personas
                    WHERE is_default = 0
                    ORDER BY name ASC
                    """
                )

            personas = []
            for row in cursor.fetchall():
                (
                    id,
                    name,
                    description,
                    system_prompt,
                    icon,
                    is_default,
                    created_at,
                    updated_at,
                ) = row

                personas.append(
                    Persona(
                        id=id,
                        name=name,
                        description=description,
                        system_prompt=system_prompt,
                        icon=icon,
                        is_default=bool(is_default),
                        created_at=datetime.fromisoformat(created_at),
                        updated_at=datetime.fromisoformat(updated_at)
                        if updated_at
                        else None,
                    )
                )

            return personas

        finally:
            conn.close()

    def update_persona(
        self, persona_id: str, updates: PersonaUpdate
    ) -> Optional[Persona]:
        """
        Update an existing persona.

        Args:
            persona_id: The ID of the persona to update
            updates: PersonaUpdate object with fields to update

        Returns:
            Updated Persona if successful, None if not found
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # First check if persona exists and is not default
            cursor.execute(
                "SELECT is_default FROM personas WHERE id = ?",
                (persona_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            is_default = bool(row[0])
            if is_default:
                raise ValueError("Cannot update default personas")

            # Build update query dynamically based on provided fields
            update_fields = []
            params = []

            if updates.name is not None:
                update_fields.append("name = ?")
                params.append(updates.name)

            if updates.description is not None:
                update_fields.append("description = ?")
                params.append(updates.description)

            if updates.system_prompt is not None:
                update_fields.append("system_prompt = ?")
                params.append(updates.system_prompt)

            if updates.icon is not None:
                update_fields.append("icon = ?")
                params.append(updates.icon)

            if not update_fields:
                # No fields to update
                return self.get_persona(persona_id)

            # Add updated_at timestamp
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())

            # Add persona_id for WHERE clause
            params.append(persona_id)

            # Execute update
            cursor.execute(
                f"UPDATE personas SET {', '.join(update_fields)} WHERE id = ?",
                params,
            )

            if cursor.rowcount == 0:
                return None

            conn.commit()
            return self.get_persona(persona_id)

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update persona: {str(e)}")
            raise e
        finally:
            conn.close()

    def delete_persona(self, persona_id: str) -> bool:
        """
        Delete a persona.

        Args:
            persona_id: The ID of the persona to delete

        Returns:
            True if successful, False if not found or is default
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if persona exists and is not default
            cursor.execute(
                "SELECT is_default FROM personas WHERE id = ?",
                (persona_id,),
            )
            row = cursor.fetchone()
            if not row:
                return False

            is_default = bool(row[0])
            if is_default:
                raise ValueError("Cannot delete default personas")

            # Delete the persona
            cursor.execute("DELETE FROM personas WHERE id = ?", (persona_id,))

            success = cursor.rowcount > 0
            conn.commit()
            return success

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete persona: {str(e)}")
            raise e
        finally:
            conn.close()

    def get_default_persona(self) -> Optional[Persona]:
        """
        Get the default journaling assistant persona.

        Returns:
            Default Persona object or None if not found
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, name, description, system_prompt, icon, is_default,
                       created_at, updated_at
                FROM personas
                WHERE id = 'persona-journal'
                LIMIT 1
                """,
            )

            row = cursor.fetchone()
            if not row:
                # Fallback to any default persona
                cursor.execute(
                    """
                    SELECT id, name, description, system_prompt, icon, is_default,
                           created_at, updated_at
                    FROM personas
                    WHERE is_default = 1
                    LIMIT 1
                    """,
                )
                row = cursor.fetchone()

            if not row:
                return None

            (
                id,
                name,
                description,
                system_prompt,
                icon,
                is_default,
                created_at,
                updated_at,
            ) = row

            return Persona(
                id=id,
                name=name,
                description=description,
                system_prompt=system_prompt,
                icon=icon,
                is_default=bool(is_default),
                created_at=datetime.fromisoformat(created_at),
                updated_at=datetime.fromisoformat(updated_at) if updated_at else None,
            )

        finally:
            conn.close()
