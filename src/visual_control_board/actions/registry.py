import importlib
import inspect
from typing import Callable, Dict, Any, Optional
import logging

from visual_control_board.config.models import ActionDefinition, ActionsConfig

logger = logging.getLogger(__name__)

class ActionRegistry:
    def __init__(self):
        self._actions: Dict[str, Callable] = {}
        self._action_definitions: Dict[str, ActionDefinition] = {}

    def load_actions(self, actions_config: Optional[ActionsConfig]):
        """
        Loads actions from the provided ActionsConfig.
        Dynamically imports modules and functions specified in the config.
        """
        if not actions_config or not actions_config.actions:
            logger.warning("No actions found in configuration or configuration not provided to load_actions.")
            return

        logger.info(f"Loading {len(actions_config.actions)} actions into registry...")
        for action_def in actions_config.actions:
            try:
                module = importlib.import_module(action_def.module)
                func = getattr(module, action_def.function)
                if callable(func):
                    self._actions[action_def.id] = func
                    self._action_definitions[action_def.id] = action_def
                    logger.info(f"Successfully registered action: {action_def.id} -> {action_def.module}.{action_def.function}")
                else:
                    logger.error(f"Error: {action_def.module}.{action_def.function} for action '{action_def.id}' is not callable.")
            except ImportError:
                logger.error(f"Error: Could not import module {action_def.module} for action '{action_def.id}'.")
            except AttributeError:
                logger.error(f"Error: Could not find function {action_def.function} in module {action_def.module} for action '{action_def.id}'.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while loading action '{action_def.id}': {e}", exc_info=True)
        logger.info("Action loading complete.")


    def get_action(self, action_id: str) -> Optional[Callable]:
        """Retrieves a callable action function by its ID."""
        return self._actions.get(action_id)

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Executes an action by its ID with the given parameters.
        Handles both synchronous and asynchronous action functions.
        """
        action_func = self.get_action(action_id)
        if not action_func:
            logger.warning(f"Action '{action_id}' not found in registry.")
            return {"error": f"Action '{action_id}' not found."}

        if params is None:
            params = {}
        
        try:
            logger.info(f"Executing action '{action_id}' with params: {params}")
            
            if inspect.iscoroutinefunction(action_func):
                 # It's an async function
                return await action_func(**params)
            else:
                # It's a sync function
                return action_func(**params)
        except Exception as e:
            logger.error(f"Error executing action '{action_id}': {e}", exc_info=True)
            return {"error": f"Error during execution of action '{action_id}': {str(e)}"}

# Global instance removed for dependency injection.
# Initialization will be handled in main.py's startup event.

# The __main__ block below is for standalone testing/demonstration.
# It would require manual setup of a dummy ActionsConfig if used,
# as it no longer relies on a global config_loader.
# For simplicity in this refactor, it's commented out.
# Proper testing should be done via unit/integration tests.
#
# if __name__ == "__main__":
#     import asyncio
#     # Example usage (requires manual setup of ActionsConfig):
#     # 1. Create a dummy ActionsConfig object
#     dummy_actions_list = [
#         ActionDefinition(id="test_greet", module="visual_control_board.actions.built_in_actions", function="greet_user_action"),
#         ActionDefinition(id="test_async", module="visual_control_board.actions.built_in_actions", function="example_async_action")
#     ]
#     dummy_actions_config = ActionsConfig(actions=dummy_actions_list)
#
#     # 2. Initialize and load actions
#     registry = ActionRegistry()
#     registry.load_actions(actions_config=dummy_actions_config)
#
#     # 3. Execute actions
#     async def main():
#         result_greet = await registry.execute_action("test_greet", {"name": "CLI User"})
#         print(f"Greet action result: {result_greet}")
#
#         result_async = await registry.execute_action("test_async", {"duration": 1})
#         print(f"Async action result: {result_async}")
#
#         result_missing = await registry.execute_action("non_existent_action")
#         print(f"Missing action result: {result_missing}")
#
#     asyncio.run(main())
