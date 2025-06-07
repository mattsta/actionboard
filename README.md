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

## Architecture

For a detailed understanding of the project's components, data flow, and extensibility, including the dynamic configuration and live update mechanisms, please refer to the [ARCHITECTURE.md](ARCHITECTURE.md) document.

## Prerequisites

*   Python 3.8+
*   `uv` (Python package installer and virtual environment manager).
    *   If you don't have `uv`, you can install it: `pip install uv` (or `pipx install uv`).

## Setup and Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd visual-control-board 
    ```
    (Replace `<repository-url>` with the actual URL of your repository).

2.  **Create and activate a virtual environment using `uv`:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Linux/macOS
    # .venv\Scripts\activate    # On Windows (Command Prompt)
    # .\.venv\Scripts\Activate.ps1 # On Windows (PowerShell)
    ```

3.  **Install dependencies using `uv`:**
    ```bash
    uv pip install -e .[dev]
    ```
    This installs the package in editable mode (`-e .`) along with development dependencies specified in `pyproject.toml` (`[dev]`).

4.  **Initial Configuration (Optional but Recommended for Customization):**
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

## Future Enhancements (Potential)

*   **More Granular API Updates:** APIs to update specific pages or buttons instead of the entire configuration for full updates.
*   **Authentication/Authorization:** Secure API endpoints and WebSocket connections.
*   **Multi-Page Navigation.**
