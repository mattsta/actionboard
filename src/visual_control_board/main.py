from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import sys

from .config.loader import ConfigLoader
from .actions.registry import ActionRegistry
from .web import routes as web_routes

# --- Logging Setup ---
# Basic configuration, can be expanded (e.g., to use a file, structured logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) # Ensure logs go to stdout for services like Docker
    ]
)
logger = logging.getLogger(__name__)

# Determine the base directory of the 'visual_control_board' package
# This is where 'static' and 'templates' (implicitly via Jinja in routes) are located
package_base_dir = Path(__file__).parent.resolve()

app = FastAPI(title="Visual Control Board")

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory=package_base_dir / "static"),
    name="static"
)

# Include web routes
app.include_router(web_routes.router)

@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    Load configurations and initialize action registry.
    These are stored in app.state for access via dependency injection.
    """
    logger.info("Application starting up...")

    # Initialize and load configurations
    # ConfigLoader defaults to src/visual_control_board/user_config/
    config_loader_instance = ConfigLoader()
    config_loader_instance.load_configs()

    app.state.ui_config = config_loader_instance.ui_config
    app.state.actions_config = config_loader_instance.actions_config

    if app.state.ui_config is None:
        logger.critical("CRITICAL: Failed to load UI configuration. Check paths and file content. Application might not function correctly.")
        # Depending on requirements, you might want to raise an error to stop startup
        # raise RuntimeError("Failed to load UI configuration. Application cannot start.")
    else:
        logger.info("UI configuration loaded successfully.")

    if app.state.actions_config is None:
        logger.critical("CRITICAL: Failed to load Actions configuration. Check paths and file content. Actions will not be available.")
        # raise RuntimeError("Failed to load Actions configuration. Application cannot start.")
    else:
        logger.info("Actions configuration loaded successfully.")
    
    # Initialize Action Registry
    action_registry_instance = ActionRegistry()
    if app.state.actions_config: # Only load if actions_config is available
        action_registry_instance.load_actions(actions_config=app.state.actions_config)
    else:
        logger.warning("Actions configuration is missing, so no actions were loaded into the registry.")
    app.state.action_registry = action_registry_instance
    logger.info("Action registry initialized.")
    
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    # Any cleanup tasks can go here
    logger.info("Application shutdown complete.")

# To run this app (from the project root directory):
# Ensure you have your config_examples copied to src/visual_control_board/user_config/
# Then run: uvicorn src.visual_control_board.main:app --reload --host 0.0.0.0 --port 8000
