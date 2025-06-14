from fastapi import Request, HTTPException, WebSocket
from typing import Optional
import logging

from .config.models import UIConfig, ActionsConfig
from .actions.registry import ActionRegistry
from .live_updates import LiveUpdateManager

logger = logging.getLogger(__name__)


def get_current_ui_config(request: Request) -> Optional[UIConfig]:
    """
    FastAPI dependency to retrieve the *currently active* UIConfig from application state.
    """
    ui_config: Optional[UIConfig] = getattr(
        request.app.state, "current_ui_config", None
    )
    if ui_config is None:
        logger.error(
            "Current UIConfig not found in application state. This indicates a severe issue."
        )
        raise HTTPException(
            status_code=503, detail="UI configuration is currently unavailable."
        )
    return ui_config


def get_current_actions_config(request: Request) -> Optional[ActionsConfig]:
    """
    FastAPI dependency to retrieve the *currently active* ActionsConfig from application state.
    """
    actions_config: Optional[ActionsConfig] = getattr(
        request.app.state, "current_actions_config", None
    )
    if actions_config is None:
        logger.error("Current ActionsConfig not found in application state.")
        raise HTTPException(
            status_code=503, detail="Actions configuration is currently unavailable."
        )
    return actions_config


def get_action_registry(request: Request) -> ActionRegistry:
    """
    FastAPI dependency to retrieve the ActionRegistry instance (based on current_actions_config).
    """
    action_registry: Optional[ActionRegistry] = getattr(
        request.app.state, "action_registry", None
    )
    if action_registry is None:
        logger.critical(
            "ActionRegistry not found in application state. This indicates a severe startup issue or misconfiguration."
        )
        raise HTTPException(
            status_code=500,
            detail="ActionRegistry is not available due to an internal server error.",
        )
    return action_registry


def get_pending_update_flag(request: Request) -> bool:
    """
    FastAPI dependency to retrieve the flag indicating if a configuration update is pending.
    """
    return getattr(request.app.state, "pending_update_available", False)


def get_live_update_manager(request: Request) -> LiveUpdateManager:
    """
    FastAPI dependency to retrieve the LiveUpdateManager instance from application state
    for HTTP routes.
    """
    manager: Optional[LiveUpdateManager] = getattr(
        request.app.state, "live_update_manager", None
    )
    if manager is None:
        logger.critical(
            "LiveUpdateManager not found in application state (HTTP context). This indicates a severe startup issue."
        )
        raise HTTPException(
            status_code=500,
            detail="LiveUpdateManager is not available due to an internal server error.",
        )
    return manager


def get_live_update_manager_ws(websocket: WebSocket) -> LiveUpdateManager:
    """
    FastAPI dependency to retrieve the LiveUpdateManager instance from application state
    for WebSocket routes.
    """
    manager: Optional[LiveUpdateManager] = getattr(
        websocket.app.state, "live_update_manager", None
    )
    if manager is None:
        # If this dependency fails, FastAPI will typically close the WebSocket connection
        # with an error code (e.g., 1011 for server error, or 403 if HTTPException is raised before accept).
        logger.critical(
            "LiveUpdateManager not found in application state (WebSocket context). This indicates a severe startup issue."
        )
        # Raising HTTPException here might result in a 403 response before handshake completes,
        # which client interprets as "bad response". This is acceptable for a critical setup error.
        raise HTTPException(
            status_code=500,  # Internal Server Error
            detail="LiveUpdateManager is not available due to an internal server error.",
        )
    return manager


# Renaming old dependencies for clarity, will update their usage in routes.py
get_ui_config = get_current_ui_config
get_actions_config = get_current_actions_config
