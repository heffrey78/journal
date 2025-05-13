"""
Extension for ChatSession model to include model-specific configuration.
"""

from pydantic import BaseModel
from typing import Optional


class SessionModelConfig(BaseModel):
    """
    Model-specific configuration for a chat session.

    Attributes:
        model_name: Name of the LLM model to use for this session
    """

    model_name: Optional[str] = None
