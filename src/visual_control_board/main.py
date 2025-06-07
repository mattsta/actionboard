from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import sys

from .config.loader import ConfigLoader
from .config.models import UIConfig, ActionsConfig # For type checking app.state
from .actions.registry import ActionRegistry
from .web import routes as web_routes
from .dependencies import get_ui_config, get_actions_config, get_action_registry # For app.state type hints

# --- Logging Setup ---
# Configure basic logging to output to stdout, suitable for containerized environments or simple console output.
# The format includes timestamp, logger name, log level, and message.
logging.basicConfig(
    level=logging.INFO, # Default level, can be overridden by specific loggers or environment variables
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) 
    ]
)
logger = logging.getLogger(__name__) # Logger for this main module

# Determine the base directory of the 'visual_control_board' package
# This is used for mounting static files relative to the package location.
package_base_dir = Path(__file__).parent.resolve()

# Initialize the FastAPI application
app = FastAPI(
    title="Visual Control Board",
    description="A web-based visual control board for triggering custom actions.",
    version="0.1.0" # Corresponds to pyproject.toml version
)

# Mount static files (CSS, JS, images)
# Files in 'src/visual_control_board/static/' will be accessible under '/static' URL path.
app.mount(
    "/static",
    StaticFiles(directory=package_base_dir / "static"),
    name="static"
)

# Include web routes defined in src/visual_control_board/web/routes.py
app.include_router(web_routes.router)

@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    This function is executed when the FastAPI application starts.
    It performs essential initializations:
    1. Loads UI and Actions configurations using ConfigLoader.
       - It prioritizes files in 'user_config/' at the project root.
       - If not found, it falls back to 'config_examples/' within the package.
    2. Stores the loaded configurations in `app.state` for global access via dependency injection.
    3. Initializes the ActionRegistry and loads actions based on the ActionsConfig.
    4. Raises a RuntimeError if critical configurations (UI or Actions) fail to load,
       preventing the application from starting in an unusable state.
    """
    logger.info("Application starting up...")

    # Initialize ConfigLoader. It will determine paths based on defaults or explicit settings.
    config_loader_instance = ConfigLoader() 
    config_loader_instance.load_configs() # This loads both UI and Actions configs

    # Store loaded configurations in app.state for access by dependencies
    app.state.ui_config: Optional[UIConfig] = config_loader_instance.ui_config
    app.state.actions_config: Optional[ActionsConfig] = config_loader_instance.actions_config

    # Critical check: UI Configuration must be loaded.
    if app.state.ui_config is None:
        logger.critical("CRITICAL: Failed to load UI configuration. No UI config found in 'user_config/' or 'config_examples/'. Application cannot start.")
        # This error will prevent Uvicorn from starting successfully if raised during startup.
        raise RuntimeError("Failed to load UI configuration. Application cannot start. Check logs for details on config file paths.")
    else:
        logger.info(f"UI configuration loaded successfully. {len(app.state.ui_config.pages)} page(s) defined.")

    # Critical check: Actions Configuration must be loaded.
    if app.state.actions_config is None:
        logger.critical("CRITICAL: Failed to load Actions configuration. No Actions config found in 'user_config/' or 'config_examples/'. Application cannot start.")
        raise RuntimeError("Failed to load Actions configuration. Application cannot start. Check logs for details on config file paths.")
    else:
        logger.info(f"Actions configuration loaded successfully. {len(app.state.actions_config.actions)} action(s) defined.")
    
    # Initialize Action Registry and load actions from the (now confirmed) loaded actions_config
    action_registry_instance = ActionRegistry()
    # The check above ensures app.state.actions_config is not None here.
    action_registry_instance.load_actions(actions_config=app.state.actions_config)
    app.state.action_registry: ActionRegistry = action_registry_instance
    logger.info("Action registry initialized and actions loaded.")
    
    logger.info("Application startup complete. Ready to accept requests.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    This function is executed when the FastAPI application is shutting down.
    Useful for cleanup tasks (e.g., closing database connections, releasing resources).
    """
    logger.info("Application shutting down...")
    # Add any cleanup tasks here if needed in the future.
    # For example:
    # if hasattr(app.state, 'db_connection') and app.state.db_connection:
    #     app.state.db_connection.close()
    #     logger.info("Database connection closed.")
    logger.info("Application shutdown complete.")

# --- How to Run This Application (from the project root directory) ---
# 1. Ensure you have `uv` installed.
# 2. Create and activate a virtual environment:
#    `uv venv`
#    `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
# 3. Install dependencies:
#    `uv pip install -e .[dev]`
# 4. (Optional but Recommended for Customization) Create 'user_config/' directory at project root:
#    `mkdir -p user_config`
#    Copy example configs:
#    `cp config_examples/ui_config.yaml user_config/`
#    `cp config_examples/actions_config.yaml user_config/`
#    Then, modify the files in `user_config/`.
# 5. Run the Uvicorn server:
#    `uvicorn src.visual_control_board.main:app --reload --host 0.0.0.0 --port 8000`
#
# The application will be accessible at http://localhost:8000 or http://<your-ip>:8000.
# It will use `config_examples/*` if `user_config/*` are not found or are invalid.
