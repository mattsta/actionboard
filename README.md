# Visual Control Board

A web-based visual control board, inspired by devices like Elgato Stream Deck, built with Python, FastAPI, and HTMX. The UI is dynamically generated from configuration files, allowing users to define buttons that trigger backend actions.

## Features

*   **Dynamic UI:** Button layouts, appearances, and actions are defined in YAML configuration files (`ui_config.yaml`, `actions_config.yaml`).
*   **Pluggable Actions:** Button actions are mapped to Python functions, allowing for easy extension by adding new Python modules and functions.
*   **Web Interface:** Accessible from any web browser on the local network.
*   **HTMX Powered:** Rich user interactions with minimal JavaScript.
*   **FastAPI Backend:** Modern, fast Python web framework.
*   **Dependency Injection:** Core components like configuration and action registry are managed via FastAPI's dependency injection for better testability and maintainability.
*   **Centralized Logging:** Standardized logging for application events.
*   **`uv` Managed:** Uses `uv` for package management and virtual environments.

## Architecture

For a detailed understanding of the project's components and data flow, please refer to the [ARCHITECTURE.md](ARCHITECTURE.md) document.

## Prerequisites

*   Python 3.8+
*   `uv` (Python package installer and virtual environment manager). If you don't have `uv`, you can install it via pip: `pip install uv`.

## Setup and Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd visual-control-board
    ```

2.  **Create and activate a virtual environment using `uv`:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Linux/macOS
    # .venv\Scripts\activate    # On Windows
    ```

3.  **Install dependencies using `uv`:**
    ```bash
    uv pip install -e .[dev]
    ```
    This installs the package in editable mode (`-e`) along with development dependencies.

4.  **Set up User Configurations:**
    *   The application expects configuration files in the `src/visual_control_board/user_config/` directory.
    *   Copy the example configurations:
        ```bash
        cp config_examples/ui_config.yaml src/visual_control_board/user_config/
        cp config_examples/actions_config.yaml src/visual_control_board/user_config/
        ```
    *   Modify these copied files in `src/visual_control_board/user_config/` to customize your board. **Do not edit the files in `config_examples/` directly for your setup.**

## Running the Application

Once the setup is complete, you can run the FastAPI application using Uvicorn:

