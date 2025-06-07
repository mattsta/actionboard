from fastapi import Request, HTTPException
from typing import Optional
import logging

# Import models for type hinting app.state attributes
from .config.models import UIConfig, ActionsConfig
from .actions.registry import ActionRegistry

logger = logging.getLogger(__name__)

def get_ui_config(request: Request) -> Optional[UIConfig]:
    """
    FastAPI dependency to retrieve the loaded UIConfig from application state.
    
    The UIConfig is loaded during application startup and stored in `request.app.state.ui_config`.
    Returns:
        The UIConfig instance if found, otherwise None. Routes using this dependency
        should handle the case where UIConfig might be None (e.g., if startup failed partially,
        though `main.py` aims to prevent startup on critical config failures).
    """
    ui_config: Optional[UIConfig] = getattr(request.app.state, "ui_config", None)
    if ui_config is None:
        # This situation should ideally be rare if startup checks in main.py are effective.
        logger.error("UIConfig not found in application state. This might indicate an incomplete or failed application startup.")
        # Depending on the strictness required by a route, it might raise HTTPException here.
        # For now, allowing None to be returned; routes must be robust.
    return ui_config

def get_actions_config(request: Request) -> Optional[ActionsConfig]:
    """
    FastAPI dependency to retrieve the loaded ActionsConfig from application state.
    
    The ActionsConfig is loaded during application startup and stored in `request.app.state.actions_config`.
    Returns:
        The ActionsConfig instance if found, otherwise None.
    """
    actions_config: Optional[ActionsConfig] = getattr(request.app.state, "actions_config", None)
    if actions_config is None:
        logger.error("ActionsConfig not found in application state. This might indicate an incomplete or failed application startup.")
    return actions_config

def get_action_registry(request: Request) -> ActionRegistry:
    """
    FastAPI dependency to retrieve the ActionRegistry instance from application state.
    
    The ActionRegistry is initialized and populated during application startup and stored in
    `request.app.state.action_registry`.
    Returns:
        The ActionRegistry instance.
    Raises:
        HTTPException (500 Internal Server Error): If the ActionRegistry is not found,
        as this is a critical component for the application's functionality.
    """
    action_registry: Optional[ActionRegistry] = getattr(request.app.state, "action_registry", None)
    if action_registry is None:
        # This is a critical component. If it's missing, the application is in a severely broken state.
        logger.critical("ActionRegistry not found in application state. This indicates a severe startup issue or misconfiguration.")
        raise HTTPException(
            status_code=500, 
            detail="ActionRegistry is not available due to an internal server error. The application may not have started correctly."
        )
    return action_registry
