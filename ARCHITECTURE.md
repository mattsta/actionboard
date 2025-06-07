# Visual Control Board - Architecture

This document outlines the architecture of the Visual Control Board application.

## Overview

The Visual Control Board is a web application designed to provide a customizable, grid-based interface of buttons. Clicking a button on the web UI triggers a predefined action on the server. The system emphasizes configurability and extensibility, allowing users to define their own UI layouts and backend actions through simple YAML files for initial setup, and programmatically via an API for dynamic updates during runtime.

It leverages:
-   **Python**, **FastAPI**, **HTMX**, **Jinja2**, **YAML**, **Pydantic**, and **`uv`**.

## Core Components

1.  **Configuration System (`src/visual_control_board/config`, `project_root/user_config/`, `project_root/config_examples/`)**
    *   **Pydantic Models (`models.py`):** Define structures for `UIConfig`, `ActionsConfig`, `ButtonConfig`, etc., and a `DynamicUpdateConfig` for API-based updates.
    *   **Configuration Loader (`loader.py`):** Handles loading initial configurations from files (`user_config/` then `config_examples/`) at startup.
    *   **Configuration Files:** YAML files for default and user-override initial setups.

2.  **Action Management (`src/visual_control_board/actions`)**
    *   **Built-in Actions (`built_in_actions.py`):** Example Python functions.
    *   **Action Registry (`registry.py`):** Dynamically loads and executes action functions based on the *current* `ActionsConfig`. It is re-initialized when new configurations are applied.

3.  **Web Interface & API (`src/visual_control_board/web`, `src/visual_control_board/main.py`)**
    *   **Main Application (`main.py`):** Initializes FastAPI.
        *   On startup, loads initial configs and sets up application state (`app.state`) to hold:
            *   `current_ui_config`, `current_actions_config`: The active configurations.
            *   `staged_ui_config`, `staged_actions_config`: Configurations pending user approval via API.
            *   `action_registry`: Instance for the current actions.
            *   `pending_update_available`: Boolean flag.
    *   **API Routes (`routes.py`):**
        *   Standard UI routes (`/`, `/action/{button_id}`).
        *   **Dynamic Configuration API (`/api/v1/config/` prefix):**
            *   `POST /stage`: Accepts a `DynamicUpdateConfig`. Validates (including action loadability check using a temporary `ActionRegistry`) and stages it. Returns an HTMX OOB swap to show an "Update Available" banner.
            *   `POST /apply`: Promotes staged configurations to current, re-initializes the main `ActionRegistry`, clears staged data, and sends `HX-Refresh: true` to clients.
            *   `POST /discard`: Clears staged configurations and updates the banner via OOB swap.
    *   **Dependencies (`dependencies.py`):** Provide access to `current_ui_config`, `current_actions_config`, `action_registry`, and `pending_update_available` flag.
    *   **HTML Templates (`templates/`):**
        *   `index.html`: Main page, includes an area for an `update_banner.html` partial.
        *   `partials/button.html`, `partials/toast.html`.
        *   `partials/update_banner.html`: Displays "Update Available" message with Apply/Discard buttons, managed via HTMX OOB swaps.
    *   **Static Assets (`static/`):** CSS, etc. Includes styles for the update banner.

## Data Flow: Dynamic Configuration Update

1.  **External Request:** An external service sends a `POST` request to `/api/v1/config/stage` with a JSON payload containing new `ui_config` and `actions_config`.
2.  **Staging & Validation:**
    *   The `stage_new_configuration` route handler in `routes.py` receives the request.
    *   Pydantic validates the structure of the incoming `DynamicUpdateConfig`.
    *   A temporary `ActionRegistry` is used to attempt loading actions from the proposed `actions_config`. If any actions fail to load (e.g., module/function not found), a `400 Bad Request` is returned.
    *   If all validations pass, the `ui_config` and `actions_config` are stored in `app.state.staged_ui_config` and `app.state.staged_actions_config`. `app.state.pending_update_available` is set to `True`.
3.  **UI Notification:**
    *   The `/stage` endpoint returns an HTML partial (`update_banner.html` rendered with `pending_update_available=True`) with `hx-swap-oob="true"`.
    *   HTMX on the client side swaps this banner into the `#update-notification-area` (or a specific `#update-banner` div) in `index.html`. The user now sees "Update Available" with "Apply" and "Discard" buttons.
4.  **User Action (Apply):**
    *   User clicks the "Apply" button.
    *   HTMX sends a `POST` request to `/api/v1/config/apply`.
    *   The `apply_staged_configuration` route handler:
        *   Moves data from `app.state.staged_...` to `app.state.current_...`.
        *   Creates a new `ActionRegistry` instance, loads actions from the new `current_actions_config`, and updates `app.state.action_registry`.
        *   Resets `app.state.staged_...` to `None` and `pending_update_available` to `False`.
        *   Returns a response with the `HX-Refresh: true` header.
5.  **Client Refresh:** HTMX processes `HX-Refresh: true`, causing a full reload of the web page. The `get_index_page` route now serves content based on the new `current_ui_config`.
6.  **User Action (Discard):**
    *   User clicks the "Discard" button.
    *   HTMX sends a `POST` request to `/api/v1/config/discard`.
    *   The `discard_staged_configuration` route handler:
        *   Resets `app.state.staged_...` to `None` and `pending_update_available` to `False`.
        *   Returns an HTML partial (`update_banner.html` rendered with `pending_update_available=False`) with `hx-swap-oob="true"`, effectively hiding or clearing the banner.

## Extensibility

*   **Adding New Buttons/Pages/Actions (Initial):** Via YAML files in `user_config/` or `config_examples/`.
*   **Updating Configuration (Runtime):** Via the `/api/v1/config/stage` API endpoint.
*   **Custom Styling:** Via `style.css`.

## Future Considerations (Potential Features)

*   **Live Button Content Updates (Streaming):** Implement WebSocket endpoint for real-time updates to individual button faces (text, icons, styles) from external data feeds. This would involve client-side JS/HTMX WebSocket handling.
*   **More Granular API Updates:** APIs to update specific pages or buttons instead of the entire configuration.
*   **Authentication/Authorization:** Secure the dynamic configuration API endpoints.
*   **Multi-Page Navigation.**
