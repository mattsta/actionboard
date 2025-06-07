# Visual Control Board - Architecture

This document outlines the architecture of the Visual Control Board application.

## Overview

The Visual Control Board is a web application designed to provide a customizable, grid-based interface of buttons. Users can navigate between multiple configured "pages" (tabs), each displaying its own set of buttons. Clicking a button on the web UI triggers a predefined action on the server. The system emphasizes configurability and extensibility. Initial UI (including page structures) and action definitions are loaded from YAML files, and the entire configuration can be dynamically updated via an API. Furthermore, individual button content (text, icon, style) can be updated in real-time via WebSockets.

It leverages:
-   **Python**, **FastAPI**, **HTMX**, **Jinja2**, **YAML**, **Pydantic**, **WebSockets**, and **`uv`**.

## Core Components

1.  **Configuration System (`src/visual_control_board/config`, `project_root/user_config/`, `project_root/config_examples/`)**
    *   **Pydantic Models (`models.py`):** Define structures for `UIConfig` (which includes a list of `PageConfig` objects), `ActionsConfig`, `ButtonConfig`, `DynamicUpdateConfig` (for full config updates), and `ButtonContentUpdate` (for live individual button updates).
    *   **Configuration Loader (`loader.py`):** Handles loading initial configurations from files at startup.

2.  **Action Management (`src/visual_control_board/actions`)**
    *   **Built-in Actions (`built_in_actions.py`):** Example Python functions.
    *   **Action Registry (`registry.py`):** Dynamically loads and executes action functions. Re-initialized when new full configurations are applied.

3.  **Live Update Management (`src/visual_control_board/live_updates.py`)**
    *   **`LiveUpdateManager`:** A class responsible for managing active WebSocket connections. It handles client connections/disconnections and provides a method to broadcast messages (typically JSON payloads for button content updates) to all connected clients. Stored in `app.state`.

4.  **Web Interface & API (`src/visual_control_board/web`, `src/visual_control_board/main.py`)**
    *   **Main Application (`main.py`):** Initializes FastAPI.
        *   On startup, loads initial configs, sets up `app.state` (for current/staged configs, action registry), and instantiates the `LiveUpdateManager`.
    *   **API Routes (`routes.py`):**
        *   **UI Routes:**
            *   `/` and `/page/{page_id}`: Serve the main HTML page, displaying the specified page's content (or the first page by default). Navigation between pages is handled via HTMX requests to `/content/page/{page_id}`.
            *   `/content/page/{page_id}`: An HTMX-specific endpoint that returns HTML partials for the selected page's button grid, updated navigation state, page title, and header.
            *   `/action/{button_id}`: Handles button click actions.
        *   **Dynamic Configuration API (`/api/v1/config/` prefix):** For staging and applying full UI/action configuration updates.
        *   **Live Button Update API (`/api/v1/buttons/` prefix):**
            *   `POST /update_content`: Accepts a `ButtonContentUpdate` payload. Uses the `LiveUpdateManager` to broadcast this update to all connected WebSocket clients.
        *   **WebSocket Endpoint (`/ws/button_updates`):**
            *   Clients connect here to receive live updates. The `LiveUpdateManager` handles these connections.
    *   **Dependencies (`dependencies.py`):** Provide access to configurations, action registry, pending update flag, and the `LiveUpdateManager`.
    *   **HTML Templates (`templates/`):**
        *   `index.html`: Main page structure. Includes a navigation area (tabs) and a content area that's dynamically updated by HTMX.
        *   `partials/nav.html`: Renders the navigation tabs.
        *   `partials/page_content.html`: Renders the button grid for a specific page.
        *   `partials/button.html`: Modified to include `data-` attributes for easier JS targeting of text, icon, and style properties.
        *   `partials/title_tag.html`, `partials/header_title_tag.html`: For OOB swapping of document title and H1 header.
        *   Other partials (`toast.html`, `update_banner.html`).
    *   **Static Assets (`static/`):** CSS, client-side JavaScript (`main.js`).

## Data Flow: Page Navigation (HTMX)

1.  **Initial Load:**
    *   User navigates to `/` (or `/page/{default_page_id}`).
    *   The server renders `index.html`, including the navigation tabs (`partials/nav.html`) with the default page marked active, and the button grid (`partials/page_content.html`) for the default page.
2.  **User Clicks a Tab:**
    *   The clicked tab (an `<a>` tag) has HTMX attributes (e.g., `hx-get="/content/page/{new_page_id}"`, `hx-target="#page-content-area"`).
    *   HTMX makes an AJAX GET request to `/content/page/{new_page_id}`.
3.  **Backend Response for Page Content:**
    *   The `/content/page/{new_page_id}` route handler:
        *   Retrieves the `PageConfig` for `{new_page_id}`.
        *   Renders the button grid for this page using `partials/page_content.html`.
        *   Renders the navigation tabs again using `partials/nav.html`, marking the `{new_page_id}` tab as active. This HTML is intended for an Out-of-Band (OOB) swap.
        *   Renders updated `<title>` and `<h1>` tags using respective partials, also for OOB swaps.
        *   Returns a combined HTML response containing the main page content and the OOB partials.
4.  **Client-Side DOM Update (HTMX):**
    *   HTMX receives the response.
    *   It swaps the main content (button grid) into the `#page-content-area` div.
    *   It processes OOB swaps: updates the navigation tabs in `#page-navigation`, the `<title>` tag, and the `<h1>` tag.
    *   The URL is updated via `hx-push-url` if configured on the tab link.
5.  **User Sees New Page:** The selected page's buttons and title are displayed without a full page reload.

## Data Flow: Live Button Content Update

1.  **WebSocket Connection Setup:**
    *   User loads `index.html`.
    *   Client-side JavaScript in `static/js/main.js` establishes a WebSocket connection to `/ws/button_updates`.
    *   The `LiveUpdateManager` on the server accepts and stores this connection.
2.  **External Trigger for Update:**
    *   An external service (or an internal process) sends an HTTP `POST` request to `/api/v1/buttons/update_content`.
    *   The request body contains a JSON payload matching `ButtonContentUpdate` (e.g., `{"button_id": "temp_sensor_1", "text": "23.5°C"}`).
3.  **Backend Broadcast:**
    *   The `push_button_content_update` route handler receives the payload.
    *   It calls a method on the `LiveUpdateManager` (e.g., `broadcast_button_update`) with the update data.
    *   The `LiveUpdateManager` iterates through all active WebSocket connections and sends a JSON message (e.g., `{"type": "button_content_update", "payload": {"button_id": "temp_sensor_1", "text": "23.5°C"}}`) to each.
4.  **Client-Side DOM Update:**
    *   The JavaScript in `static/js/main.js` (listening on the WebSocket) receives the message.
    *   It parses the JSON data.
    *   It finds the HTML element for the specified `button_id` (e.g., `<button id="btn-temp_sensor_1">...</button>`).
    *   It updates the button's content directly in the DOM:
        *   Changes the text of the `span[data-role="button-text"]`.
        *   Updates the class of the `i[data-role="button-icon"]` or creates/removes it.
        *   Modifies the `classList` of the main button element to reflect the new `style_class`, using `data-current-style-class` to manage the previous dynamic style.
5.  **User Sees Live Change:** The button's appearance on the user's screen updates in real-time without a page reload.

## Data Flow: Dynamic Configuration Update (Full Board)

1.  **Staging a New Configuration:**
    *   An external system (e.g., a script, another service, or a manual `curl` command) sends an HTTP `POST` request to `/api/v1/config/stage`.
    *   The request body contains a JSON payload matching `DynamicUpdateConfig`, which includes both a full `ui_config` and `actions_config`.
    *   The `stage_new_configuration` route handler:
        *   Validates the new `actions_config` by attempting to load them into a temporary `ActionRegistry`. If any action fails to load (e.g., module not found, function not found), it returns an error.
        *   If validation passes, stores the new `ui_config` and `actions_config` in `request.app.state.staged_ui_config` and `request.app.state.staged_actions_config`.
        *   Sets `request.app.state.pending_update_available = True`.
        *   Returns an HTML partial (`partials/update_banner.html`) indicating an update is available. This partial is swapped into the `#update-notification-area` on the client via HTMX's OOB swap.
2.  **User Interaction with Update Banner:**
    *   The user sees the banner with "Apply Update" and "Discard" buttons.
3.  **Applying the Staged Configuration:**
    *   User clicks "Apply Update".
    *   HTMX sends a `POST` request to `/api/v1/config/apply`.
    *   The `apply_staged_configuration` route handler:
        *   Moves the configurations from `staged_*` to `current_*` in `app.state`.
        *   Re-initializes the main `app.state.action_registry` with the new `current_actions_config`.
        *   Clears the `staged_*` configurations and sets `pending_update_available = False`.
        *   Returns a response with the `HX-Refresh: true` header.
4.  **Client-Side Page Refresh:**
    *   HTMX detects the `HX-Refresh: true` header and performs a full page reload.
    *   The application now serves content based on the new `current_ui_config` and uses the updated `action_registry`. The page navigation structure will also be updated.
5.  **Discarding the Staged Configuration:**
    *   User clicks "Discard".
    *   HTMX sends a `POST` request to `/api/v1/config/discard`.
    *   The `discard_staged_configuration` route handler:
        *   Clears the `staged_*` configurations and sets `pending_update_available = False`.
        *   Returns an HTML partial (`partials/update_banner.html` rendered as hidden) to clear the banner from the UI.

## Extensibility

*   **Adding New Buttons/Pages/Actions (Initial):** Via YAML files. `ui_config.yaml` now defines multiple pages.
*   **Updating Full Configuration (Runtime):** Via the `/api/v1/config/stage` API.
*   **Pushing Live Button Content:** Via the `/api/v1/buttons/update_content` API.
*   **Custom Styling:** Via `style.css`.

## Future Considerations

*   **WebSocket Authentication/Authorization:** Secure the WebSocket endpoint if sensitive data is involved or if updates should be restricted.
*   **Scalability of `LiveUpdateManager`:** For a large number of connections, the in-memory list in `LiveUpdateManager` might become a bottleneck. Consider using a message broker like Redis Pub/Sub for broadcasting in such scenarios.
*   **More Sophisticated Client-Side State Management:** For very complex UIs with many live-updating elements, a more structured client-side approach (e.g., a minimal JavaScript framework or state management library) might be beneficial, though the goal here is to keep client-side JS light.
*   **Persistence of Current Page:** Currently, refreshing the browser will revert to the default page (or the page specified in the URL if `hx-push-url` is used effectively). User's last selected tab could be persisted (e.g., in localStorage or a cookie) for a more seamless experience across sessions, though this adds client-side complexity.
