# Visual Control Board - Architecture

This document outlines the architecture of the Visual Control Board application.

## Overview

The Visual Control Board is a web application designed to provide a customizable, grid-based interface of buttons. Clicking a button on the web UI triggers a predefined action on the server. The system emphasizes configurability and extensibility, allowing users to define their own UI layouts and backend actions through simple YAML files.

It leverages:
-   **Python** as the primary programming language.
-   **FastAPI** as the high-performance web framework for the backend API and serving HTML.
-   **HTMX** for enhancing HTML to create dynamic frontend interactions with minimal custom JavaScript.
-   **Jinja2** for server-side HTML templating.
-   **YAML** for human-readable configuration files (UI layout and action definitions).
-   **Pydantic** for data validation, parsing, and settings management of configuration files.
-   **`uv`** for project dependency management and virtual environments.

## Core Components

The application is structured into several key components:

1.  **Configuration System (`src/visual_control_board/config`, `project_root/user_config/`, `project_root/config_examples/`)**
    *   **Pydantic Models (`models.py` in `src/visual_control_board/config`):** These define the expected structure and data types for configuration files (e.g., `UIConfig`, `PageConfig`, `ButtonConfig`, `ActionsConfig`, `ActionDefinition`). They provide robust validation and parsing of YAML data.
    *   **Configuration Loader (`loader.py` in `src/visual_control_board/config`):** The `ConfigLoader` class is responsible for:
        *   Reading `ui_config.yaml` and `actions_config.yaml`.
        *   Implementing a fallback strategy: It first attempts to load configurations from the `user_config/` directory (located at the project root, e.g., `project_root/user_config/ui_config.yaml`). This directory is intended for user-specific overrides and customizations.
        *   If configuration files are not found in `user_config/`, or if that directory doesn't exist, the loader falls back to using the default/example configurations packaged with the application in the `config_examples/` directory (e.g., `project_root/config_examples/ui_config.yaml`). This ensures the application can run out-of-the-box with sensible defaults.
    *   **User Override Configuration Files (`project_root/user_config/`):** This optional directory, typically created and managed by the user at the project root, can contain:
        *   `ui_config.yaml`: Defines the user's custom layout of pages, buttons (including text, icons, styles), and the `action_id` they trigger.
        *   `actions_config.yaml`: Defines the user's custom mappings from an `action_id` to a specific Python function (module and function name).
    *   **Default/Example Configuration Files (`project_root/config_examples/`):** These are provided as part of the application. They serve as runnable defaults if no user configurations are found and also act as templates for users wishing to create their own `user_config/` files.

2.  **Action Management (`src/visual_control_board/actions`)**
    *   **Built-in Actions (`built_in_actions.py`):** A collection of predefined Python functions that can be triggered by buttons (e.g., logging time, greeting a user). These serve as examples and can be used directly.
    *   **Action Registry (`registry.py`):** The `ActionRegistry` class is responsible for:
        *   Discovering and dynamically loading action functions based on the definitions in the loaded `actions_config.yaml`.
        *   Executing actions when requested, handling both synchronous and asynchronous (async/await) Python functions. It passes parameters defined in `ui_config.yaml` (`action_params`) to the target function.

3.  **Web Interface & API (`src/visual_control_board/web`, `src/visual_control_board/main.py`)**
    *   **Main Application (`main.py` in `src/visual_control_board/`):** Initializes the FastAPI application.
        *   On application startup (`@app.on_event("startup")`), it uses `ConfigLoader` to load all configurations and `ActionRegistry` to prepare all defined actions. These are stored in `app.state` for access via dependency injection.
        *   It mounts directories for static assets (CSS, client-side JS if any).
        *   It includes the API router for web endpoints.
    *   **API Routes (`routes.py` in `src/visual_control_board/web`):** Defines HTTP endpoints using FastAPI's `APIRouter`.
        *   `/` (GET): Serves the main HTML page, dynamically rendered using Jinja2 templates and the loaded `UIConfig`.
        *   `/action/{button_id}` (POST): Handles button click events sent by HTMX. It identifies the action, executes it via the `ActionRegistry`, and returns an HTML partial response (often including an updated button state and an out-of-band toast message for feedback).
    *   **Dependencies (`dependencies.py` in `src/visual_control_board/`):** FastAPI dependency functions that provide access to shared application state like the loaded `UIConfig`, `ActionsConfig`, and the `ActionRegistry` instance to route handlers.
    *   **HTML Templates (`templates/` in `src/visual_control_board/web`):** Jinja2 templates for rendering the main page (`index.html`) and partials (e.g., `button.html`, `toast.html`) used by HTMX for dynamic updates.
    *   **Static Assets (`static/` in `src/visual_control_board/`):** Contains CSS stylesheets (`style.css`) and potentially client-side JavaScript files or images.

## Data Flow (Example: Button Click)

1.  **Application Startup:**
    *   `main.py` initializes `ConfigLoader` and `ActionRegistry`.
    *   Configurations (`ui_config.yaml`, `actions_config.yaml`) are loaded (user overrides first, then examples).
    *   Actions are registered from `actions_config.yaml`.
2.  **User Interaction:**
    *   User navigates to the root URL (`/`).
    *   `routes.py` serves `index.html`, rendered with data from `UIConfig` (e.g., the first page and its buttons).
    *   User clicks a button on the web page.
3.  **HTMX Request:**
    *   The button (an HTML `<button>` element) has HTMX attributes (e.g., `hx-post="/action/{button_id}"`).
    *   HTMX sends an asynchronous POST request to the specified URL (e.g., `/action/greet_dev_button`).
4.  **Backend Processing:**
    *   FastAPI routes the request to the `handle_button_action` function in `routes.py`.
    *   Dependencies provide the `UIConfig` and `ActionRegistry` to the route handler.
    *   The handler uses `button_id` to find the `ButtonConfig` in `UIConfig`, retrieving its `action_id` and `action_params`.
    *   `ActionRegistry.execute_action(action_id, action_params)` is called.
    *   The `ActionRegistry` looks up the Python function associated with `action_id` and executes it (synchronously or asynchronously) with the provided `action_params`.
5.  **Response Generation:**
    *   The action function returns a result (typically a dictionary with `status` and `message`).
    *   The `handle_button_action` route handler uses this result to prepare an HTML response. This response usually includes:
        *   The re-rendered HTML for the button itself (for `hx-swap="outerHTML"`).
        *   An out-of-band (OOB) swapped HTML snippet for a toast notification (e.g., `partials/toast.html`) to provide feedback.
6.  **Frontend Update:**
    *   HTMX receives the HTML response.
    *   It swaps the original button with its new version from the response.
    *   It processes any OOB swaps, inserting the toast message into the designated container (`#toast-container`).
    *   The user sees the updated UI (e.g., button might appear pressed/reset, toast message appears).

## Extensibility

*   **Adding New Buttons/Pages:**
    *   Primarily involves modifying `ui_config.yaml` (preferably your copy in `user_config/`). Define new `PageConfig` or `ButtonConfig` entries following the Pydantic models.
*   **Adding New Actions:**
    1.  Write a new Python function (synchronous or asynchronous) in `src/visual_control_board/actions/built_in_actions.py` or your own custom Python module within the project.
    2.  Register this new function in `actions_config.yaml` (preferably your copy in `user_config/`) by adding a new `ActionDefinition` entry (specifying `id`, `module`, and `function`).
    3.  Reference the new action `id` in your `ui_config.yaml` under the desired button's `action_id` field.
*   **Custom Styling:** Modify `src/visual_control_board/static/css/style.css` or add new CSS files and link them in `index.html`. Button-specific styles can be applied using the `style_class` property in `ButtonConfig`.

## Future Considerations (Potential Features)

*   **Multi-Page Navigation:** The current system loads all pages from `UIConfig` but primarily displays the first one. True navigation between multiple defined pages would require frontend and backend changes (e.g., route parameters for page ID, navigation controls).
*   **Dynamic Button Content Updates:** The `ButtonConfig` includes a `dynamic_content_url` field. A future enhancement could involve client-side JavaScript polling this URL or server-side push mechanisms (e.g., WebSockets) to update button text, icons, or styles in real-time based on external system states.
*   **Sequence/Tree of Actions:** The current model supports one `action_id` per button. A more advanced feature would be to allow a button to trigger a defined sequence of actions, or a conditional tree of actions. This would require changes to `ButtonConfig` and `ActionRegistry` logic.
*   **More Sophisticated Layouts:** Beyond the current grid layout, support for other layout systems (e.g., flexbox configurations, user-defined dashboards) could be added.
*   **User Authentication & Authorization:** For environments requiring secure access, implementing user login and permissions for accessing the control board or specific actions.
*   **Configuration via UI:** Allowing users to modify parts of the configuration through the web interface itself, rather than just YAML files.
*   **Enhanced Action Parameter Typing:** While `ButtonActionParams` is flexible, actions requiring specific typed parameters could benefit from a system where Pydantic models for parameters are more directly tied to action definitions for automatic validation.
