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
    These are stored in app.state for access via dependency injection.
    If critical configurations (UI or Actions) fail to load, the application
    will raise a RuntimeError to prevent starting in a broken state.
    """
    logger.info("Application starting up...")

    # Initialize and load configurations
    config_loader_instance = ConfigLoader() # Defaults to src/visual_control_board/user_config/
    config_loader_instance.load_configs()

    app.state.ui_config = config_loader_instance.ui_config
    app.state.actions_config = config_loader_instance.actions_config

    if app.state.ui_config is None:
        logger.critical("CRITICAL: Failed to load UI configuration. Check paths and file content.")
        raise RuntimeError("Failed to load UI configuration. Application cannot start.")
    else:
        logger.info("UI configuration loaded successfully.")

    if app.state.actions_config is None:
        logger.critical("CRITICAL: Failed to load Actions configuration. Check paths and file content.")
        raise RuntimeError("Failed to load Actions configuration. Application cannot start.")
    else:
        logger.info("Actions configuration loaded successfully.")
    
    # Initialize Action Registry
    action_registry_instance = ActionRegistry()
    # Actions config is guaranteed to be non-None here due to the check above,
    # but we check again for logical completeness or if the above logic changes.
    if app.state.actions_config:
        action_registry_instance.load_actions(actions_config=app.state.actions_config)
    else:
        # This case should ideally not be reached if the RuntimeError above is active.
        logger.warning("Actions configuration is missing; no actions were loaded into the registry. This is unexpected if startup checks passed.")
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
# 3. Copy example configs:
#    cp config_examples/ui_config.yaml src/visual_control_board/user_config/
#    cp config_examples/actions_config.yaml src/visual_control_board/user_config/
# 4. Run: uvicorn src.visual_control_board.main:app --reload --host 0.0.0.0 --port 8000
