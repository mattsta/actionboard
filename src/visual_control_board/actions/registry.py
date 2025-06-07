import importlib
import inspect
from typing import Callable, Dict, Any, Optional
import logging

from visual_control_board.config.models import ActionDefinition, ActionsConfig

logger = logging.getLogger(__name__)

class ActionRegistry:
    """
    Manages the registration and execution of actions defined in the ActionsConfig.
    Actions are Python functions that can be dynamically loaded and called.
    """
    def __init__(self):
        self._actions: Dict[str, Callable] = {}
        self._action_definitions: Dict[str, ActionDefinition] = {}
        logger.debug("ActionRegistry initialized.")

    def load_actions(self, actions_config: Optional[ActionsConfig]):
        """
        Loads and registers actions from the provided ActionsConfig.
        It dynamically imports the modules and retrieves the functions specified
        in each ActionDefinition.

        Args:
            actions_config: An ActionsConfig object containing the list of actions to load.
                            If None or empty, no actions are loaded.
        """
        if not actions_config or not actions_config.actions:
            logger.warning("No actions found in configuration or ActionsConfig not provided. Action registry will be empty.")
            return

        logger.info(f"Loading {len(actions_config.actions)} actions into registry...")
        for action_def in actions_config.actions:
            try:
                logger.debug(f"Attempting to load action '{action_def.id}': module='{action_def.module}', function='{action_def.function}'")
                module = importlib.import_module(action_def.module)
                func = getattr(module, action_def.function)
                
                if callable(func):
                    self._actions[action_def.id] = func
                    self._action_definitions[action_def.id] = action_def
                    logger.info(f"Successfully registered action: ID='{action_def.id}' -> {action_def.module}.{action_def.function}")
                else:
                    logger.error(f"Failed to register action '{action_def.id}': {action_def.module}.{action_def.function} is not callable.")
            except ImportError:
                logger.error(f"Failed to register action '{action_def.id}': Could not import module '{action_def.module}'. Check PYTHONPATH and module name.", exc_info=True)
            except AttributeError:
                logger.error(f"Failed to register action '{action_def.id}': Could not find function '{action_def.function}' in module '{action_def.module}'.", exc_info=True)
            except Exception as e:
                logger.error(f"An unexpected error occurred while loading action '{action_def.id}': {e}", exc_info=True)
        logger.info(f"Action loading complete. {len(self._actions)} actions registered.")


    def get_action(self, action_id: str) -> Optional[Callable]:
        """
        Retrieves a callable action function by its registered ID.

        Args:
            action_id: The unique ID of the action.

        Returns:
            The callable function if found, otherwise None.
        """
        action_func = self._actions.get(action_id)
        if not action_func:
            logger.warning(f"Action with ID '{action_id}' not found in registry.")
        return action_func

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Executes a registered action by its ID with the given parameters.
        This method handles both synchronous and asynchronous (awaitable) action functions.

        Args:
            action_id: The ID of the action to execute.
            params: A dictionary of parameters to pass to the action function.
                    Defaults to an empty dictionary if None.

        Returns:
            The result of the action function execution. If the action is not found
            or an error occurs during execution, a dictionary with an "error" key
            is returned.
        """
        action_func = self.get_action(action_id)
        if not action_func:
            error_msg = f"Action '{action_id}' not found in registry. Cannot execute."
            logger.error(error_msg)
            return {"status": "error", "error": error_msg, "message": error_msg} # Ensure message for toast

        if params is None:
            params = {}
        
        try:
            logger.info(f"Executing action '{action_id}' with params: {params if params else 'No params'}")
            
            if inspect.iscoroutinefunction(action_func):
                # Action is an async function
                logger.debug(f"Action '{action_id}' is an async function. Awaiting execution.")
                result = await action_func(**params)
            else:
                # Action is a sync function
                logger.debug(f"Action '{action_id}' is a sync function. Executing directly.")
                result = action_func(**params)
            
            logger.info(f"Action '{action_id}' executed successfully.")
            logger.debug(f"Result for action '{action_id}': {result}")
            return result
        except Exception as e:
            error_msg = f"Error during execution of action '{action_id}': {str(e)}"
            logger.error(f"Error executing action '{action_id}': {e}", exc_info=True)
            return {"status": "error", "error": error_msg, "message": error_msg} # Ensure message for toast

# Note: The global instance of ActionRegistry was removed to favor dependency injection.
# Initialization and loading are handled in main.py's startup event.

# The __main__ block below is for standalone testing/demonstration.
# It requires manual setup of a dummy ActionsConfig.
# For comprehensive testing, unit/integration tests (e.g., using pytest) are recommended.
#
# if __name__ == "__main__":
#     import asyncio
#     logging.basicConfig(level=logging.DEBUG)
#     logger.info("Running ActionRegistry standalone test...")

#     # Example: Create a dummy ActionsConfig object
#     # This assumes you have 'visual_control_board.actions.built_in_actions' available
#     # and it contains the specified functions.
#     dummy_actions_list = [
#         ActionDefinition(id="test_greet", module="visual_control_board.actions.built_in_actions", function="greet_user_action"),
#         ActionDefinition(id="test_async", module="visual_control_board.actions.built_in_actions", function="example_async_action"),
#         ActionDefinition(id="non_existent_func_action", module="visual_control_board.actions.built_in_actions", function="this_function_does_not_exist")
#     ]
#     dummy_actions_config = ActionsConfig(actions=dummy_actions_list)

#     # Initialize and load actions
#     registry = ActionRegistry()
#     registry.load_actions(actions_config=dummy_actions_config)

#     # Test execution
#     async def main_test():
#         print("\n--- Testing Action Execution ---")
#         result_greet = await registry.execute_action("test_greet", {"name": "CLI Tester"})
#         print(f"Greet action result: {result_greet}")

#         result_async = await registry.execute_action("test_async", {"duration": 0.1}) # Short duration for test
#         print(f"Async action result: {result_async}")

#         result_missing_func = await registry.execute_action("non_existent_func_action")
#         print(f"Missing function action result: {result_missing_func}")
        
#         result_missing_id = await registry.execute_action("action_id_not_in_registry")
#         print(f"Missing action ID result: {result_missing_id}")

#     asyncio.run(main_test())
#     logger.info("ActionRegistry standalone test finished.")
