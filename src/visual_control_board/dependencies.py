from fastapi import Request, HTTPException
from typing import Optional

from .config.models import UIConfig, ActionsConfig
from .actions.registry import ActionRegistry
import logging

logger = logging.getLogger(__name__)

def get_ui_config(request: Request) -> Optional[UIConfig]:
    """Dependency to get the loaded UI configuration."""
    ui_config = getattr(request.app.state, "ui_config", None)
    if ui_config is None:
        logger.error("UIConfig not found in application state. App may not have started correctly.")
        # Depending on strictness, you might raise HTTPException here
        # For now, allowing None to be returned, routes must handle it.
    return ui_config

def get_actions_config(request: Request) -> Optional[ActionsConfig]:
    """Dependency to get the loaded Actions configuration."""
    actions_config = getattr(request.app.state, "actions_config", None)
    if actions_config is None:
        logger.error("ActionsConfig not found in application state. App may not have started correctly.")
    return actions_config

def get_action_registry(request: Request) -> ActionRegistry:
    """Dependency to get the ActionRegistry instance."""
    action_registry = getattr(request.app.state, "action_registry", None)
    if action_registry is None:
        # This is a critical component. If it's missing, something is very wrong.
        logger.critical("ActionRegistry not found in application state. This indicates a severe startup issue.")
        raise HTTPException(status_code=500, detail="ActionRegistry not available. Application error.")
    return action_registry
