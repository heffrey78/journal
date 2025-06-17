from typing import Optional

from app.storage.base import BaseStorage
from app.models import LLMConfig, WebSearchConfig


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
                search_model TEXT,
                chat_model TEXT,
                analysis_model TEXT,
                max_retries INTEGER NOT NULL,
                retry_delay REAL NOT NULL,
                temperature REAL NOT NULL,
                max_tokens INTEGER NOT NULL,
                system_prompt TEXT,
                min_similarity REAL DEFAULT 0.5
            )
            """
        )

        # Check and migrate existing table structure
        self._migrate_config_table(cursor)

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

        # Create web search config table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS web_search_config (
                id TEXT PRIMARY KEY,
                enabled BOOLEAN NOT NULL DEFAULT 1,
                max_searches_per_minute INTEGER NOT NULL DEFAULT 10,
                max_results_per_search INTEGER NOT NULL DEFAULT 5,
                default_region TEXT NOT NULL DEFAULT 'wt-wt',
                cache_duration_hours INTEGER NOT NULL DEFAULT 1,
                enable_news_search BOOLEAN NOT NULL DEFAULT 1,
                max_snippet_length INTEGER NOT NULL DEFAULT 200
            )
            """
        )

        conn.commit()
        conn.close()

    def _migrate_config_table(self, cursor):
        """Migrate config table to add new model fields if they don't exist."""
        # Get current table structure
        cursor.execute("PRAGMA table_info(config)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add missing columns
        new_columns = {
            "search_model": "TEXT",
            "chat_model": "TEXT",
            "analysis_model": "TEXT",
        }

        for column_name, column_type in new_columns.items():
            if column_name not in columns:
                try:
                    cursor.execute(
                        f"ALTER TABLE config ADD COLUMN {column_name} {column_type}"
                    )
                    print(f"Added column {column_name} to config table")
                except Exception as e:
                    # Column might already exist, or other error
                    print(f"Could not add column {column_name}: {e}")

    def _init_default_config(self):
        """Initialize default LLM and web search configurations if they don't exist."""
        if not self.get_llm_config():
            default_config = LLMConfig()
            self.save_llm_config(default_config)

        if not self.get_web_search_config():
            default_web_search_config = WebSearchConfig()
            self.save_web_search_config(default_web_search_config)

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
            # Save main config with explicit column names to handle column order correctly
            cursor.execute(
                """INSERT OR REPLACE INTO config
                (id, model_name, embedding_model, search_model, chat_model, analysis_model,
                 max_retries, retry_delay, temperature, max_tokens, system_prompt, min_similarity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    config.id,
                    config.model_name,
                    config.embedding_model,
                    config.search_model,
                    config.chat_model,
                    config.analysis_model,
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
            # Get main config with explicit column order
            cursor.execute(
                """
                SELECT
                    model_name, embedding_model, max_retries, retry_delay, temperature, max_tokens,
                    system_prompt, min_similarity, search_model, chat_model, analysis_model
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
                search_model,
                chat_model,
                analysis_model,
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
                    search_model=search_model,
                    chat_model=chat_model,
                    analysis_model=analysis_model,
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
                    search_model=search_model,
                    chat_model=chat_model,
                    analysis_model=analysis_model,
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

    def save_web_search_config(self, config: WebSearchConfig) -> bool:
        """
        Save web search configuration settings.

        Args:
            config: The WebSearchConfig object to save

        Returns:
            True if successful, False otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        import logging

        logger = logging.getLogger(__name__)

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO web_search_config
                (id, enabled, max_searches_per_minute, max_results_per_search,
                 default_region, cache_duration_hours, enable_news_search, max_snippet_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    config.id,
                    config.enabled,
                    config.max_searches_per_minute,
                    config.max_results_per_search,
                    config.default_region,
                    config.cache_duration_hours,
                    config.enable_news_search,
                    config.max_snippet_length,
                ),
            )

            conn.commit()
            logger.info(f"Saved web search config: {config.id}")
            return True
        except Exception as e:
            logger.error(f"Error saving web search config: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_web_search_config(
        self, config_id: str = "default"
    ) -> Optional[WebSearchConfig]:
        """
        Retrieve web search configuration settings.

        Args:
            config_id: The configuration ID to retrieve (defaults to "default")

        Returns:
            WebSearchConfig object if found, None otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        import logging

        logger = logging.getLogger(__name__)

        try:
            cursor.execute(
                """
                SELECT enabled, max_searches_per_minute, max_results_per_search,
                       default_region, cache_duration_hours, enable_news_search, max_snippet_length
                FROM web_search_config WHERE id = ?
                """,
                (config_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            (
                enabled,
                max_searches_per_minute,
                max_results_per_search,
                default_region,
                cache_duration_hours,
                enable_news_search,
                max_snippet_length,
            ) = row

            config = WebSearchConfig(
                id=config_id,
                enabled=bool(enabled),
                max_searches_per_minute=max_searches_per_minute,
                max_results_per_search=max_results_per_search,
                default_region=default_region,
                cache_duration_hours=cache_duration_hours,
                enable_news_search=bool(enable_news_search),
                max_snippet_length=max_snippet_length,
            )

            return config
        except Exception as e:
            logger.error(f"Error retrieving web search config: {e}")
            return None
        finally:
            conn.close()
