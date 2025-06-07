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
    *   Customize initial setup via `user_config/`.

## Running the Application

