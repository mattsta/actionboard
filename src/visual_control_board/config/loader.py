import yaml
from pathlib import Path
from .models import UIConfig, ActionsConfig
from typing import Optional, Dict # Removed Tuple as it's no longer used here
import logging
# import shutil # Unused import

logger = logging.getLogger(__name__)

# Project root directory, calculated relative to this file's location.
# Assuming src/visual_control_board/config/loader.py
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Default directory for user-override configurations (expected at project root)
DEFAULT_USER_CONFIG_DIR = PROJECT_ROOT / "user_config"
DEFAULT_USER_UI_CONFIG_FILE = DEFAULT_USER_CONFIG_DIR / "ui_config.yaml"
DEFAULT_USER_ACTIONS_CONFIG_FILE = DEFAULT_USER_CONFIG_DIR / "actions_config.yaml"

# Directory for example/fallback configurations (part of the package/repository)
EXAMPLE_CONFIG_DIR = PROJECT_ROOT / "config_examples"
EXAMPLE_UI_CONFIG_FILE = EXAMPLE_CONFIG_DIR / "ui_config.yaml"
EXAMPLE_ACTIONS_CONFIG_FILE = EXAMPLE_CONFIG_DIR / "actions_config.yaml"

class ConfigLoader:
    """
    Handles loading of UI and Actions configurations from YAML files.
    It implements a fallback mechanism:
    1. Attempts to load from explicitly provided paths (if any).
    2. If no explicit path, attempts to load from `user_config/` directory at the project root.
    3. If not found in `user_config/` (and no explicit path was given), falls back to `config_examples/`.
    """
    def __init__(
        self,
        ui_config_path: Optional[Path] = None,
        actions_config_path: Optional[Path] = None,
    ):
        """
        Initializes the ConfigLoader with optional explicit paths for configuration files.

        Args:
            ui_config_path: Explicit path to the UI configuration YAML file.
            actions_config_path: Explicit path to the Actions configuration YAML file.
        """
        self.explicit_ui_path_provided = ui_config_path is not None
        self.explicit_actions_path_provided = actions_config_path is not None

        # Determine primary and fallback paths for UI config
        self.primary_ui_config_path = ui_config_path or DEFAULT_USER_UI_CONFIG_FILE
        self.fallback_ui_config_path = None if self.explicit_ui_path_provided else EXAMPLE_UI_CONFIG_FILE
        
        # Determine primary and fallback paths for Actions config
        self.primary_actions_config_path = actions_config_path or DEFAULT_USER_ACTIONS_CONFIG_FILE
        self.fallback_actions_config_path = None if self.explicit_actions_path_provided else EXAMPLE_ACTIONS_CONFIG_FILE
        
        self.ui_config: Optional[UIConfig] = None
        self.actions_config: Optional[ActionsConfig] = None
        
        logger.info("ConfigLoader initialized.")
        logger.info(f"UI Config: Primary path = '{self.primary_ui_config_path}'" +
                    (f", Fallback path = '{self.fallback_ui_config_path}'" if self.fallback_ui_config_path else " (No fallback due to explicit path)"))
        logger.info(f"Actions Config: Primary path = '{self.primary_actions_config_path}'" +
                    (f", Fallback path = '{self.fallback_actions_config_path}'" if self.fallback_actions_config_path else " (No fallback due to explicit path)"))

    def _attempt_load_yaml(self, file_path: Path) -> Optional[Dict]:
        """
        Attempts to load and parse a YAML file.

        Args:
            file_path: The Path object pointing to the YAML file.

        Returns:
            A dictionary with the parsed YAML content, or None if loading/parsing fails or file is empty.
        """
        if not file_path.exists():
            logger.debug(f"Configuration file not found at {file_path}")
            return None
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
            if data is None: # File is empty or contains only comments
                logger.warning(f"Configuration file at {file_path} is empty or contains only comments. No data loaded.")
                return None
            logger.debug(f"Successfully read YAML data from {file_path}")
            return data
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML from {file_path}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path}: {e}", exc_info=True)
        return None

    def load_configs(self):
        """
        Loads both UI and Actions configurations.
        It tries the primary path first, then the fallback path if applicable.
        Loaded configurations are stored in `self.ui_config` and `self.actions_config`.
        """
        logger.info("Attempting to load UI and Actions configurations...")
        
        # --- Load UI Config ---
        ui_data = self._attempt_load_yaml(self.primary_ui_config_path)
        loaded_ui_path_str = str(self.primary_ui_config_path) # For logging
        
        if ui_data is None and self.fallback_ui_config_path:
            logger.info(f"Primary UI config not found or invalid at '{self.primary_ui_config_path}'. Attempting fallback from '{self.fallback_ui_config_path}'.")
            ui_data = self._attempt_load_yaml(self.fallback_ui_config_path)
            if ui_data:
                loaded_ui_path_str = str(self.fallback_ui_config_path)
        
        if ui_data:
            try:
                self.ui_config = UIConfig(**ui_data)
                logger.info(f"UI configuration loaded successfully from '{loaded_ui_path_str}'.")
            except Exception as e: # Catches Pydantic validation errors
                logger.error(f"Error validating UI config data from '{loaded_ui_path_str}': {e}", exc_info=True)
                self.ui_config = None # Ensure config is None if validation fails
        
        if not self.ui_config:
             logger.warning(f"UI configuration FAILED to load. Attempted primary: '{self.primary_ui_config_path}'" +
                           (f" and fallback: '{self.fallback_ui_config_path}'." if self.fallback_ui_config_path else "."))

        # --- Load Actions Config ---
        actions_data = self._attempt_load_yaml(self.primary_actions_config_path)
        loaded_actions_path_str = str(self.primary_actions_config_path) # For logging

        if actions_data is None and self.fallback_actions_config_path:
            logger.info(f"Primary Actions config not found or invalid at '{self.primary_actions_config_path}'. Attempting fallback from '{self.fallback_actions_config_path}'.")
            actions_data = self._attempt_load_yaml(self.fallback_actions_config_path)
            if actions_data:
                loaded_actions_path_str = str(self.fallback_actions_config_path)

        if actions_data:
            try:
                self.actions_config = ActionsConfig(**actions_data)
                logger.info(f"Actions configuration loaded successfully from '{loaded_actions_path_str}'.")
            except Exception as e: # Catches Pydantic validation errors
                logger.error(f"Error validating Actions config data from '{loaded_actions_path_str}': {e}", exc_info=True)
                self.actions_config = None # Ensure config is None if validation fails

        if not self.actions_config:
            logger.warning(f"Actions configuration FAILED to load. Attempted primary: '{self.primary_actions_config_path}'" +
                           (f" and fallback: '{self.fallback_actions_config_path}'." if self.fallback_actions_config_path else "."))

# Main block for standalone testing of ConfigLoader
if __name__ == "__main__":
    # Setup basic logging for the test
    logging.basicConfig(
        level=logging.DEBUG, # Use DEBUG to see file not found messages etc.
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger.info("Running ConfigLoader standalone test...")

    # --- Test Case 1: No user_config, should fallback to config_examples ---
    logger.info("\n--- Test Case 1: Fallback to example configurations ---")
    # Ensure user_config directory is clean for this test part.
    # These files should not exist for fallback to trigger.
    if DEFAULT_USER_UI_CONFIG_FILE.exists():
        DEFAULT_USER_UI_CONFIG_FILE.unlink()
    if DEFAULT_USER_ACTIONS_CONFIG_FILE.exists():
        DEFAULT_USER_ACTIONS_CONFIG_FILE.unlink()
    # If the directory exists and is empty (e.g., only .gitkeep), that's fine.
    # If it doesn't exist, that's also fine.

    loader_fallback = ConfigLoader()
    loader_fallback.load_configs()

    if loader_fallback.ui_config:
        logger.info(f"UI Config Loaded (fallback test). Source should be example: '{EXAMPLE_UI_CONFIG_FILE}'.")
        # Example assertion: check a known value from example config
        assert loader_fallback.ui_config.pages[0].name == "Main Controls" 
    else:
        logger.error("Failed to load UI Config in fallback test.")
        
    if loader_fallback.actions_config:
        logger.info(f"Actions Config Loaded (fallback test). Source should be example: '{EXAMPLE_ACTIONS_CONFIG_FILE}'.")
        assert len(loader_fallback.actions_config.actions) > 0
    else:
        logger.error("Failed to load Actions Config in fallback test.")

    # --- Test Case 2: user_config exists and has files, should override examples ---
    logger.info("\n--- Test Case 2: User configurations override examples ---")
    DEFAULT_USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create dummy user UI config
    dummy_user_ui_content = {
        "pages": [{
            "name": "User Test Page", "id": "user_test_page", "layout": "grid", "grid_columns": 1,
            "buttons": [{"id": "user_btn", "text": "User Button", "action_id": "user_action"}]
        }]
    }
    with open(DEFAULT_USER_UI_CONFIG_FILE, "w") as f:
        yaml.dump(dummy_user_ui_content, f)
    logger.info(f"Created dummy user UI config for test at {DEFAULT_USER_UI_CONFIG_FILE}")

    # Create dummy user Actions config
    dummy_user_actions_content = {
        "actions": [{"id": "user_action", "module": "user.module", "function": "user_func"}]
    }
    with open(DEFAULT_USER_ACTIONS_CONFIG_FILE, "w") as f:
        yaml.dump(dummy_user_actions_content, f)
    logger.info(f"Created dummy user Actions config for test at {DEFAULT_USER_ACTIONS_CONFIG_FILE}")

    loader_override = ConfigLoader()
    loader_override.load_configs()

    if loader_override.ui_config:
        logger.info(f"UI Config Loaded (override test). Source should be user: '{DEFAULT_USER_UI_CONFIG_FILE}'.")
        assert loader_override.ui_config.pages[0].name == "User Test Page"
    else:
        logger.error("Failed to load UI Config in override test.")
        
    if loader_override.actions_config:
        logger.info(f"Actions Config Loaded (override test). Source should be user: '{DEFAULT_USER_ACTIONS_CONFIG_FILE}'.")
        assert loader_override.actions_config.actions[0].id == "user_action"
    else:
        logger.error("Failed to load Actions Config in override test.")

    # --- Test Case 3: Explicit path provided, should only use that path ---
    logger.info("\n--- Test Case 3: Explicit path provided (using example file as explicit) ---")
    # For this test, we use one of the example files as an "explicitly provided" path.
    # This means the loader should not attempt to load from user_config or any other fallback for this specific config.
    explicit_ui_path = EXAMPLE_UI_CONFIG_FILE 
    
    # Temporarily remove user UI config to ensure explicit path is the only one considered
    if DEFAULT_USER_UI_CONFIG_FILE.exists():
        DEFAULT_USER_UI_CONFIG_FILE.unlink()

    loader_explicit = ConfigLoader(ui_config_path=explicit_ui_path) # Provide only UI path explicitly
    loader_explicit.load_configs() # Actions config will still use default logic (user then example)
    
    if loader_explicit.ui_config:
        logger.info(f"UI Config Loaded (explicit path test). Source MUST be '{explicit_ui_path}'.")
        assert loader_explicit.ui_config.pages[0].name == "Main Controls" # From example config
    else:
        logger.error("Failed to load UI Config in explicit path test.")
    
    if loader_explicit.actions_config: # Actions config should have loaded from example as user_actions_config.yaml was removed for override test
        logger.info(f"Actions Config Loaded (explicit UI path test, actions default logic). Source should be '{EXAMPLE_ACTIONS_CONFIG_FILE}' (assuming user one is cleaned up).")
    else:
        logger.error("Failed to load Actions Config in explicit UI path test.")


    # --- Cleanup dummy user config files created by this test ---
    logger.info("\nCleaning up dummy user configuration files...")
    if DEFAULT_USER_UI_CONFIG_FILE.exists():
        DEFAULT_USER_UI_CONFIG_FILE.unlink()
        logger.debug(f"Removed {DEFAULT_USER_UI_CONFIG_FILE}")
    if DEFAULT_USER_ACTIONS_CONFIG_FILE.exists():
        DEFAULT_USER_ACTIONS_CONFIG_FILE.unlink()
        logger.debug(f"Removed {DEFAULT_USER_ACTIONS_CONFIG_FILE}")
    
    # Attempt to remove user_config dir ONLY if it's empty and was likely created by this test.
    # Be cautious if .gitkeep or other files might be in user_config.
    # The `any(DEFAULT_USER_CONFIG_DIR.iterdir())` check might be problematic if .gitkeep exists.
    # For simplicity, we'll just log if removal fails.
    if DEFAULT_USER_CONFIG_DIR.exists():
        try:
            # Check if it's truly empty (ignoring .gitkeep for this check is harder)
            # A simple check: if only .gitkeep, it has 1 item. If empty, 0 items.
            # For this test, we only created .yaml files, so if they are gone, it might be empty.
            if not any(f for f in DEFAULT_USER_CONFIG_DIR.iterdir() if f.name != ".gitkeep"):
                 # If only .gitkeep or empty, try to remove. This logic is imperfect.
                 # A safer approach for tests is to use a temporary directory for user_config.
                 # For now, we'll be less aggressive with rmdir.
                 logger.info(f"Directory {DEFAULT_USER_CONFIG_DIR} might be eligible for cleanup if empty (excluding .gitkeep). Manual check recommended if it persists.")
        except OSError as e:
            logger.warning(f"Could not remove or check directory {DEFAULT_USER_CONFIG_DIR} during cleanup: {e}")
    
    logger.info("ConfigLoader standalone test finished.")
