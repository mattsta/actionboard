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
from typing import Optional, Dict, Any
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
async def apply_staged_configuration(request: Request, response: Response):
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
    WebSocket endpoint for clients to receive live button content updates.
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
@router.get("/", response_class=HTMLResponse)
async def get_index_page(
    request: Request,
    ui_config: Optional[UIConfig] = Depends(get_ui_config),
    pending_update_available: bool = Depends(get_pending_update_flag),
):
    if not ui_config or not ui_config.pages:
        logger.warning(
            "UI Configuration not found or no pages defined when serving index page."
        )
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "page_title": "Error - Visual Control Board",
                "current_page": None,
                "error": "UI Configuration not found or is empty.",
                "pending_update_available": pending_update_available,
            },
            status_code=500,
        )

    current_page = ui_config.pages[0]
    logger.info(
        f"Serving index page with content from page: '{current_page.name}' (ID: {current_page.id})"
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page_title": f"{current_page.name} - Visual Control Board",
            "current_page": current_page,
            "error": None,
            "pending_update_available": pending_update_available,
        },
    )


@router.post("/action/{button_id}", response_class=HTMLResponse)
async def handle_button_action(
    request: Request,
    button_id: str,
    ui_config: Optional[UIConfig] = Depends(get_ui_config),
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

    originating_page_config, button_config = found_config
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
