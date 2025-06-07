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
        raise HTTPException(status_code=500, detail="UI Configuration not loaded. Cannot process button action.")

    button_config: Optional[ButtonConfig] = None
    originating_page_config: Optional[PageConfig] = None
    for page in ui_config.pages:
        for btn in page.buttons:
            if btn.id == button_id:
                button_config = btn
                originating_page_config = page
                break
        if button_config:
            break
    
    if not button_config or not originating_page_config:
        logger.warning(f"Button with ID '{button_id}' not found in UI configuration.")
        raise HTTPException(status_code=404, detail=f"Button with ID '{button_id}' not found in UI configuration.")

    action_id = button_config.action_id
    action_params = button_config.action_params or {}
    
    logger.info(f"Received action for button ID: {button_id}, action ID: {action_id}, params: {action_params}")

    result = await action_registry.execute_action(action_id, params=action_params)

    logger.info(f"Action '{action_id}' for button '{button_id}' executed. Result: {result}")
    
    feedback_message = f"Action '{action_id}' triggered."
    toast_class = "toast show" # Default success toast

    if isinstance(result, dict):
        if "error" in result:
            feedback_message = f"Error: {result['error']}"
            toast_class = "toast show error" # Add an error class for styling
            logger.error(f"Action '{action_id}' for button '{button_id}' resulted in an error: {result['error']}")
        elif "message" in result:
            feedback_message = str(result["message"])
    elif isinstance(result, str): # Simple string result
        feedback_message = result
    elif result is None: # Action might not return anything meaningful for UI
        feedback_message = f"Action '{action_id}' completed."


    # Prepare OOB swap for the toast message
    # Ensure toast_message id is unique if multiple toasts can appear, or it's always replaced.
    # Current setup replaces #toast-message content.
    toast_html = templates.get_template("partials/toast.html").render({
        "request": request, # Pass request for url_for if needed in toast, not currently used
        "message_id": "toast-message-content", # ID for the content part of the toast
        "message": feedback_message,
        "toast_class": toast_class
    })


    # Prepare the main content: re-render the button that was actioned.
    button_html = templates.get_template("partials/button.html").render({
        "request": request,
        "button": button_config,
        "current_page": originating_page_config 
    })

    final_html_content = toast_html + button_html
    
    return HTMLResponse(content=final_html_content)

