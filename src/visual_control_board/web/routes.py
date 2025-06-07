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
# e.g., src/visual_control_board/web/routes.py -> src/visual_control_board/web/templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def get_index_page(
    request: Request,
    ui_config: Optional[UIConfig] = Depends(get_ui_config)
):
    """
    Serves the main index.html page.
    The content of the page (specifically, the buttons displayed) is determined by
    the loaded UI configuration. Currently, it displays the first page defined in the config.
    """
    if not ui_config or not ui_config.pages:
        logger.warning("UI Configuration not found or no pages defined when serving index page.")
        # Render the index page with an error message if UI config is missing or empty.
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "page_title": "Error - Visual Control Board",
                "current_page": None, # No current page to display
                "error": "UI Configuration not found or is empty. Please check server logs and configuration files (e.g., user_config/ui_config.yaml or config_examples/ui_config.yaml)."
            },
            status_code=500 # Internal server error, as config is crucial
        )
    
    # For simplicity in this version, always use the first page defined in the UIConfig.
    # Future enhancements could include multi-page navigation.
    current_page = ui_config.pages[0]
    logger.info(f"Serving index page with content from page: '{current_page.name}' (ID: {current_page.id})")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page_title": f"{current_page.name} - Visual Control Board",
            "current_page": current_page,
            "error": None # No error
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
    Handles a button click action triggered by an HTMX POST request.
    
    This endpoint:
    1. Finds the button configuration using `button_id`.
    2. Retrieves the associated `action_id` and `action_params`.
    3. Executes the action using the `ActionRegistry`.
    4. Returns an HTML response that typically includes:
       - Re-rendered HTML for the button itself (for `hx-swap="outerHTML"`).
       - An Out-of-Band (OOB) swapped HTML snippet for a toast notification
         to provide feedback on the action's result.
    
    If the button configuration is not found, it returns an OOB error toast.
    """
    if not ui_config:
        # This should ideally be prevented by startup checks in main.py,
        # but as a safeguard:
        logger.critical(f"UI Configuration not available when handling action for button ID: {button_id}. This is a severe error.")
        # Return an OOB error toast if possible, though the system might be in a bad state.
        error_message = "Critical Error: UI Configuration not loaded. Cannot process button action."
        toast_html = templates.get_template("partials/toast.html").render({
            "request": request, "message": error_message, "toast_class": "toast show error"
        })
        return HTMLResponse(content=toast_html, status_code=500)

    # Find the button configuration within the loaded UIConfig
    found_config = ui_config.find_button_and_page(button_id)
    
    if not found_config:
        logger.warning(f"Button with ID '{button_id}' not found in UI configuration. Action cannot be performed.")
        # User error: button ID from client does not match any known button.
        # Return an OOB error toast. The button that was clicked remains unchanged on the page.
        error_message = f"Configuration error: Button ID '{button_id}' not found."
        toast_html = templates.get_template("partials/toast.html").render({
            "request": request,
            "message": error_message,
            "toast_class": "toast show error"
        })
        # Return 200 OK so HTMX processes the OOB swap for the toast.
        # The main target (the button) won't be updated as we don't send its HTML.
        return HTMLResponse(content=toast_html)

    originating_page_config, button_config = found_config
    
    action_id = button_config.action_id
    # action_params is a Pydantic model (ButtonActionParams), convert to dict for passing to action function.
    # The default_factory ensures action_params is always an instance, so model_dump() is safe.
    action_params = button_config.action_params.model_dump()
    
    logger.info(f"Received action for button ID: '{button_id}' on page '{originating_page_config.name}'. Action ID: '{action_id}', Params: {action_params if action_params else 'None'}")

    # Execute the action via the registry
    result = await action_registry.execute_action(action_id, params=action_params)

    logger.info(f"Action '{action_id}' for button '{button_id}' executed. Raw result: {result}")
    
    # Determine feedback message and toast style based on action result
    feedback_message = f"Action '{action_id}' completed." # Default success message
    toast_class = "toast show" # Default success toast style

    if isinstance(result, dict):
        if "error" in result or result.get("status") == "error":
            # If the action itself returned an error structure
            feedback_message = result.get("message", result.get("error", f"Error executing action '{action_id}'."))
            toast_class = "toast show error"
            logger.error(f"Action '{action_id}' for button '{button_id}' reported an error: {feedback_message}")
        elif "message" in result:
            # If the action returned a specific message
            feedback_message = str(result["message"])
    elif isinstance(result, str) and result: # If action returns a non-empty string
        feedback_message = result
    # If result is None, an empty string, or an unhandled dict structure, the default "completed" message is used.

    # Prepare OOB swap for the toast message
    # The toast.html partial expects 'message_id', 'message', 'toast_class'.
    toast_html = templates.get_template("partials/toast.html").render({
        "request": request,
        "message_id": f"toast-message-content-{button_id}", # Unique ID for content span if needed
        "message": feedback_message,
        "toast_class": toast_class
    })

    # Prepare the main content: re-render the button that was actioned.
    # This allows the button's appearance to be updated if the action modified its state
    # (though current ButtonConfig doesn't store state that changes post-action directly).
    # button.html expects 'button' and 'request'.
    button_html = templates.get_template("partials/button.html").render({
        "request": request,
        "button": button_config,
        # "current_page": originating_page_config # Not strictly needed by button.html currently
    })

    # Combine the OOB toast HTML with the main button HTML.
    # HTMX will process these: the button_html swaps the target, toast_html is OOB.
    final_html_content = toast_html + button_html
    
    return HTMLResponse(content=final_html_content)

