from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from visual_control_board.config.models import UIConfig, ButtonConfig, PageConfig
from visual_control_board.actions.registry import ActionRegistry
from visual_control_board.dependencies import get_ui_config, get_action_registry

logger = logging.getLogger(__name__)

# Determine the templates directory relative to this file's location
# src/visual_control_board/web/routes.py -> src/visual_control_board/web/templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def get_index_page(
    request: Request,
    ui_config: Optional[UIConfig] = Depends(get_ui_config)
):
    """Serves the main index.html page."""
    if not ui_config or not ui_config.pages:
        logger.warning("UI Configuration not found or empty when serving index page.")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "page_title": "Error - Control Board",
                "current_page": None,
                "error": "UI Configuration not found or is empty. Please check server logs and configuration files."
            }
        )
    
    # For simplicity, use the first page defined. Multi-page navigation is a future enhancement.
    current_page = ui_config.pages[0]
    logger.info(f"Serving index page with content from page: '{current_page.name}' (ID: {current_page.id})")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page_title": current_page.name,
            "current_page": current_page,
        }
    )

@router.post("/action/{button_id}", response_class=HTMLResponse)
async def handle_button_action(
    request: Request,
    button_id: str,
    ui_config: Optional[UIConfig] = Depends(get_ui_config),
    action_registry: ActionRegistry = Depends(get_action_registry)
):
    """
    Handles a button click action.
    This endpoint is called by HTMX when a button is pressed.
    It returns HTML to re-render the button and an OOB swap for a toast message.
    """
    if not ui_config:
        logger.error(f"UI Configuration not available when handling action for button ID: {button_id}")
        # This case should ideally be prevented by startup checks in main.py
        raise HTTPException(status_code=500, detail="UI Configuration not loaded. Cannot process button action.")

    found_config = ui_config.find_button_and_page(button_id)
    
    if not found_config:
        logger.warning(f"Button with ID '{button_id}' not found in UI configuration.")
        # Return a 404 response that HTMX can handle, perhaps by showing an error toast.
        # For now, raising HTTPException which will be a JSON response unless an exception handler is added.
        # A more HTMX-friendly approach might be to return an error toast directly.
        raise HTTPException(status_code=404, detail=f"Button with ID '{button_id}' not found in UI configuration.")

    originating_page_config, button_config = found_config
    
    action_id = button_config.action_id
    # Ensure action_params is a dict, even if None or not present in config.
    # Pydantic model default_factory for ButtonActionParams handles this.
    action_params = button_config.action_params.model_dump() if button_config.action_params else {}
    
    logger.info(f"Received action for button ID: {button_id}, action ID: {action_id}, params: {action_params}")

    result = await action_registry.execute_action(action_id, params=action_params)

    logger.info(f"Action '{action_id}' for button '{button_id}' executed. Result: {result}")
    
    feedback_message = f"Action '{action_id}' completed." # Default message
    toast_class = "toast show" # Default success toast

    if isinstance(result, dict):
        if "error" in result:
            feedback_message = f"Error: {result['error']}"
            toast_class = "toast show error"
            logger.error(f"Action '{action_id}' for button '{button_id}' resulted in an error: {result['error']}")
        elif "message" in result:
            feedback_message = str(result["message"])
    elif isinstance(result, str) and result: # Non-empty string result
        feedback_message = result
    # If result is None or an empty string, the default "completed" message is used.

    # Prepare OOB swap for the toast message
    toast_html = templates.get_template("partials/toast.html").render({
        "request": request,
        "message_id": "toast-message-content", 
        "message": feedback_message,
        "toast_class": toast_class
    })

    # Prepare the main content: re-render the button that was actioned.
    button_html = templates.get_template("partials/button.html").render({
        "request": request,
        "button": button_config,
        # "current_page": originating_page_config # Not strictly needed by button.html currently
    })

    final_html_content = toast_html + button_html
    
    return HTMLResponse(content=final_html_content)

