import asyncio
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class LiveUpdateManager:
    """
    Manages active WebSocket connections and broadcasts messages for live updates.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        logger.info("LiveUpdateManager initialized.")

    async def connect(self, websocket: WebSocket):
        """
        Accepts a new WebSocket connection and adds it to the list of active connections.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established: {websocket.client}")
        logger.debug(f"Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Removes a WebSocket connection from the list of active connections.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket connection closed: {websocket.client}")
            logger.debug(f"Total active connections: {len(self.active_connections)}")
        else:
            logger.warning(f"Attempted to disconnect a WebSocket that was not in active_connections: {websocket.client}")


    async def broadcast_json(self, data: Dict[str, Any]):
        """
        Broadcasts a JSON payload (as a dictionary) to all active WebSocket connections.
        """
        if not self.active_connections:
            logger.debug("No active WebSocket connections to broadcast to.")
            return

        logger.info(f"Broadcasting JSON data to {len(self.active_connections)} connection(s): {data}")
        
        # Create a list of tasks for sending messages concurrently
        # If a connection is closed, sending will raise an error.
        # We should handle this gracefully and remove dead connections.
        tasks = []
        dead_connections = []

        for connection in self.active_connections:
            try:
                # Create a task for each send operation
                tasks.append(connection.send_json(data))
            except Exception as e: # Broad exception to catch various WebSocket errors
                logger.warning(f"Error preparing to send to WebSocket {connection.client}: {e}. Marking for removal.")
                dead_connections.append(connection)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    connection = self.active_connections[i-len(dead_connections)] # Adjust index if some were already marked
                    logger.error(f"Failed to send message to WebSocket {connection.client}: {result}. Marking for removal.")
                    if connection not in dead_connections: # Avoid double-adding
                        dead_connections.append(connection)
        
        # Remove all identified dead connections
        for dead_connection in dead_connections:
            self.disconnect(dead_connection)
        
        if not dead_connections:
            logger.debug("Broadcast successful to all connections.")
        else:
            logger.info(f"Removed {len(dead_connections)} dead connections during broadcast.")

    async def broadcast_button_update(self, update_data: Dict[str, Any]):
        """
        Specifically broadcasts a button content update.
        The `update_data` should conform to what the client-side JavaScript expects,
        typically including `type: "button_content_update"` and the payload.
        """
        message_to_broadcast = {
            "type": "button_content_update",
            "payload": update_data
        }
        await self.broadcast_json(message_to_broadcast)

