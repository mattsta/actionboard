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

Once the setup is complete and dependencies are installed, you can run the FastAPI application using Uvicorn:

