# Visual Control Board

A web-based visual control board, inspired by devices like Elgato Stream Deck, built with Python, FastAPI, and HTMX. The UI is dynamically generated from configuration files, allowing users to define buttons that trigger backend actions.

## Features

*   **Dynamic UI from Configuration:** Button layouts, appearances (text, icons, styles), and associated actions are defined in `ui_config.yaml`.
*   **Pluggable Actions:** Button actions are mapped to Python functions via `actions_config.yaml`, allowing for easy extension and customization of backend operations. Each button currently triggers a single action.
*   **User-Managed Overrides:** Customize by placing your `ui_config.yaml` and `actions_config.yaml` in a `user_config/` directory at the project root. These files will override the default example configurations.
*   **Runs Out-of-the-Box:** Comes with default example configurations in `config_examples/`, so it's runnable immediately after setup.
*   **HTMX Powered Frontend:** Rich user interactions (like button clicks and feedback toasts) with minimal custom JavaScript, leveraging HTMX for server-rendered HTML partials.
*   **FastAPI Backend:** Modern, fast (high-performance) Python web framework for building APIs and serving the web interface.
*   **Dependency Injection:** Core components like configurations and the action registry are managed and accessed via FastAPI's dependency injection system.
*   **Centralized Logging:** Standardized logging for application events, errors, and debugging.
*   **`uv` Managed Project:** Uses `uv` for Python package installation and virtual environment management.
*   **Asynchronous Support:** Actions can be defined as standard synchronous Python functions or `async` functions for non-blocking I/O operations.

## Architecture

For a detailed understanding of the project's components, data flow, and extensibility, please refer to the [ARCHITECTURE.md](ARCHITECTURE.md) document.

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

2.  **Create and activate a virtual environment using `uv`:**
    ```bash
    uv venv  # This creates a .venv directory
    source .venv/bin/activate  # On Linux/macOS
    # .venv\Scripts\activate    # On Windows (Command Prompt)
    # .\.venv\Scripts\Activate.ps1 # On Windows (PowerShell)
    ```

3.  **Install dependencies using `uv`:**
    ```bash
    uv pip install -e .[dev]
    ```
    This installs the package in editable mode (`-e .`) along with development dependencies specified in `pyproject.toml` (`[dev]`).

4.  **Configuration:**
    *   The application runs by default using the example configurations found in the `config_examples/` directory (e.g., `config_examples/ui_config.yaml`).
    *   **To customize (Recommended):**
        1.  Create a `user_config/` directory at the root of the project (i.e., at the same level as `src/` and `README.md`):
            ```bash
            mkdir -p user_config
            ```
            (The `user_config` directory might already exist if you cloned the repo, possibly containing a `.gitkeep` file. Its *contents* are typically gitignored.)
        2.  Copy the example configurations from `config_examples/` to your new `user_config/` directory:
            ```bash
            cp config_examples/ui_config.yaml user_config/
            cp config_examples/actions_config.yaml user_config/
            ```
        3.  Modify the YAML files within `user_config/` to define your custom pages, buttons, and actions. These files will take precedence over the defaults in `config_examples/`.

## Running the Application

Once the setup is complete and dependencies are installed, you can run the FastAPI application using Uvicorn:

