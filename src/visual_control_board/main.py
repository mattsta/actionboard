from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import sys

from .config.loader import ConfigLoader
from .actions.registry import ActionRegistry
from .web import routes as web_routes

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) # Ensure logs go to stdout for services like Docker
    ]
)
logger = logging.getLogger(__name__)

# Determine the base directory of the 'visual_control_board' package
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
    Configurations are loaded first from 'user_config/' at the project root (if present),
    falling back to 'config_examples/' if user-specific files are not found.
    These are stored in app.state for access via dependency injection.
    If critical configurations (UI or Actions) fail to load even from fallbacks,
    the application will raise a RuntimeError.
    """
    logger.info("Application starting up...")

    # Initialize and load configurations.
    # ConfigLoader will try user_config/ first, then config_examples/.
    config_loader_instance = ConfigLoader() 
    config_loader_instance.load_configs()

    app.state.ui_config = config_loader_instance.ui_config
    app.state.actions_config = config_loader_instance.actions_config

    if app.state.ui_config is None:
        logger.critical("CRITICAL: Failed to load UI configuration. No UI config found in 'user_config/' or 'config_examples/'. Application cannot start.")
        raise RuntimeError("Failed to load UI configuration. Application cannot start.")
    else:
        logger.info("UI configuration loaded successfully.")

    if app.state.actions_config is None:
        logger.critical("CRITICAL: Failed to load Actions configuration. No Actions config found in 'user_config/' or 'config_examples/'. Application cannot start.")
        raise RuntimeError("Failed to load Actions configuration. Application cannot start.")
    else:
        logger.info("Actions configuration loaded successfully.")
    
    # Initialize Action Registry
    action_registry_instance = ActionRegistry()
    if app.state.actions_config: # Should always be true if startup checks passed
        action_registry_instance.load_actions(actions_config=app.state.actions_config)
    else:
        # This case should ideally not be reached if the RuntimeError above is active.
        logger.warning("Actions configuration is missing post-startup checks; no actions were loaded. This is unexpected.")
    app.state.action_registry = action_registry_instance
    logger.info("Action registry initialized.")
    
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    # Any cleanup tasks can go here
    logger.info("Application shutdown complete.")

# To run this app (from the project root directory):
# 1. Ensure you have `uv` installed and a virtual environment set up and activated.
# 2. Install dependencies: `uv pip install -e .[dev]`
# 3. (Optional) To customize, create 'user_config/' at the project root and copy examples:
#    mkdir -p user_config
#    cp config_examples/ui_config.yaml user_config/
#    cp config_examples/actions_config.yaml user_config/
# 4. Run: uvicorn src.visual_control_board.main:app --reload --host 0.0.0.0 --port 8000
#    The app will run with example configs if 'user_config/' is not set up.
