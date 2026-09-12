from typing import List, Optional, Union
from fastapi import Depends, Request
from pydantic import BaseModel
from loguru import logger

from app.config import config
from app.controllers import base
from app.controllers.v1.base import new_router
from app.utils import utils

router = new_router(dependencies=[Depends(base.verify_token)])


class ConfigSyncRequest(BaseModel):
    llm_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model_name: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model_name: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: Optional[str] = None
    anthropic_model_name: Optional[str] = None
    pexels_api_keys: Optional[Union[List[str], str]] = None
    pixabay_api_keys: Optional[Union[List[str], str]] = None


@router.get("/config/sync", summary="Get status of configured engine providers and keys")
def get_config_sync_status(request: Request):
    return utils.get_response(
        200,
        {
            "llm_provider": config.app.get("llm_provider", ""),
            "gemini_model_name": config.app.get("gemini_model_name", ""),
            "has_gemini_key": bool(config.app.get("gemini_api_key", "").strip()),
            "has_openai_key": bool(config.app.get("openai_api_key", "").strip()),
            "has_anthropic_key": bool(config.app.get("anthropic_api_key", "").strip()),
            "has_pexels_key": bool(config.app.get("pexels_api_keys")),
            "has_pixabay_key": bool(config.app.get("pixabay_api_keys")),
        },
        "ok",
    )


@router.post("/config/sync", summary="Synchronize frontend credentials to engine config")
def sync_engine_config(req: ConfigSyncRequest, request: Request):
    updated = {}

    if req.llm_provider is not None:
        val = req.llm_provider.strip().lower()
        if val:
            config.app["llm_provider"] = val
            updated["llm_provider"] = val

    if req.gemini_api_key is not None:
        config.app["gemini_api_key"] = req.gemini_api_key.strip()
        updated["gemini_api_key"] = bool(config.app["gemini_api_key"])

    if req.gemini_model_name is not None:
        config.app["gemini_model_name"] = req.gemini_model_name.strip()
        updated["gemini_model_name"] = config.app["gemini_model_name"]
    elif config.app.get("llm_provider") == "gemini" and not config.app.get("gemini_model_name"):
        config.app["gemini_model_name"] = "gemini-3.6-flash"

    if req.openai_api_key is not None:
        config.app["openai_api_key"] = req.openai_api_key.strip()
        updated["openai_api_key"] = bool(config.app["openai_api_key"])

    if req.openai_base_url is not None:
        config.app["openai_base_url"] = req.openai_base_url.strip()

    if req.openai_model_name is not None:
        config.app["openai_model_name"] = req.openai_model_name.strip()

    if req.anthropic_api_key is not None:
        config.app["anthropic_api_key"] = req.anthropic_api_key.strip()
        updated["anthropic_api_key"] = bool(config.app["anthropic_api_key"])

    if req.anthropic_base_url is not None:
        config.app["anthropic_base_url"] = req.anthropic_base_url.strip()

    if req.anthropic_model_name is not None:
        config.app["anthropic_model_name"] = req.anthropic_model_name.strip()

    if req.pexels_api_keys is not None:
        if isinstance(req.pexels_api_keys, str):
            keys = [k.strip() for k in req.pexels_api_keys.split(",") if k.strip()]
        else:
            keys = [k.strip() for k in req.pexels_api_keys if k and k.strip()]
        config.app["pexels_api_keys"] = keys
        updated["pexels_api_keys"] = len(keys)

    if req.pixabay_api_keys is not None:
        if isinstance(req.pixabay_api_keys, str):
            keys = [k.strip() for k in req.pixabay_api_keys.split(",") if k.strip()]
        else:
            keys = [k.strip() for k in req.pixabay_api_keys if k and k.strip()]
        config.app["pixabay_api_keys"] = keys
        updated["pixabay_api_keys"] = len(keys)

    try:
        config.save_config()
        logger.info(f"Engine config synchronized successfully: {list(updated.keys())}")
    except Exception as e:
        logger.error(f"Failed to persist engine config to disk: {str(e)}")

    return utils.get_response(
        200,
        {
            "updated": updated,
            "llm_provider": config.app.get("llm_provider", ""),
            "has_gemini_key": bool(config.app.get("gemini_api_key", "").strip()),
            "has_pexels_key": bool(config.app.get("pexels_api_keys")),
        },
        "Engine config synchronized successfully",
    )
