import datetime
import asyncio # For async example
import logging

logger = logging.getLogger(__name__)

def greet_user_action(name: str = "User"):
    """Simple action that prints a greeting and returns a message."""
    message = f"Hello, {name}! This action was triggered."
    logger.info(f"Executing greet_user_action for {name}")
    return {"status": "success", "message": message}

def log_current_time_action():
    """Logs the current time to the console and returns it."""
    now = datetime.datetime.now().isoformat()
    message = f"Current time: {now}"
    logger.info("Executing log_current_time_action")
    return {"status": "success", "timestamp": now, "message": message}

async def example_async_action(duration: int = 1):
    """An example of an asynchronous action that simulates work."""
    message_start = f"Starting async action (will take {duration}s)..."
    logger.info(message_start)
    await asyncio.sleep(duration)
    message_end = f"Async action completed after {duration}s."
    logger.info(message_end)
    return {"status": "success", "message": message_end, "duration": duration}

def another_action():
    """Another simple placeholder action."""
    message = "Another action was performed!"
    logger.info("Executing another_action")
    return {"status": "success", "message": message}

# You can add more actions here.
# Remember to register them in your actions_config.yaml
