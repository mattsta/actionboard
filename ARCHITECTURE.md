# Visual Control Board - Architecture

This document outlines the architecture of the Visual Control Board application.

## Overview

The Visual Control Board is a web application designed to provide a customizable, grid-based interface of buttons. Users can navigate between multiple configured "pages" (tabs), each displaying its own set of buttons. Clicking a button on the web UI triggers a predefined action on the server. The system emphasizes configurability and extensibility. Initial UI (including page structures) and action definitions are loaded from YAML files, and the entire configuration can be dynamically updated via an API. Furthermore, individual button content (text, icon, style) can be updated in real-time via WebSockets. Navigation tabs also update in real-time for all connected clients when the server configuration changes.

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
    *   **`LiveUpdateManager`:** A class responsible for managing active WebSocket connections. It handles client connections/disconnections and provides a method to broadcast messages (typically JSON payloads for button content updates or navigation update triggers) to all connected clients. Stored in `app.state`.

4.  **Web Interface & API (`src/visual_control_board/web`, `src/visual_control_board/main.py`)**
    *   **Main Application (`main.py`):** Initializes FastAPI.
        *   On startup, loads initial configs, sets up `app.state` (for current/staged configs, action registry), and instantiates the `LiveUpdateManager`.
    *   **API Routes (`routes.py`):**
        *   **UI Routes:**
            *   `/` and `/page/{page_id}`: Serve the main HTML page, displaying the specified page's content (or the first page by default). Navigation between pages is handled via HTMX requests to `/content/page/{page_id}`.
            *   `/content/page/{page_id}`: An HTMX-specific endpoint that returns HTML partials for the selected page's button grid, updated navigation state, page title, and header.
            *   `/content/navigation_panel`: An HTMX-specific endpoint that returns *only* the HTML for the navigation tabs. Used for live updates of the navigation area.
            *   `/action/{button_id}`: Handles button click actions.
        *   **Dynamic Configuration API (`/api/v1/config/` prefix):** For staging and applying full UI/action configuration updates.
        *   **Live Button Update API (`/api/v1/buttons/` prefix):**
            *   `POST /update_content`: Accepts a `ButtonContentUpdate` payload. Uses the `LiveUpdateManager` to broadcast this update to all connected WebSocket clients.
        *   **WebSocket Endpoint (`/ws/button_updates`):**
            *   Clients connect here to receive live updates for button content and navigation changes. The `LiveUpdateManager` handles these connections.
    *   **Dependencies (`dependencies.py`):** Provide access to configurations, action registry, pending update flag, and the `LiveUpdateManager`.
    *   **HTML Templates (`templates/`):**
        *   `index.html`: Main page structure. Includes a navigation area (tabs) and a content area that's dynamically updated by HTMX.
        *   `partials/nav.html`: Renders the navigation tabs. Includes `data-page-id` attributes on links for client-side identification.
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
    *   It updates the button's content directly in the DOM.
5.  **User Sees Live Change:** The button's appearance on the user's screen updates in real-time without a page reload.

## Data Flow: Dynamic Configuration Update (Full Board) & Live Navigation Update

1.  **Staging a New Configuration:** (Same as before)
    *   External system `POST`s to `/api/v1/config/stage` with new `ui_config` and `actions_config`.
    *   Server validates and stores them in `app.state.staged_*`.
    *   `pending_update_available` is set to `True`.
    *   Update banner HTML is returned to the initiating client.
2.  **User Interaction with Update Banner:** (Same as before)
3.  **Applying the Staged Configuration:**
    *   User (or script like `dynamic_board_controller.py`) triggers `POST` to `/api/v1/config/apply`.
    *   The `apply_staged_configuration` route handler:
        *   Moves configurations from `staged_*` to `current_*`.
        *   Re-initializes `action_registry`.
        *   Clears staged configs and `pending_update_available`.
        *   **Crucially, it now also calls `live_update_mgr.broadcast_json({"type": "navigation_update", "payload": {}})` to notify all connected WebSocket clients.**
        *   For the client that made the `/apply` request (if it's a browser via the banner button), it returns a response with the `HX-Refresh: true` header.
4.  **Client-Side Updates:**
    *   **Initiating Client (via UI Banner):** Detects `HX-Refresh: true` and performs a full page reload. The reloaded page will have the new navigation and content.
    *   **Other Connected Clients (and `dynamic_board_controller.py`'s effect on browsers):**
        *   The JavaScript in `static/js/main.js` receives the `{"type": "navigation_update"}` WebSocket message.
        *   The `refreshNavigationPanel()` JavaScript function is called.
        *   This function determines the client's current active page ID from the DOM.
        *   It makes an HTMX AJAX `GET` request to `/content/navigation_panel?active_page_id={id}`.
        *   The server responds with the HTML for the updated navigation tabs, rendered with the correct active tab.
        *   HTMX swaps this new HTML into the `#page-navigation` element.
        *   Users on these clients see the navigation tabs update (e.g., new tab appears/disappears) without a full page reload.
5.  **Discarding the Staged Configuration:** (Same as before)

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
*   **Content Sync on Nav Update:** If a live navigation update removes the currently viewed page for a client, its main content area won't automatically change until the user clicks a new tab. More sophisticated handling could redirect or clear content.
