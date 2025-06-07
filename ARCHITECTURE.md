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

(This remains as previously described. Updates target buttons by ID; visibility depends on whether the button's page is currently active in the DOM.)

## Data Flow: Dynamic Configuration Update (Full Board)

(This remains as previously described, involving staging, applying, and client-side page refresh via `HX-Refresh` which reloads the entire application state including page navigation.)

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
