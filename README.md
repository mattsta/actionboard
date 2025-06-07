# Visual Control Board

A web-based visual control board, inspired by devices like Elgato Stream Deck, built with Python, FastAPI, and HTMX. The UI is dynamically generated from configuration files, allowing users to define buttons that trigger backend actions. This version also supports dynamic updates to the entire board configuration via an API.

## Features

*   **Dynamic UI from Configuration:** Button layouts, appearances (text, icons, styles), and associated actions are defined in `ui_config.yaml`.
*   **Pluggable Actions:** Button actions are mapped to Python functions via `actions_config.yaml`, allowing for easy extension and customization of backend operations.
*   **User-Managed Overrides:** Customize by placing your `ui_config.yaml` and `actions_config.yaml` in a `user_config/` directory at the project root. These files will override the default example configurations on initial startup.
*   **Runs Out-of-the-Box:** Comes with default example configurations in `config_examples/`.
*   **HTMX Powered Frontend:** Rich user interactions (like button clicks, feedback toasts, and dynamic configuration update notifications) with minimal custom JavaScript.
*   **FastAPI Backend:** Modern, fast Python web framework.
*   **Dynamic Configuration API:**
    *   Allows external services to propose a new UI and Actions configuration via a `POST` request to `/api/v1/config/stage`.
    *   Staged configurations are validated (including action loadability).
    *   Users are notified in the UI about pending updates and can choose to `Apply` or `Discard` them.
    *   Applying an update refreshes the entire board and action registry.
*   **Dependency Injection:** Core components are managed via FastAPI's dependency injection.
*   **Centralized Logging & Asynchronous Support.**
*   **`uv` Managed Project.**

## Architecture

For a detailed understanding of the project's components, data flow, and extensibility, including the dynamic configuration update mechanism, please refer to the [ARCHITECTURE.md](ARCHITECTURE.md) document.

## Prerequisites

*   Python 3.8+
*   `uv` (Python package installer and virtual environment manager).

## Setup and Installation

1.  **Clone the repository.**
2.  **Create and activate a virtual environment using `uv`:**
    ```bash
    uv venv
    source .venv/bin/activate  # Or equivalent for your shell
    ```
3.  **Install dependencies:**
    ```bash
    uv pip install -e .[dev]
    ```
4.  **Initial Configuration (Optional):**
    *   To customize the initial setup, create `user_config/` at the project root and copy/modify configurations from `config_examples/`.

## Running the Application

