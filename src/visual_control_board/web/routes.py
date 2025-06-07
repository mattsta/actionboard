from fastapi import APIRouter, Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from visual_control_board.config.models import UIConfig, ButtonConfig, PageConfig, DynamicUpdateConfig, ActionsConfig
from visual_control_board.actions.registry import ActionRegistry
from visual_control_board.dependencies import get_ui_config, get_action_registry, get_pending_update_flag

logger = logging.getLogger(__name__)

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter()

# API Router for configuration management
config_router = APIRouter(prefix="/api/v1/config", tags=["Configuration Management"])

@config_router.post("/stage", status_code=202) # 202 Accepted
async def stage_new_configuration(
    request: Request,
    update_request: DynamicUpdateConfig
):
    """
    Stages a new UI and Actions configuration.
    The new configuration is validated (including action loadability) but not applied immediately.
    A notification banner will be shown in the UI to apply or discard.
    """
    logger.info("Received request to stage new configuration.")

    # Validate the new ActionsConfig by attempting to load actions into a temporary registry
    temp_action_registry = ActionRegistry()
    # Capture logs from the temporary registry loading process to check for errors
    # This is a simplified way; a more robust method might involve custom log handlers
    # or checking the number of successfully loaded actions against definitions.
    # For now, we assume `load_actions` logs errors for unresolvable actions.
    # A more direct validation would be to check `len(temp_action_registry._actions)`
    # against `len(update_request.actions_config.actions)`.
    
    # We need a way to check if temp_action_registry had issues.
    # One simple way: count actions before and after.
    # Or, `load_actions` could return a status or raise specific validation errors.
    # For now, let's assume Pydantic validation of ActionDefinition is the primary check for structure.
    # The dynamic import check is crucial.
    
    # Let's refine action validation:
    # The ActionRegistry's load_actions logs errors but doesn't explicitly return them.
    # We can count successfully loaded actions.
    initial_action_count = len(temp_action_registry._actions)
    temp_action_registry.load_actions(update_request.actions_config)
    loaded_action_count = len(temp_action_registry._actions)
    defined_action_count = len(update_request.actions_config.actions)

    if loaded_action_count != defined_action_count:
        # This implies some actions failed to load.
        # More detailed error reporting would require `load_actions` to return status/errors.
        error_msg = (
            f"Failed to stage new configuration: Not all actions could be loaded. "
            f"Defined: {defined_action_count}, Successfully Loaded: {loaded_action_count}. "
            "Check server logs for details on specific action loading errors."
        )
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    # If validation passes, store the new configurations in app.state
    request.app.state.staged_ui_config = update_request.ui_config
    request.app.state.staged_actions_config = update_request.actions_config
    request.app.state.pending_update_available = True
    logger.info("New configuration staged successfully.")

    # Return HTML for the update banner using an OOB swap
    banner_html = templates.get_template("partials/update_banner.html").render({
        "request": request,
        "pending_update_available": True
    })
    return HTMLResponse(content=banner_html)


@config_router.post("/apply")
async def apply_staged_configuration(request: Request, response: Response):
    """
    Applies the staged UI and Actions configuration, making it current.
    Triggers a full page refresh on the client.
    """
    logger.info("Received request to apply staged configuration.")
    if not request.app.state.pending_update_available or \
       request.app.state.staged_ui_config is None or \
       request.app.state.staged_actions_config is None:
        logger.warning("No staged configuration available to apply.")
        raise HTTPException(status_code=404, detail="No staged configuration found to apply.")

    # Apply the staged configurations
    request.app.state.current_ui_config = request.app.state.staged_ui_config
    request.app.state.current_actions_config = request.app.state.staged_actions_config
    
    # Re-initialize the action registry with the new actions config
    new_action_registry = ActionRegistry()
    new_action_registry.load_actions(request.app.state.current_actions_config)
    request.app.state.action_registry = new_action_registry
    logger.info("Action registry re-initialized with new configuration.")

    # Clear staged configurations and flag
    request.app.state.staged_ui_config = None
    request.app.state.staged_actions_config = None
    request.app.state.pending_update_available = False
    logger.info("Staged configuration applied and cleared.")

    # Instruct HTMX to do a full page refresh
    response.headers["HX-Refresh"] = "true"
    return {"message": "Configuration applied successfully. Page will refresh."} # JSON response, HX-Refresh handles UI


@config_router.post("/discard")
async def discard_staged_configuration(request: Request):
    """
    Discards any staged UI and Actions configuration.
    Updates the UI to remove the 'update available' banner.
    """
    logger.info("Received request to discard staged configuration.")
    request.app.state.staged_ui_config = None
    request.app.state.staged_actions_config = None
    request.app.state.pending_update_available = False
    logger.info("Staged configuration discarded.")

    # Return HTML for an empty/hidden update banner
    banner_html = templates.get_template("partials/update_banner.html").render({
        "request": request,
        "pending_update_available": False
    })
    return HTMLResponse(content=banner_html)


# Main UI routes
@router.get("/", response_class=HTMLResponse)
async def get_index_page(
    request: Request,
    ui_config: Optional[UIConfig] = Depends(get_ui_config), # Uses updated get_ui_config
    pending_update_available: bool = Depends(get_pending_update_flag)
):
    if not ui_config or not ui_config.pages:
        logger.warning("UI Configuration not found or no pages defined when serving index page.")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "page_title": "Error - Visual Control Board",
                "current_page": None,
                "error": "UI Configuration not found or is empty.",
                "pending_update_available": pending_update_available # Pass flag even on error page
            },
            status_code=500
        )
    
    current_page = ui_config.pages[0]
    logger.info(f"Serving index page with content from page: '{current_page.name}' (ID: {current_page.id})")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page_title": f"{current_page.name} - Visual Control Board",
            "current_page": current_page,
            "error": None,
            "pending_update_available": pending_update_available
        }
    )

@router.post("/action/{button_id}", response_class=HTMLResponse)
async def handle_button_action(
    request: Request,
    button_id: str,
    ui_config: Optional[UIConfig] = Depends(get_ui_config), # Uses updated get_ui_config
    action_registry: ActionRegistry = Depends(get_action_registry)
):
    if not ui_config:
        logger.critical(f"UI Configuration not available for button ID: {button_id}.")
        error_message = "Critical Error: UI Configuration not loaded."
        toast_html = templates.get_template("partials/toast.html").render({
            "request": request, "message": error_message, "toast_class": "toast show error"
        })
        return HTMLResponse(content=toast_html, status_code=500)

    found_config = ui_config.find_button_and_page(button_id)
    
    if not found_config:
        logger.warning(f"Button ID '{button_id}' not found in UI configuration.")
        error_message = f"Configuration error: Button ID '{button_id}' not found."
        toast_html = templates.get_template("partials/toast.html").render({
            "request": request,
            "message": error_message,
            "toast_class": "toast show error"
        })
        return HTMLResponse(content=toast_html)

    originating_page_config, button_config = found_config
    action_id = button_config.action_id
    action_params = button_config.action_params.model_dump()
    
    logger.info(f"Action for button ID: '{button_id}', Action ID: '{action_id}', Params: {action_params}")
    result = await action_registry.execute_action(action_id, params=action_params)
    logger.info(f"Action '{action_id}' for button '{button_id}' result: {result}")
    
    feedback_message = f"Action '{action_id}' completed."
    toast_class = "toast show"

    if isinstance(result, dict):
        if "error" in result or result.get("status") == "error":
            feedback_message = result.get("message", result.get("error", f"Error executing action '{action_id}'."))
            toast_class = "toast show error"
            logger.error(f"Action '{action_id}' for button '{button_id}' error: {feedback_message}")
        elif "message" in result:
            feedback_message = str(result["message"])
    elif isinstance(result, str) and result:
        feedback_message = result

    toast_html = templates.get_template("partials/toast.html").render({
        "request": request,
        "message_id": f"toast-message-content-{button_id}",
        "message": feedback_message,
        "toast_class": toast_class
    })
    button_html = templates.get_template("partials/button.html").render({
        "request": request,
        "button": button_config,
    })
    final_html_content = toast_html + button_html
    return HTMLResponse(content=final_html_content)

# Include the config_router in the main app router
router.include_router(config_router)
