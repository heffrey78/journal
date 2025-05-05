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
                system_prompt TEXT,
                min_similarity REAL DEFAULT 0.5
            )
            """
        )

        # Create prompt types table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prompt_types (
                id TEXT NOT NULL,
                config_id TEXT NOT NULL,
                name TEXT NOT NULL,
                prompt TEXT NOT NULL,
                PRIMARY KEY (id, config_id),
                FOREIGN KEY (config_id) REFERENCES config(id)
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
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Save main config
            cursor.execute(
                "INSERT OR REPLACE INTO config VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    config.id,
                    config.model_name,
                    config.embedding_model,
                    config.max_retries,
                    config.retry_delay,
                    config.temperature,
                    config.max_tokens,
                    config.system_prompt,
                    config.min_similarity,
                ),
            )

            # Handle prompt types
            logger.info(f"Saving prompt types for config {config.id}")

            # Delete existing prompt types for this config
            cursor.execute("DELETE FROM prompt_types WHERE config_id = ?", (config.id,))

            # Insert new prompt types
            if config.prompt_types:
                logger.info(f"Saving {len(config.prompt_types)} prompt types")
                for pt in config.prompt_types:
                    logger.info(f"Saving prompt type: {pt.id} - {pt.name}")
                    cursor.execute(
                        "INSERT INTO prompt_types (id, config_id, name, prompt) "
                        "VALUES (?, ?, ?, ?)",
                        (pt.id, config.id, pt.name, pt.prompt),
                    )

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving LLM config: {e}")
            conn.rollback()
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
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Get main config
            cursor.execute(
                """
                SELECT
                    model_name, embedding_model, max_retries, retry_delay,
                    temperature, max_tokens, system_prompt, min_similarity
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
                min_similarity,
            ) = row

            # Get prompt types for this config
            from app.models import PromptType

            cursor.execute(
                "SELECT id, name, prompt FROM prompt_types WHERE config_id = ?",
                (config_id,),
            )

            prompt_types = []
            for pt_row in cursor.fetchall():
                pt_id, pt_name, pt_prompt = pt_row
                logger.info(f"Retrieved prompt type: {pt_id} - {pt_name}")
                prompt_types.append(
                    PromptType(id=pt_id, name=pt_name, prompt=pt_prompt)
                )

            # Create the config with or without prompt types
            if not prompt_types:
                logger.info("No prompt types found, using defaults")
                config = LLMConfig(
                    id=config_id,
                    model_name=model_name,
                    embedding_model=embedding_model,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                    min_similarity=min_similarity
                    if min_similarity is not None
                    else 0.5,
                )
            else:
                logger.info(f"Found {len(prompt_types)} prompt types")
                config = LLMConfig(
                    id=config_id,
                    model_name=model_name,
                    embedding_model=embedding_model,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                    min_similarity=min_similarity
                    if min_similarity is not None
                    else 0.5,
                    prompt_types=prompt_types,
                )

            return config
        except Exception as e:
            logger.error(f"Error retrieving LLM config: {e}")
            return None
        finally:
            conn.close()
