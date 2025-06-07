from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import sys
from typing import Optional 

from .config.loader import ConfigLoader
from .config.models import UIConfig, ActionsConfig 
from .actions.registry import ActionRegistry
from .web import routes as web_routes
# Dependencies are used by routes, not directly in main usually, but good to be aware of them.
# from .dependencies import get_ui_config, get_actions_config, get_action_registry

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) 
    ]
)
logger = logging.getLogger(__name__) 

package_base_dir = Path(__file__).parent.resolve()

app = FastAPI(
    title="Visual Control Board",
    description="A web-based visual control board for triggering custom actions, with dynamic update capabilities.",
    version="0.1.1" # Incremented version for new feature
)

app.mount(
    "/static",
    StaticFiles(directory=package_base_dir / "static"),
    name="static"
)

app.include_router(web_routes.router)

@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    Initializes configurations and action registry.
    Sets up state for current and potentially staged configurations.
    """
    logger.info("Application starting up...")

    config_loader_instance = ConfigLoader() 
    config_loader_instance.load_configs() 

    # Initialize current configurations
    app.state.current_ui_config: Optional[UIConfig] = config_loader_instance.ui_config
    app.state.current_actions_config: Optional[ActionsConfig] = config_loader_instance.actions_config

    # Initialize staged configurations (for dynamic updates)
    app.state.staged_ui_config: Optional[UIConfig] = None
    app.state.staged_actions_config: Optional[ActionsConfig] = None
    app.state.pending_update_available: bool = False

    # Critical check: Initial UI Configuration must be loaded.
    if app.state.current_ui_config is None:
        logger.critical("CRITICAL: Failed to load initial UI configuration. Application cannot start.")
        raise RuntimeError("Failed to load initial UI configuration. Check logs for details.")
    else:
        logger.info(f"Initial UI configuration loaded: {len(app.state.current_ui_config.pages)} page(s).")

    # Critical check: Initial Actions Configuration must be loaded.
    if app.state.current_actions_config is None:
        logger.critical("CRITICAL: Failed to load initial Actions configuration. Application cannot start.")
        raise RuntimeError("Failed to load initial Actions configuration. Check logs for details.")
    else:
        logger.info(f"Initial Actions configuration loaded: {len(app.state.current_actions_config.actions)} action(s).")
    
    # Initialize Action Registry with current actions config
    action_registry_instance = ActionRegistry()
    action_registry_instance.load_actions(actions_config=app.state.current_actions_config)
    app.state.action_registry: ActionRegistry = action_registry_instance
    logger.info("Action registry initialized with current actions.")
    
    logger.info("Application startup complete. Ready to accept requests.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    """
    logger.info("Application shutting down...")
    logger.info("Application shutdown complete.")

