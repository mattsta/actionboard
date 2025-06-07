import datetime
import asyncio # For async example
import logging

logger = logging.getLogger(__name__)

def greet_user_action(name: str = "User"):
    """
    A simple synchronous action that prints a greeting and returns a message.
    
    Args:
        name (str): The name of the user to greet. Defaults to "User".
        
    Returns:
        dict: A dictionary containing the status and a greeting message.
    """
    message = f"Hello, {name}! This action was triggered."
    logger.info(f"Executing greet_user_action for {name}")
    return {"status": "success", "message": message}

def log_current_time_action():
    """
    Logs the current ISO formatted time to the console and returns it along with a message.
    
    Returns:
        dict: A dictionary containing the status, current timestamp, and a message.
    """
    now = datetime.datetime.now().isoformat()
    message = f"Current time: {now}"
    logger.info("Executing log_current_time_action")
    return {"status": "success", "timestamp": now, "message": message}

async def example_async_action(duration: int = 1):
    """
    An example of an asynchronous action that simulates a delay.
    
    Args:
        duration (int): The number of seconds to wait. Defaults to 1.
        
    Returns:
        dict: A dictionary containing the status, a completion message, and the duration.
    """
    message_start = f"Starting async action (will take {duration}s)..."
    logger.info(message_start)
    await asyncio.sleep(duration)
    message_end = f"Async action completed after {duration}s."
    logger.info(message_end)
    return {"status": "success", "message": message_end, "duration": duration}

def another_action():
    """
    Another simple placeholder synchronous action.
    
    Returns:
        dict: A dictionary containing the status and a generic message.
    """
    message = "Another action was performed!"
    logger.info("Executing another_action")
    return {"status": "success", "message": message}

# You can add more actions here.
# Remember to register them in your actions_config.yaml
# (e.g., in src/visual_control_board/user_config/actions_config.yaml)
