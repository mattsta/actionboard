# Visual Control Board

A web-based visual control board, inspired by devices like Elgato Stream Deck, built with Python, FastAPI, and HTMX. The UI is dynamically generated from configuration files, allowing users to define buttons that trigger backend actions. This version supports dynamic updates to the entire board configuration via an API, and live streaming of individual button content (text, icon, style) via WebSockets.

## Features

*   **Dynamic UI from Configuration:** Button layouts, appearances, and actions defined in `ui_config.yaml`.
*   **Pluggable Actions:** Actions mapped to Python functions via `actions_config.yaml`.
*   **User-Managed Overrides:** `user_config/` for initial custom configurations.
*   **Runs Out-of-the-Box:** Default examples in `config_examples/`.
*   **HTMX Powered Frontend:** Rich interactions with minimal custom JavaScript.
*   **FastAPI Backend:** Modern, high-performance Python web framework.
*   **Dynamic Configuration API:**
    *   `POST /api/v1/config/stage`: Stages new UI/Actions configurations.
    *   `POST /api/v1/config/apply`: Applies staged configurations.
    *   `POST /api/v1/config/discard`: Discards staged configurations.
*   **Live Button Content Streaming (WebSockets):**
    *   `GET /ws/button_updates`: WebSocket endpoint for clients to receive real-time updates to button content.
    *   `POST /api/v1/buttons/update_content`: HTTP endpoint for external services to push content updates for specific buttons, which are then broadcast over WebSockets.
*   **Dependency Injection, Centralized Logging, Asynchronous Support.**
*   **`uv` Managed Project.**
*   **Multi-Page Navigation:** Define multiple pages (tabs) in `ui_config.yaml` and navigate between them.

## Quickstart

```bash
pip install -U uv
uv sync
uv run uvicorn src.visual_control_board.main:app --reload --host 0.0.0.0 --port 8000
# open http://127.0.0.1:8000
# Configuration files for actions are in config_examples/actions_config.yaml
# Configuration files for tab and button layout binding to actions are in config_examples/ui_config.yaml

# You can also run a demo of replacing/updating the entire buttons UI live
# (along with having buttons refresh their display content from API updates)
# with the example script at:
uv run python -m examples.dynamic_board_controller
```

## Architecture

For a detailed understanding of the project's components, data flow, and extensibility, including the dynamic configuration and live update mechanisms, please refer to the [ARCHITECTURE.md](ARCHITECTURE.md) document.

### **Initial Configuration (Optional but Recommended for Customization)**

*   The application runs by default using the example configurations found in the `config_examples/` directory.
*   To customize:
    1.  Ensure a `user_config/` directory exists at the root of the project. If not, create it:
        ```bash
        mkdir -p user_config
        ```
    2.  Copy the example configurations from `config_examples/` to your `user_config/` directory:
        ```bash
        cp config_examples/ui_config.yaml user_config/
        cp config_examples/actions_config.yaml user_config/
        ```
    3.  Modify the YAML files within `user_config/` to define your custom pages, buttons, and actions. These files will take precedence over the defaults in `config_examples/` when the application starts.

## Running the Application

<!-- NOTE: DO NOT EDIT OR MOVE OR CHANGE THIS UVICORN COMMAND OR ELSE THE README BREAKS! -->
Once the setup is complete and dependencies are installed, you can run the FastAPI application using Uvicorn. To do this, execute the command: `uvicorn src.visual_control_board.main:app --reload --host 0.0.0.0 --port 8000` in your terminal.
<!-- NOTE: DO NOT EDIT OR MOVE OR CHANGE THE ABOVE UVICORN COMMAND OR ELSE THE README BREAKS! -->

The options used are:
*   `--reload`: Enables auto-reloading when code changes (useful for development).
*   `--host 0.0.0.0`: Makes the application accessible from other devices on your network.
*   `--port 8000`: Specifies the port to run on.

Open your web browser and navigate to `http://localhost:8000` (or `http://<your-server-ip>:8000` if accessing from another device).

## Creating Custom Actions

You can extend the functionality of the Visual Control Board by adding your own custom actions. Here's how:

1.  **Write your Action Function in Python:**
    *   Create a new Python file (e.g., `my_custom_actions.py`) or add to an existing one (like `src/visual_control_board/actions/built_in_actions.py`).
    *   Your function can be synchronous (`def`) or asynchronous (`async def`).
    *   It can accept parameters, which will be supplied from `action_params` in your `ui_config.yaml`.
    *   It's recommended to return a dictionary, often with `"status"` and `"message"` keys, for UI feedback (e.g., toast notifications).

    Example (`my_custom_actions.py` placed in `src/visual_control_board/actions/`):
    ```python
    # src/visual_control_board/actions/my_custom_actions.py
    import logging
    import asyncio # if using async

    logger = logging.getLogger(__name__)

    def my_new_action(target_url: str, attempts: int = 1):
        logger.info(f"My new action called with URL: {target_url} and {attempts} attempts.")
        # ... your custom logic here ...
        return {
            "status": "success",
            "message": f"Successfully pinged {target_url} {attempts} times."
        }

    async def my_async_custom_action(user_id: str):
        logger.info(f"Async custom action for user: {user_id}")
        # ... your async logic here ...
        await asyncio.sleep(1) # Example async operation
        return {
            "status": "success",
            "message": f"Async task for {user_id} completed."
        }
    ```

2.  **Register your Action in `actions_config.yaml`:**
    *   Open your `user_config/actions_config.yaml` (or `config_examples/actions_config.yaml` if you're providing defaults).
    *   Add a new entry under the `actions` list:
        *   `id`: A unique identifier for your action.
        *   `module`: The Python module path to your function (e.g., `visual_control_board.actions.my_custom_actions`).
        *   `function`: The name of your Python function.

    Example `actions_config.yaml` entry:
    ```yaml
    actions:
      # ... other actions ...
      - id: "custom_ping_action"
        module: "visual_control_board.actions.my_custom_actions"
        function: "my_new_action"
      
      - id: "custom_async_user_task"
        module: "visual_control_board.actions.my_custom_actions"
        function: "my_async_custom_action"
    ```
    *Ensure your Python module (`my_custom_actions.py` in this example) is discoverable in Python's path. Placing it within the `src/visual_control_board/actions/` directory and making sure `src/visual_control_board/actions/__init__.py` exists usually suffices.*

3.  **Use your Action in `ui_config.yaml`:**
    *   In your `user_config/ui_config.yaml`, define a button and set its `action_id` to the ID you registered.
    *   You can pass parameters using `action_params`.

    Example `ui_config.yaml` button:
    ```yaml
    pages:
      - name: "Custom Page"
        id: "custom_page"
        buttons:
          - id: "trigger_my_action"
            text: "Ping Example.com"
            icon_class: "fas fa-network-wired"
            action_id: "custom_ping_action"
            action_params:
              target_url: "http://example.com"
              attempts: 3
          - id: "trigger_my_async_action"
            text: "User Task"
            icon_class: "fas fa-user-cog"
            action_id: "custom_async_user_task"
            action_params:
              user_id: "user123"
    ```

4.  **Restart the Application:** If the application is already running, you'll need to restart it for the new Python modules and action configurations to be loaded. If you're using `--reload`, changes to Python files might trigger a reload, but new action configurations in YAML typically require a restart or a dynamic configuration update via the API.

## Dynamic Configuration API

(See ARCHITECTURE.md for details on `/api/v1/config/*` endpoints)

## Live Button Content Update API

*   **WebSocket Endpoint: `GET /ws/button_updates`**
    *   Clients connect to this endpoint to receive live updates.
    *   Messages are JSON, typically: `{"type": "button_content_update", "payload": {"button_id": "...", "text": "...", ...}}`

*   **HTTP Endpoint: `POST /api/v1/buttons/update_content`**
    *   **Purpose**: Allows external services or internal logic to push a content update for a specific button.
    *   **Request Body**: A JSON object matching the `ButtonContentUpdate` model:
        ```json
        {
          "button_id": "my_button_1",
          "text": "New Live Text!",
          "icon_class": "fas fa-sync fa-spin",
          "style_class": "button-live-updated"
        }
        ```
        (All fields in the payload except `button_id` are optional).
    *   **Behavior**: The server broadcasts this update payload to all connected WebSocket clients.
    *   **Response**: `200 OK` with a confirmation message.

## Examples

See the `examples/` directory for scripts that demonstrate programmatic interaction with the Visual Control Board, such as dynamically adding pages/buttons and streaming live content. The `examples/README.md` provides instructions on how to run them.

## Future Enhancements (Potential)

*   **More Granular API Updates:** APIs to update specific pages or buttons instead of the entire configuration for full updates.
*   **Authentication/Authorization:** Secure API endpoints and WebSocket connections.
