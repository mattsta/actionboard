from fastapi import Request, HTTPException
from typing import Optional
import logging

from .config.models import UIConfig, ActionsConfig
from .actions.registry import ActionRegistry

logger = logging.getLogger(__name__)

def get_current_ui_config(request: Request) -> Optional[UIConfig]:
    """
    FastAPI dependency to retrieve the *currently active* UIConfig from application state.
    """
    ui_config: Optional[UIConfig] = getattr(request.app.state, "current_ui_config", None)
    if ui_config is None:
        logger.error("Current UIConfig not found in application state. This indicates a severe issue.")
        # This should ideally not happen if startup sequence is robust.
        # Raising an error as the UI would be non-functional.
        raise HTTPException(status_code=503, detail="UI configuration is currently unavailable.")
    return ui_config

def get_current_actions_config(request: Request) -> Optional[ActionsConfig]:
    """
    FastAPI dependency to retrieve the *currently active* ActionsConfig from application state.
    """
    actions_config: Optional[ActionsConfig] = getattr(request.app.state, "current_actions_config", None)
    if actions_config is None:
        logger.error("Current ActionsConfig not found in application state.")
        # This is critical for action execution.
        raise HTTPException(status_code=503, detail="Actions configuration is currently unavailable.")
    return actions_config

def get_action_registry(request: Request) -> ActionRegistry:
    """
    FastAPI dependency to retrieve the ActionRegistry instance (based on current_actions_config).
    """
    action_registry: Optional[ActionRegistry] = getattr(request.app.state, "action_registry", None)
    if action_registry is None:
        logger.critical("ActionRegistry not found in application state. This indicates a severe startup issue or misconfiguration.")
        raise HTTPException(
            status_code=500, 
            detail="ActionRegistry is not available due to an internal server error."
        )
    return action_registry

def get_pending_update_flag(request: Request) -> bool:
    """
    FastAPI dependency to retrieve the flag indicating if a configuration update is pending.
    """
    return getattr(request.app.state, "pending_update_available", False)

# Renaming old dependencies for clarity, will update their usage in routes.py
get_ui_config = get_current_ui_config 
get_actions_config = get_current_actions_config
