from typing import Optional

from app.storage.base import BaseStorage
from app.models import LLMConfig


class ConfigStorage(BaseStorage):
    """Handles storage and retrieval of configuration settings."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize configuration storage with database setup.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        super().__init__(base_dir)
        self._init_table()
        self._init_default_config()

    def _init_table(self):
        """Initialize config table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                max_retries INTEGER NOT NULL,
                retry_delay REAL NOT NULL,
                temperature REAL NOT NULL,
                max_tokens INTEGER NOT NULL,
                system_prompt TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def _init_default_config(self):
        """Initialize default LLM configuration if it doesn't exist."""
        if not self.get_llm_config():
            default_config = LLMConfig()
            self.save_llm_config(default_config)

    def save_llm_config(self, config: LLMConfig) -> bool:
        """
        Save LLM configuration settings.

        Args:
            config: The LLMConfig object to save

        Returns:
            True if successful, False otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO config VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    config.id,
                    config.model_name,
                    config.embedding_model,
                    config.max_retries,
                    config.retry_delay,
                    config.temperature,
                    config.max_tokens,
                    config.system_prompt,
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving LLM config: {e}")
            return False
        finally:
            conn.close()

    def get_llm_config(self, config_id: str = "default") -> Optional[LLMConfig]:
        """
        Retrieve LLM configuration settings.

        Args:
            config_id: The configuration ID to retrieve (defaults to "default")

        Returns:
            LLMConfig object if found, None otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    model_name, embedding_model, max_retries, retry_delay,
                    temperature, max_tokens, system_prompt
                FROM config WHERE id = ?
                """,
                (config_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            (
                model_name,
                embedding_model,
                max_retries,
                retry_delay,
                temperature,
                max_tokens,
                system_prompt,
            ) = row

            return LLMConfig(
                id=config_id,
                model_name=model_name,
                embedding_model=embedding_model,
                max_retries=max_retries,
                retry_delay=retry_delay,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
        finally:
            conn.close()
