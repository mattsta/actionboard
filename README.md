# Visual Control Board

A web-based visual control board, inspired by devices like Elgato Stream Deck, built with Python, FastAPI, and HTMX. The UI is dynamically generated from configuration files, allowing users to define buttons that trigger backend actions.

## Features

*   **Dynamic UI:** Button layouts and appearances are defined in a YAML configuration file (`ui_config.yaml`).
*   **Pluggable Actions:** Button actions are mapped to Python functions defined in `actions_config.yaml`, allowing for easy extension by adding new Python modules and functions.
*   **Web Interface:** Accessible from any web browser on the local network.
*   **HTMX Powered:** Rich user interactions with minimal JavaScript.
*   **FastAPI Backend:** Modern, fast Python web framework.
*   **Dependency Injection:** Core components like configuration and action registry are managed via FastAPI's dependency injection for better testability and maintainability.
*   **Centralized Logging:** Standardized logging for application events.
*   **`uv` Managed:** Uses `uv` for package management.

## Project Structure

(The project structure remains largely the same, refer to `ARCHITECTURE.md` for component details)
