import datetime
import asyncio  # For async example
import logging

logger = logging.getLogger(__name__)


def greet_user_action(name: str = "User"):
    """
    A simple synchronous action that logs a greeting and returns a message.
    This action demonstrates how parameters from `action_params` in the UI config
    can be passed to an action function.

    Args:
        name (str): The name of the user to greet. Defaults to "User".

    Returns:
        dict: A dictionary containing the status and a greeting message.
              This dictionary is often used to provide feedback to the UI.
    """
    message = f"Hello, {name}! This greeting action was successfully triggered."
    logger.info(f"Executing greet_user_action for '{name}'")
    # The returned dictionary can be used by the frontend (e.g., to show a toast message)
    return {"status": "success", "message": message}


def log_current_time_action():
    """
    Logs the current ISO formatted time to the server console and returns it
    along with a success message.

    Returns:
        dict: A dictionary containing the status, current timestamp, and a message.
    """
    now = datetime.datetime.now().isoformat()
    message = f"Current server time: {now}"
    logger.info(f"Executing log_current_time_action. Time: {now}")
    return {"status": "success", "timestamp": now, "message": message}


async def example_async_action(duration: int = 1):
    """
    An example of an asynchronous action that simulates a delay (e.g., a long-running task).

    Args:
        duration (int): The number of seconds to wait. Defaults to 1.

    Returns:
        dict: A dictionary containing the status, a completion message, and the duration.
    """
    message_start = f"Starting async action (simulated duration: {duration}s)..."
    logger.info(message_start)

    await asyncio.sleep(duration)  # Simulate an I/O bound operation

    message_end = f"Async action completed after {duration}s."
    logger.info(message_end)
    return {"status": "success", "message": message_end, "duration": duration}


def another_action():
    """
    Another simple placeholder synchronous action for demonstration purposes.

    Returns:
        dict: A dictionary containing the status and a generic message.
    """
    message = "The 'another_action' was performed successfully!"
    logger.info("Executing another_action")
    return {"status": "success", "message": message}


# To add more actions:
# 1. Define your Python function here (or in another module).
#    - It can be synchronous (def my_action():) or asynchronous (async def my_action():).
#    - It can accept parameters, which will be supplied from `action_params` in `ui_config.yaml`.
#    - It should ideally return a dictionary, often with "status" and "message" keys,
#      to provide feedback to the UI (e.g., for toast notifications).
#
# 2. Register your action in an `actions_config.yaml` file.
#    - This file is typically `user_config/actions_config.yaml` (to override examples)
#      or `config_examples/actions_config.yaml` (for default/packaged actions).
#    - Example registration:
#      ```yaml
#      actions:
#        - id: "my_custom_action"  # Unique ID for this action
#          module: "visual_control_board.actions.built_in_actions" # Or your custom module path
#          function: "my_newly_defined_function_name"
#      ```
#
# 3. Reference the action `id` in your `ui_config.yaml` for a button:
#    ```yaml
#    buttons:
#      - id: "my_button_for_custom_action"
#        text: "Run My Custom Action"
#        action_id: "my_custom_action"
#        action_params: # Optional parameters for your action
#          param1: "value1"
#          count: 10
#    ```
