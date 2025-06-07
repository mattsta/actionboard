# Visual Control Board - Architecture

This document outlines the architecture of the Visual Control Board application.

## Overview

The Visual Control Board is a web application that provides a customizable, grid-based interface of buttons. Clicking a button triggers a predefined action on the server. The system is designed to be highly configurable and extensible.

It leverages:
-   **Python** as the primary programming language.
-   **FastAPI** as the web framework for the backend.
-   **HTMX** for dynamic frontend interactions with minimal JavaScript.
-   **Jinja2** for server-side HTML templating.
-   **YAML** for configuration files.
-   **Pydantic** for data validation and settings management.
-   **`uv`** for project and package management.

## Core Components

The application is composed of several key components:

1.  **Configuration (`src/visual_control_board/config`)**
    *   **Models (`models.py`):** Defines Pydantic models for structuring configuration data (e.g., `UIConfig`, `PageConfig`, `ButtonConfig`, `ActionsConfig`, `ActionDefinition`). These models ensure that configuration files are correctly formatted and provide type safety.
    *   **Loader (`loader.py`):** Responsible for loading and validating `ui_config.yaml` and `actions_config.yaml` from the `user_config` directory. It uses the Pydantic models for validation.
    *   **User Configuration Files (`user_config/`):**
        *   `ui_config.yaml`: Defines the layout of pages, buttons, their appearance (text, icons, styles), and which action they trigger.
        *   `actions_config.yaml`: Maps action IDs (used in `ui_config.yaml`) to specific Python functions (modules and function names).

2.  **Actions (`src/visual_control_board/actions`)**
    *   **Built-in Actions (`built_in_actions.py`):** A collection of predefined Python functions that can be triggered by buttons (e.g., logging time, greeting a user). Users can add their own action modules here or in separate files.
    *   **Registry (`registry.py`):** The `ActionRegistry` class is responsible for discovering and loading action functions based on `actions_config.yaml`. It dynamically imports modules and retrieves functions, making them available for execution by their ID. It handles both synchronous and asynchronous action functions.

3.  **Web Interface (`src/visual_control_board/web`)**
    *   **Main Application (`main.py` at project root):** Initializes the FastAPI application.
        *   Sets up logging.
        *   Mounts static file serving.
        *   Includes API routers.
        *   Manages application lifecycle events (`startup`, `shutdown`):
            *   On startup, it initializes `ConfigLoader` to load configurations and `ActionRegistry` to load actions. These are stored in `app.state` to be accessible via dependency injection.
    *   **Routes (`routes.py`):** Defines HTTP endpoints.
        *   `/`: Serves the main HTML page, rendering buttons based on `ui_config.yaml`.
        *   `/action/{button_id}` (POST): Handles button clicks triggered by HTMX. It identifies the button, retrieves its associated action and parameters, executes the action via the `ActionRegistry`, and returns an HTML response (typically re-rendering the button and providing a toast notification via HTMX Out-of-Band swaps).
    *   **Dependencies (`dependencies.py`):** FastAPI dependency functions to provide access to shared application state like `UIConfig`, `ActionsConfig`, and `ActionRegistry` within route handlers. This promotes cleaner code and better testability.
    *   **Templates (`templates/`):** Jinja2 HTML templates.
        *   `index.html`: The main page layout.
        *   `partials/button.html`: Template for rendering a single button.
        *   `partials/toast.html`: Template for rendering toast notifications.
    *   **Static Files (`static/`):** CSS stylesheets (`style.css`) and potentially JavaScript files.

## Data Flow (Button Click Example)

1.  **User Interaction:** User clicks a button in the web browser.
2.  **HTMX Request:** HTMX sends a POST request to the `/action/{button_id}` endpoint.
3.  **FastAPI Routing:** FastAPI routes the request to the `handle_button_action` function in `web/routes.py`.
4.  **Configuration & Action Retrieval:**
    *   The route handler uses dependency injection to get the `UIConfig` and `ActionRegistry`.
    *   It looks up the `ButtonConfig` for the given `button_id` in `UIConfig` to find the `action_id` and any `action_params`.
5.  **Action Execution:**
    *   The `ActionRegistry.execute_action(action_id, params)` method is called.
    *   The registry finds the corresponding Python function and executes it (synchronously or asynchronously).
6.  **Response Generation:**
    *   The action function returns a result (e.g., a dictionary with status and message).
    *   The route handler processes this result to create a user-facing feedback message.
7.  **HTMX Response:**
    *   The server renders two HTML partials:
        *   The updated button state (`partials/button.html`).
        *   A toast notification (`partials/toast.html`) marked for Out-of-Band (OOB) swapping.
    *   FastAPI returns this combined HTML to the client.
8.  **Frontend Update:**
    *   HTMX receives the response.
    *   It swaps the original button in the DOM with the new button HTML.
    *   It swaps the content of the `#toast-container` (or a specific element within it) with the new toast HTML due to the OOB swap directive.
    *   A small piece of JavaScript handles the display and auto-hiding of the toast.

## Extensibility

*   **Adding New Buttons/Pages:** Modify `user_config/ui_config.yaml`.
*   **Adding New Actions:**
    1.  Write a new Python function (e.g., in `actions/built_in_actions.py` or a new custom module).
    2.  Register this function in `user_config/actions_config.yaml` by providing an `id`, `module` path, and `function` name.
*   **Custom Styling:** Modify `static/css/style.css` or add new CSS classes referenced in `ui_config.yaml`.

## Future Considerations (Potential Features)

*   **Multi-Page Navigation:** The current setup serves the first page. A navigation system could be added.
*   **Dynamic Button Content:** The `dynamic_content_url` in `ButtonConfig` could be implemented to allow buttons to periodically fetch and update their text/icon from a URL.
*   **Action Sequences/Trees:** The `action_id` in `ButtonConfig` could be extended to support a list or a more complex structure to define a sequence or tree of actions.
*   **User Authentication & Authorization:** For sensitive actions, an authentication layer would be necessary.
*   **WebSockets for Real-time Updates:** For more immediate feedback or server-pushed updates to buttons, WebSockets could be integrated.
