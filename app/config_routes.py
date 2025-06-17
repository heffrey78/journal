"""
API endpoints for configuration settings.
"""

from fastapi import APIRouter, HTTPException, Depends
import logging
from typing import List, Dict, Any

from app.llm_service import LLMService
from app.utils import get_llm_service, get_storage
from app.models import WebSearchConfig

logger = logging.getLogger(__name__)

config_router = APIRouter(prefix="/config", tags=["Configuration"])


@config_router.get("/llm")
async def get_llm_config(
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    Get the current LLM configuration.

    Returns:
        Dictionary with LLM configuration settings
    """
    try:
        # Return the current configuration from the LLM service
        config = llm_service.get_config()
        return config
    except Exception as e:
        logger.error(f"Failed to get LLM config: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get LLM configuration: {str(e)}"
        )


@config_router.get("/available-models")
async def get_available_models(
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, List[str]]:
    """
    Get the list of available LLM models that can be used.

    Returns:
        Dictionary with a list of available model names
    """
    try:
        # Get available models from the LLM service
        models = llm_service.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to get available models: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get available models: {str(e)}"
        )


@config_router.get("/web-search", response_model=WebSearchConfig)
async def get_web_search_config(
    storage=Depends(get_storage),
) -> WebSearchConfig:
    """
    Get the current web search configuration.

    Returns:
        WebSearchConfig object with current settings
    """
    try:
        config = storage.config.get_web_search_config()
        if not config:
            # Return default config if none exists
            config = WebSearchConfig()
        return config
    except Exception as e:
        logger.error(f"Failed to get web search config: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get web search configuration: {str(e)}"
        )


@config_router.put("/web-search", response_model=WebSearchConfig)
async def update_web_search_config(
    config: WebSearchConfig,
    storage=Depends(get_storage),
) -> WebSearchConfig:
    """
    Update the web search configuration.

    Args:
        config: New web search configuration settings

    Returns:
        Updated WebSearchConfig object
    """
    try:
        success = storage.config.save_web_search_config(config)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to save web search configuration"
            )

        logger.info(f"Updated web search config: enabled={config.enabled}")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update web search config: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update web search configuration: {str(e)}",
        )
