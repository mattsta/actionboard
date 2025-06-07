import yaml
from pathlib import Path
from .models import UIConfig, ActionsConfig
from typing import Optional, Tuple, Dict
import logging
import shutil

logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Default directory for user-override configurations (at project root)
DEFAULT_USER_CONFIG_DIR = PROJECT_ROOT / "user_config"
DEFAULT_USER_UI_CONFIG_FILE = DEFAULT_USER_CONFIG_DIR / "ui_config.yaml"
DEFAULT_USER_ACTIONS_CONFIG_FILE = DEFAULT_USER_CONFIG_DIR / "actions_config.yaml"

# Directory for example/fallback configurations (part of the package/repository)
EXAMPLE_CONFIG_DIR = PROJECT_ROOT / "config_examples"
EXAMPLE_UI_CONFIG_FILE = EXAMPLE_CONFIG_DIR / "ui_config.yaml"
EXAMPLE_ACTIONS_CONFIG_FILE = EXAMPLE_CONFIG_DIR / "actions_config.yaml"

class ConfigLoader:
    def __init__(
        self,
        ui_config_path: Optional[Path] = None,
        actions_config_path: Optional[Path] = None,
    ):
        self.explicit_ui_path_provided = ui_config_path is not None
        self.explicit_actions_path_provided = actions_config_path is not None

        self.primary_ui_config_path = ui_config_path or DEFAULT_USER_UI_CONFIG_FILE
        self.fallback_ui_config_path = None if self.explicit_ui_path_provided else EXAMPLE_UI_CONFIG_FILE
        
        self.primary_actions_config_path = actions_config_path or DEFAULT_USER_ACTIONS_CONFIG_FILE
        self.fallback_actions_config_path = None if self.explicit_actions_path_provided else EXAMPLE_ACTIONS_CONFIG_FILE
        
        self.ui_config: Optional[UIConfig] = None
        self.actions_config: Optional[ActionsConfig] = None
        
        logger.info(f"ConfigLoader initialized.")
        logger.info(f"Primary UI config path: {self.primary_ui_config_path}")
        if self.fallback_ui_config_path:
            logger.info(f"Fallback UI config path: {self.fallback_ui_config_path}")
        logger.info(f"Primary Actions config path: {self.primary_actions_config_path}")
        if self.fallback_actions_config_path:
            logger.info(f"Fallback Actions config path: {self.fallback_actions_config_path}")

    def _attempt_load_yaml(self, file_path: Path) -> Optional[Dict]:
        """Attempts to load and parse a YAML file."""
        if not file_path.exists():
            logger.debug(f"Configuration file not found at {file_path}")
            return None
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
            if data is None:
                logger.warning(f"Configuration file at {file_path} is empty or contains only comments.")
                return None
            return data
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML from {file_path}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path}: {e}", exc_info=True)
        return None

    def load_configs(self):
        """Loads both UI and Actions configurations, with fallback mechanism."""
        logger.info("Attempting to load UI and Actions configurations...")
        
        # Load UI Config
        ui_data = self._attempt_load_yaml(self.primary_ui_config_path)
        loaded_ui_path = self.primary_ui_config_path
        if ui_data is None and self.fallback_ui_config_path:
            logger.info(f"Primary UI config not found or invalid at {self.primary_ui_config_path}. Attempting fallback.")
            ui_data = self._attempt_load_yaml(self.fallback_ui_config_path)
            loaded_ui_path = self.fallback_ui_config_path if ui_data else None
        
        if ui_data:
            try:
                self.ui_config = UIConfig(**ui_data)
                logger.info(f"UI configuration loaded successfully from {loaded_ui_path}")
            except Exception as e: # Catches Pydantic validation errors
                logger.error(f"Error validating UI config from {loaded_ui_path}: {e}", exc_info=True)
                self.ui_config = None
        
        if not self.ui_config:
             logger.warning(f"UI configuration failed to load. Tried primary: '{self.primary_ui_config_path}'" +
                           (f" and fallback: '{self.fallback_ui_config_path}'." if self.fallback_ui_config_path else "."))


        # Load Actions Config
        actions_data = self._attempt_load_yaml(self.primary_actions_config_path)
        loaded_actions_path = self.primary_actions_config_path
        if actions_data is None and self.fallback_actions_config_path:
            logger.info(f"Primary Actions config not found or invalid at {self.primary_actions_config_path}. Attempting fallback.")
            actions_data = self._attempt_load_yaml(self.fallback_actions_config_path)
            loaded_actions_path = self.fallback_actions_config_path if actions_data else None

        if actions_data:
            try:
                self.actions_config = ActionsConfig(**actions_data)
                logger.info(f"Actions configuration loaded successfully from {loaded_actions_path}")
            except Exception as e: # Catches Pydantic validation errors
                logger.error(f"Error validating Actions config from {loaded_actions_path}: {e}", exc_info=True)
                self.actions_config = None

        if not self.actions_config:
            logger.warning(f"Actions configuration failed to load. Tried primary: '{self.primary_actions_config_path}'" +
                           (f" and fallback: '{self.fallback_actions_config_path}'." if self.fallback_actions_config_path else "."))

    # Methods _load_ui_config and _load_actions_config are refactored into load_configs with _attempt_load_yaml helper

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running ConfigLoader standalone test...")

    # Test Case 1: No user_config, should fallback to config_examples
    logger.info("\n--- Test Case 1: Fallback to example configurations ---")
    # Ensure user_config directory is temporarily removed or empty for this test part
    # For safety, we'll rename if it exists, then rename back.
    # Or, more simply, ensure no dummy files are in user_config for this part.
    # We assume config_examples/*.yaml exist.
    
    # Clean up any dummy files from previous tests in user_config
    if DEFAULT_USER_UI_CONFIG_FILE.exists():
        DEFAULT_USER_UI_CONFIG_FILE.unlink()
    if DEFAULT_USER_ACTIONS_CONFIG_FILE.exists():
        DEFAULT_USER_ACTIONS_CONFIG_FILE.unlink()
    if DEFAULT_USER_CONFIG_DIR.exists() and not any(DEFAULT_USER_CONFIG_DIR.iterdir()):
         DEFAULT_USER_CONFIG_DIR.rmdir()


    loader_fallback = ConfigLoader()
    loader_fallback.load_configs()

    if loader_fallback.ui_config:
        logger.info(f"UI Config Loaded (fallback test). Source should be '{EXAMPLE_UI_CONFIG_FILE}'.")
        # logger.info(loader_fallback.ui_config.model_dump_json(indent=2))
    else:
        logger.error("Failed to load UI Config in fallback test.")
        
    if loader_fallback.actions_config:
        logger.info(f"Actions Config Loaded (fallback test). Source should be '{EXAMPLE_ACTIONS_CONFIG_FILE}'.")
        # logger.info(loader_fallback.actions_config.model_dump_json(indent=2))
    else:
        logger.error("Failed to load Actions Config in fallback test.")

    # Test Case 2: user_config exists and has files, should override examples
    logger.info("\n--- Test Case 2: User configurations override examples ---")
    DEFAULT_USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    dummy_user_ui_content = {
        "pages": [{
            "name": "User Test Page", "id": "user_test_page", "layout": "grid", "grid_columns": 1,
            "buttons": [{"id": "user_btn", "text": "User Button", "action_id": "user_action"}]
        }]
    }
    with open(DEFAULT_USER_UI_CONFIG_FILE, "w") as f:
        yaml.dump(dummy_user_ui_content, f)
    logger.info(f"Created dummy user UI config for test at {DEFAULT_USER_UI_CONFIG_FILE}")

    dummy_user_actions_content = {
        "actions": [{"id": "user_action", "module": "user.module", "function": "user_func"}]
    }
    with open(DEFAULT_USER_ACTIONS_CONFIG_FILE, "w") as f:
        yaml.dump(dummy_user_actions_content, f)
    logger.info(f"Created dummy user Actions config for test at {DEFAULT_USER_ACTIONS_CONFIG_FILE}")

    loader_override = ConfigLoader()
    loader_override.load_configs()

    if loader_override.ui_config:
        logger.info(f"UI Config Loaded (override test). Source should be '{DEFAULT_USER_UI_CONFIG_FILE}'.")
        assert loader_override.ui_config.pages[0].name == "User Test Page"
        # logger.info(loader_override.ui_config.model_dump_json(indent=2))
    else:
        logger.error("Failed to load UI Config in override test.")
        
    if loader_override.actions_config:
        logger.info(f"Actions Config Loaded (override test). Source should be '{DEFAULT_USER_ACTIONS_CONFIG_FILE}'.")
        assert loader_override.actions_config.actions[0].id == "user_action"
        # logger.info(loader_override.actions_config.model_dump_json(indent=2))
    else:
        logger.error("Failed to load Actions Config in override test.")

    # Test Case 3: Explicit path provided, should only use that path
    logger.info("\n--- Test Case 3: Explicit path provided ---")
    explicit_ui_path = EXAMPLE_CONFIG_DIR / "ui_config.yaml" # Using example for convenience
    loader_explicit = ConfigLoader(ui_config_path=explicit_ui_path)
    loader_explicit.load_configs()
    if loader_explicit.ui_config:
        logger.info(f"UI Config Loaded (explicit path test). Source should be '{explicit_ui_path}'.")
        assert loader_explicit.ui_config.pages[0].name == "Main Controls" # From example config
    else:
        logger.error("Failed to load UI Config in explicit path test.")


    # Cleanup dummy user config files
    logger.info("\nCleaning up dummy user configuration files...")
    if DEFAULT_USER_UI_CONFIG_FILE.exists():
        DEFAULT_USER_UI_CONFIG_FILE.unlink()
    if DEFAULT_USER_ACTIONS_CONFIG_FILE.exists():
        DEFAULT_USER_ACTIONS_CONFIG_FILE.unlink()
    # Remove user_config dir if it's empty and was created by this test
    if DEFAULT_USER_CONFIG_DIR.exists() and not any(DEFAULT_USER_CONFIG_DIR.iterdir()):
        try:
            DEFAULT_USER_CONFIG_DIR.rmdir()
            logger.info(f"Removed empty directory: {DEFAULT_USER_CONFIG_DIR}")
        except OSError as e:
            logger.warning(f"Could not remove directory {DEFAULT_USER_CONFIG_DIR}: {e}")
    
    logger.info("ConfigLoader standalone test finished.")
