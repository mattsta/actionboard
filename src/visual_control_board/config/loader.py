import yaml
from pathlib import Path
from .models import UIConfig, ActionsConfig
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Default path relative to the 'src/visual_control_board' directory
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent / "user_config"
DEFAULT_UI_CONFIG_FILE = DEFAULT_CONFIG_DIR / "ui_config.yaml"
DEFAULT_ACTIONS_CONFIG_FILE = DEFAULT_CONFIG_DIR / "actions_config.yaml"

class ConfigLoader:
    def __init__(
        self,
        ui_config_path: Optional[Path] = None,
        actions_config_path: Optional[Path] = None,
    ):
        self.ui_config_path = ui_config_path or DEFAULT_UI_CONFIG_FILE
        self.actions_config_path = actions_config_path or DEFAULT_ACTIONS_CONFIG_FILE
        
        self.ui_config: Optional[UIConfig] = None
        self.actions_config: Optional[ActionsConfig] = None
        logger.info(f"ConfigLoader initialized. UI config path: {self.ui_config_path}, Actions config path: {self.actions_config_path}")

    def load_configs(self):
        """Loads both UI and Actions configurations."""
        logger.info("Attempting to load UI and Actions configurations...")
        self.ui_config = self._load_ui_config()
        self.actions_config = self._load_actions_config()
        
        if not self.ui_config:
            logger.warning(f"UI configuration failed to load from {self.ui_config_path}. Check file existence and content.")
        else:
            logger.info(f"UI configuration loaded successfully from {self.ui_config_path}")
            
        if not self.actions_config:
            logger.warning(f"Actions configuration failed to load from {self.actions_config_path}. Check file existence and content.")
        else:
            logger.info(f"Actions configuration loaded successfully from {self.actions_config_path}")


    def _load_ui_config(self) -> Optional[UIConfig]:
        if not self.ui_config_path.exists():
            logger.error(f"UI config file not found at {self.ui_config_path}")
            return None
        try:
            with open(self.ui_config_path, "r") as f:
                data = yaml.safe_load(f)
            if data is None: # Handle empty YAML file
                logger.error(f"UI config file at {self.ui_config_path} is empty or contains only comments.")
                return None
            return UIConfig(**data)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing UI config YAML from {self.ui_config_path}: {e}", exc_info=True)
        except Exception as e: # Catches Pydantic validation errors too
            logger.error(f"Error validating UI config from {self.ui_config_path}: {e}", exc_info=True)
        return None

    def _load_actions_config(self) -> Optional[ActionsConfig]:
        if not self.actions_config_path.exists():
            logger.error(f"Actions config file not found at {self.actions_config_path}")
            return None
        try:
            with open(self.actions_config_path, "r") as f:
                data = yaml.safe_load(f)
            if data is None: # Handle empty YAML file
                logger.error(f"Actions config file at {self.actions_config_path} is empty or contains only comments.")
                return None
            return ActionsConfig(**data)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing Actions config YAML from {self.actions_config_path}: {e}", exc_info=True)
        except Exception as e: # Catches Pydantic validation errors too
            logger.error(f"Error validating Actions config from {self.actions_config_path}: {e}", exc_info=True)
        return None

# Global instance and getter functions removed for dependency injection.
# ConfigLoader will be instantiated and managed by the FastAPI app.

if __name__ == "__main__":
    # This block is for standalone testing of the ConfigLoader.
    # It requires dummy config files to be present.
    logging.basicConfig(level=logging.INFO)
    logger.info("Running ConfigLoader standalone test...")

    # Ensure user_config directory exists for the test
    test_config_dir = Path(__file__).parent.parent / "user_config"
    test_config_dir.mkdir(parents=True, exist_ok=True)
    
    dummy_ui_path = test_config_dir / "ui_config.yaml"
    if not dummy_ui_path.exists():
        with open(dummy_ui_path, "w") as f:
            yaml.dump({
                "pages": [{
                    "name": "Test Page", "id": "test_page", "layout": "grid", "grid_columns": 2,
                    "buttons": [{
                        "id": "test_btn", "text": "Test Button", "action_id": "test_action"
                    }]
                }]
            }, f)
        logger.info(f"Created dummy UI config for test at {dummy_ui_path}")

    dummy_actions_path = test_config_dir / "actions_config.yaml"
    if not dummy_actions_path.exists():
        with open(dummy_actions_path, "w") as f:
            yaml.dump({
                "actions": [{
                    "id": "test_action", "module": "some.module", "function": "some_func"
                }]
            }, f)
        logger.info(f"Created dummy Actions config for test at {dummy_actions_path}")

    # Instantiate ConfigLoader directly for testing
    loader = ConfigLoader(
        ui_config_path=dummy_ui_path,
        actions_config_path=dummy_actions_path
    )
    loader.load_configs()

    if loader.ui_config:
        logger.info("UI Config Loaded (standalone test):")
        logger.info(loader.ui_config.model_dump_json(indent=2))
    else:
        logger.error("Failed to load UI Config in standalone test.")
        
    if loader.actions_config:
        logger.info("\nActions Config Loaded (standalone test):")
        logger.info(loader.actions_config.model_dump_json(indent=2))
    else:
        logger.error("Failed to load Actions Config in standalone test.")
