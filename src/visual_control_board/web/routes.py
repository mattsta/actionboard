from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    Depends,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import json  # For WebSocket message parsing if needed, though send_json/receive_json handle it

from visual_control_board.config.models import (
    UIConfig,
    ButtonConfig,
    PageConfig,
    DynamicUpdateConfig,
    ActionsConfig,
    ButtonContentUpdate,
)
from visual_control_board.actions.registry import ActionRegistry
from visual_control_board.dependencies import (
    get_ui_config,
    get_action_registry,
    get_pending_update_flag,
    get_live_update_manager,
    get_live_update_manager_ws,  # Import the new WebSocket-specific dependency
)
from visual_control_board.live_updates import LiveUpdateManager


logger = logging.getLogger(__name__)

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter()

# API Router for configuration management
config_router = APIRouter(prefix="/api/v1/config", tags=["Configuration Management"])


@config_router.post("/stage", status_code=202)  # 202 Accepted
async def stage_new_configuration(
    request: Request, update_request: DynamicUpdateConfig
):
    logger.info("Received request to stage new configuration.")
    temp_action_registry = ActionRegistry()
    temp_action_registry.load_actions(update_request.actions_config)
    loaded_action_count = len(temp_action_registry._actions)
    defined_action_count = len(update_request.actions_config.actions)

    if loaded_action_count != defined_action_count:
        error_msg = (
            f"Failed to stage new configuration: Not all actions could be loaded. "
            f"Defined: {defined_action_count}, Successfully Loaded: {loaded_action_count}. "
            "Check server logs for details on specific action loading errors."
        )
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    request.app.state.staged_ui_config = update_request.ui_config
    request.app.state.staged_actions_config = update_request.actions_config
    request.app.state.pending_update_available = True
    logger.info("New configuration staged successfully.")

    banner_html = templates.get_template("partials/update_banner.html").render(
        {"request": request, "pending_update_available": True}
    )
    return HTMLResponse(content=banner_html)


@config_router.post("/apply")
async def apply_staged_configuration(
    request: Request,
    response: Response,
    live_update_mgr: LiveUpdateManager = Depends(
        get_live_update_manager
    ),  # Added dependency
):
    logger.info("Received request to apply staged configuration.")
    if (
        not request.app.state.pending_update_available
        or request.app.state.staged_ui_config is None
        or request.app.state.staged_actions_config is None
    ):
        logger.warning("No staged configuration available to apply.")
        raise HTTPException(
            status_code=404, detail="No staged configuration found to apply."
        )

    request.app.state.current_ui_config = request.app.state.staged_ui_config
    request.app.state.current_actions_config = request.app.state.staged_actions_config

    new_action_registry = ActionRegistry()
    new_action_registry.load_actions(request.app.state.current_actions_config)
    request.app.state.action_registry = new_action_registry
    logger.info("Action registry re-initialized with new configuration.")

    request.app.state.staged_ui_config = None
    request.app.state.staged_actions_config = None
    request.app.state.pending_update_available = False
    logger.info("Staged configuration applied and cleared.")

    # Broadcast navigation update to all connected WebSocket clients
    # This tells them to refresh their navigation panel.
    await live_update_mgr.broadcast_json({"type": "navigation_update", "payload": {}})
    logger.info("Broadcasted navigation_update message to WebSocket clients.")

    # For the client that initiated this action (e.g., by clicking "Apply Update" button),
    # trigger a full page refresh. Other clients will handle the WebSocket message.
    response.headers["HX-Refresh"] = "true"
    return {"message": "Configuration applied successfully. Page will refresh."}


@config_router.post("/discard")
async def discard_staged_configuration(request: Request):
    logger.info("Received request to discard staged configuration.")
    request.app.state.staged_ui_config = None
    request.app.state.staged_actions_config = None
    request.app.state.pending_update_available = False
    logger.info("Staged configuration discarded.")

    banner_html = templates.get_template("partials/update_banner.html").render(
        {"request": request, "pending_update_available": False}
    )
    return HTMLResponse(content=banner_html)


# API Router for live button content updates
live_updates_router = APIRouter(prefix="/api/v1/buttons", tags=["Live Button Updates"])


@live_updates_router.post("/update_content", status_code=200)
async def push_button_content_update(
    update_data: ButtonContentUpdate,
    live_update_mgr: LiveUpdateManager = Depends(
        get_live_update_manager
    ),  # Uses the HTTP-compatible dependency
):
    """
    Receives a request to update a button's content and broadcasts it via WebSocket.
    """
    logger.info(
        f"Received request to update content for button_id: {update_data.button_id}"
    )

    await live_update_mgr.broadcast_button_update(
        update_data.model_dump(exclude_none=True)
    )
    return {
        "message": "Button content update broadcasted.",
        "button_id": update_data.button_id,
    }


# WebSocket endpoint
@router.websocket("/ws/button_updates")
async def websocket_button_updates_endpoint(
    websocket: WebSocket,
    live_update_mgr: LiveUpdateManager = Depends(
        get_live_update_manager_ws
    ),  # Use the WebSocket-compatible dependency
):
    """
    WebSocket endpoint for clients to receive live button content updates and other UI events.
    """
    await live_update_mgr.connect(
        websocket
    )  # This internally calls await websocket.accept()
    try:
        while True:
            # Keep the connection alive. Clients primarily receive data.
            # This will block until a message is received or the connection is closed by the client.
            await websocket.receive_text()
            # If you expect messages from the client, process them here.
            # For now, any text received is just logged as a keep-alive or unexpected message.
            logger.debug(
                f"Received keep-alive or unexpected message from {websocket.client}"
            )

    except WebSocketDisconnect:
        logger.info(f"WebSocket {websocket.client} disconnected.")
    except Exception as e:
        logger.error(
            f"Error in WebSocket connection {websocket.client}: {e}", exc_info=True
        )
    finally:
        live_update_mgr.disconnect(websocket)


# Main UI routes
def _render_index_page(
    request: Request,
    ui_config: UIConfig,
    current_page_id: str,
    pending_update_available: bool,
    error_message: Optional[str] = None,
    status_code: int = 200,
):
    current_page: Optional[PageConfig] = ui_config.find_page(current_page_id)
    all_pages: List[PageConfig] = ui_config.pages if ui_config else []

    if (
        not current_page and all_pages
    ):  # If current_page_id is invalid but there are pages, default to first
        current_page = all_pages[0]
        current_page_id = current_page.id
        logger.warning(
            f"Requested page_id '{current_page_id}' not found, defaulting to first page '{current_page.id}'."
        )
    elif not current_page and not all_pages:  # No pages configured at all
        logger.error("No pages configured in UIConfig.")
        error_message = error_message or "UI Configuration has no pages."
        # Fall through to render with error
    elif not current_page:  # Specific page_id not found, but other pages exist
        logger.warning(
            f"Requested page_id '{current_page_id}' not found. Valid pages: {[p.id for p in all_pages]}"
        )
        # This case should ideally be handled by defaulting or a specific error message
        # For now, let it fall through, it might show an error or an empty content area if current_page is None

    page_title = (
        f"{current_page.name} - Visual Control Board"
        if current_page
        else "Visual Control Board"
    )
    if error_message:
        page_title = "Error - Visual Control Board"

    context = {
        "request": request,
        "page_title": page_title,
        "all_pages": all_pages,
        "current_page_id": current_page.id if current_page else None,
        "current_page": current_page,  # This is the PageConfig object for the content area
        "error": error_message,
        "pending_update_available": pending_update_available,
    }
    return templates.TemplateResponse("index.html", context, status_code=status_code)


@router.get("/", response_class=HTMLResponse, name="get_index_page_root")
@router.get(
    "/page/{page_id:str}",
    response_class=HTMLResponse,
    name="get_index_page_with_page_id",
)
async def get_index_page(
    request: Request,
    page_id: Optional[str] = None,  # Comes from path parameter
    ui_config: UIConfig = Depends(get_ui_config),
    pending_update_available: bool = Depends(get_pending_update_flag),
):
    if not ui_config or not ui_config.pages:
        logger.warning("UI Configuration not found or no pages defined.")
        return _render_index_page(
            request,
            ui_config,
            None,
            pending_update_available,
            error_message="UI Configuration not found or is empty.",
            status_code=500,
        )

    initial_page_id = page_id or ui_config.pages[0].id

    current_page_obj = ui_config.find_page(initial_page_id)
    if not current_page_obj:
        logger.warning(
            f"Initial page ID '{initial_page_id}' not found. Defaulting to first available page."
        )
        initial_page_id = ui_config.pages[
            0
        ].id  # Default to the first page if specified ID is invalid

    return _render_index_page(
        request, ui_config, initial_page_id, pending_update_available
    )


@router.get(
    "/content/page/{page_id:str}", response_class=HTMLResponse, name="get_page_content"
)
async def get_page_content_partial(
    request: Request,
    page_id: str,
    ui_config: UIConfig = Depends(get_ui_config),
    pending_update_available: bool = Depends(
        get_pending_update_flag
    ),  # Keep context consistent
):
    if not ui_config:
        raise HTTPException(
            status_code=503, detail="UI configuration is currently unavailable."
        )

    selected_page = ui_config.find_page(page_id)
    if not selected_page:
        logger.warning(f"Page ID '{page_id}' not found for content rendering.")
        # Return an error message within the content area
        error_content = templates.get_template("partials/page_content.html").render(
            {
                "request": request,
                "page": PageConfig(
                    name="Error", id="error", buttons=[]
                ),  # Dummy page for structure
                "error": f"Page '{page_id}' not found.",
            }
        )
        # Also update nav to show no active tab or handle gracefully
        nav_html = templates.get_template("partials/nav.html").render(
            {
                "request": request,
                "all_pages": ui_config.pages,
                "current_page_id": None,  # No page is active
                "is_direct_nav_render": False,  # This is for OOB swap
            }
        )
        title_html = templates.get_template("partials/title_tag.html").render(
            {"page_title": "Page Not Found"}
        )
        header_title_html = templates.get_template(
            "partials/header_title_tag.html"
        ).render({"header_title": "Page Not Found"})

        return HTMLResponse(
            content=error_content + nav_html + title_html + header_title_html
        )

    # Render page content
    page_content_html = templates.get_template("partials/page_content.html").render(
        {"request": request, "page": selected_page}
    )

    # Render updated navigation (for OOB swap, to set active class)
    nav_html = templates.get_template("partials/nav.html").render(
        {
            "request": request,
            "all_pages": ui_config.pages,
            "current_page_id": selected_page.id,
            "pending_update_available": pending_update_available,  # Pass this through
            "is_direct_nav_render": False,  # This is for OOB swap
        }
    )

    # Render updated page title (for OOB swap)
    new_page_title = f"{selected_page.name} - Visual Control Board"
    title_html = templates.get_template("partials/title_tag.html").render(
        {"page_title": new_page_title}
    )

    # Render updated header title (for OOB swap)
    header_title_html = templates.get_template("partials/header_title_tag.html").render(
        {"header_title": selected_page.name}
    )

    # Combine all parts for the response
    # The main page content is first, then OOB swaps
    full_response_content = (
        page_content_html + nav_html + title_html + header_title_html
    )
    return HTMLResponse(content=full_response_content)


@router.get(
    "/content/navigation_panel",
    response_class=HTMLResponse,
    name="get_navigation_panel",
)
async def get_navigation_panel_partial(
    request: Request,
    active_page_id: Optional[str] = None,  # Client can suggest its current active page
    ui_config: UIConfig = Depends(get_ui_config),
    pending_update_available: bool = Depends(get_pending_update_flag),
):
    """
    Renders and returns only the navigation panel HTML.
    Used by client-side JS to refresh navigation via WebSocket trigger.
    The 'is_direct_nav_render' context variable is set to True here.
    """
    if not ui_config or not ui_config.pages:
        # Return an empty nav or a specific message if no pages
        # Ensure it still has the id for replacement target
        return HTMLResponse(
            content='<nav id="page-navigation" class="nav-tabs"><ul></ul></nav>'
        )

    current_page_id_for_nav = active_page_id
    if active_page_id and not ui_config.find_page(active_page_id):
        logger.warning(
            f"Requested active_page_id '{active_page_id}' for nav not found in current config. Defaulting."
        )
        current_page_id_for_nav = None  # Let template default or pick first

    if not current_page_id_for_nav and ui_config.pages:
        current_page_id_for_nav = ui_config.pages[
            0
        ].id  # Default to first page if none active or provided invalid

    nav_html = templates.get_template("partials/nav.html").render(
        {
            "request": request,
            "all_pages": ui_config.pages,
            "current_page_id": current_page_id_for_nav,
            "pending_update_available": pending_update_available,
            "is_direct_nav_render": True,  # Key change: signal direct render
        }
    )
    return HTMLResponse(content=nav_html)


@router.post("/action/{button_id}", response_class=HTMLResponse)
async def handle_button_action(
    request: Request,
    button_id: str,
    ui_config: UIConfig = Depends(get_ui_config),
    action_registry: ActionRegistry = Depends(get_action_registry),
):
    if not ui_config:
        logger.critical(f"UI Configuration not available for button ID: {button_id}.")
        error_message = "Critical Error: UI Configuration not loaded."
        toast_html = templates.get_template("partials/toast.html").render(
            {
                "request": request,
                "message": error_message,
                "toast_class": "toast show error",
            }
        )
        return HTMLResponse(content=toast_html, status_code=500)

    found_config = ui_config.find_button_and_page(button_id)

    if not found_config:
        logger.warning(f"Button ID '{button_id}' not found in UI configuration.")
        error_message = f"Configuration error: Button ID '{button_id}' not found."
        toast_html = templates.get_template("partials/toast.html").render(
            {
                "request": request,
                "message": error_message,
                "toast_class": "toast show error",
            }
        )
        return HTMLResponse(content=toast_html)

    _originating_page_config, button_config = found_config
    action_id = button_config.action_id
    action_params = button_config.action_params.model_dump()

    logger.info(
        f"Action for button ID: '{button_id}', Action ID: '{action_id}', Params: {action_params}"
    )
    result = await action_registry.execute_action(action_id, params=action_params)
    logger.info(f"Action '{action_id}' for button '{button_id}' result: {result}")

    feedback_message = f"Action '{action_id}' completed."
    toast_class = "toast show"

    if isinstance(result, dict):
        if "error" in result or result.get("status") == "error":
            feedback_message = result.get(
                "message", result.get("error", f"Error executing action '{action_id}'.")
            )
            toast_class = "toast show error"
            logger.error(
                f"Action '{action_id}' for button '{button_id}' error: {feedback_message}"
            )
        elif "message" in result:
            feedback_message = str(result["message"])
    elif isinstance(result, str) and result:
        feedback_message = result

    toast_html = templates.get_template("partials/toast.html").render(
        {
            "request": request,
            "message_id": f"toast-message-content-{button_id}",
            "message": feedback_message,
            "toast_class": toast_class,
        }
    )
    # Since button hx-swap="none", this button_html part of response is ignored by the button itself.
    # It's still good practice to have it in case hx-swap behavior changes on button.
    button_html = templates.get_template("partials/button.html").render(
        {
            "request": request,
            "button": button_config,
        }
    )
    final_html_content = toast_html + button_html
    return HTMLResponse(content=final_html_content)


# Include the sub-routers in the main app router
router.include_router(config_router)
router.include_router(live_updates_router)
