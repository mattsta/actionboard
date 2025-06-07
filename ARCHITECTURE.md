# Visual Control Board - Architecture

This document outlines the architecture of the Visual Control Board application.

## Overview

The Visual Control Board is a web application designed to provide a customizable, grid-based interface of buttons. Users can navigate between multiple configured "pages" (tabs), each displaying its own set of buttons. Clicking a button on the web UI triggers a predefined action on the server. The system emphasizes configurability and extensibility. Initial UI (including page structures) and action definitions are loaded from YAML files, and the entire configuration can be dynamically updated via an API. Furthermore, individual button content (text, icon, style, or SVG sparkline) can be updated in real-time via WebSockets. Navigation tabs also update in real-time for all connected clients when the server configuration changes.

It leverages:
-   **Python**, **FastAPI**, **HTMX**, **Jinja2**, **YAML**, **Pydantic**, **WebSockets**, and **`uv`**.

## Core Components

1.  **Configuration System (`src/visual_control_board/config`, `project_root/user_config/`, `project_root/config_examples/`)**
    *   **Pydantic Models (`models.py`):** Define structures for `UIConfig`, `PageConfig`, `ButtonConfig`, `ActionsConfig`, `DynamicUpdateConfig`, `ButtonContentUpdate`, and `SparklinePayload`. `ButtonContentUpdate` now supports an optional `sparkline` field to send data for SVG sparklines.
    *   **Configuration Loader (`loader.py`):** Handles loading initial configurations from files at startup.

2.  **Action Management (`src/visual_control_board/actions`)**
    *   **Built-in Actions (`built_in_actions.py`):** Example Python functions.
    *   **Action Registry (`registry.py`):** Dynamically loads and executes action functions. Re-initialized when new full configurations are applied.

3.  **Live Update Management (`src/visual_control_board/live_updates.py`)**
    *   **`LiveUpdateManager`:** Manages active WebSocket connections and broadcasts messages (button content, sparklines, navigation triggers) to clients.

4.  **Web Interface & API (`src/visual_control_board/web`, `src/visual_control_board/main.py`)**
    *   **Main Application (`main.py`):** Initializes FastAPI, loads configs, sets up `app.state`.
    *   **API Routes (`routes.py`):**
        *   **UI Routes:** Serve main HTML, handle page navigation, and button actions. Includes `/content/navigation_panel` for live nav updates.
        *   **Dynamic Configuration API (`/api/v1/config/`):** For staging and applying full UI/action configuration updates.
        *   **Live Button Update API (`/api/v1/buttons/update_content`):** Accepts `ButtonContentUpdate` payloads, now including optional `sparkline` data.
        *   **WebSocket Endpoint (`/ws/button_updates`):** For clients to receive live updates (button content, sparklines, navigation).
    *   **Dependencies (`dependencies.py`):** Provide access to shared resources.
    *   **HTML Templates (`templates/`):**
        *   `index.html`: Main page structure.
        *   `partials/nav.html`: Navigation tabs.
        *   `partials/page_content.html`: Button grid for a page.
        *   `partials/button.html`: Renders a single button. Now includes an `<svg data-role="button-sparkline">` element, and a `div.button-graphic-area` to contain either the icon or the sparkline.
        *   Other partials for titles, toast, update banner.
    *   **Static Assets (`static/`):**
        *   `css/style.css`: Styles for buttons, SVG sparklines, and layout.
        *   `js/main.js`: Client-side JavaScript for WebSocket handling and DOM manipulation, including `renderSparkline` function to draw SVGs.

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

## Data Flow: Live Button Content Update (Icon or Sparkline)

1.  **WebSocket Connection Setup:** (Same as before)
2.  **External Trigger for Update:**
    *   An external service sends an HTTP `POST` to `/api/v1/buttons/update_content`.
    *   The payload can now include:
        *   `icon_class` for FontAwesome icons.
        *   `sparkline: {"data": [1,2,3,...], "color": "#hex", "stroke_width": 2}` for SVG sparklines.
        *   `text` and `style_class` as before.
3.  **Backend Broadcast:** (Same as before) The `LiveUpdateManager` broadcasts the JSON payload.
4.  **Client-Side DOM Update (`js/main.js`):**
    *   The `updateButtonContent` function in JavaScript receives the message.
    *   **If `sparkline` data is present:**
        *   Hides the `i[data-role="button-icon"]` element.
        *   Shows the `svg[data-role="button-sparkline"]` element.
        *   Calls `renderSparkline(svgElement, sparklinePayload)` which:
            *   Normalizes data points to the SVG's `viewBox`.
            *   Generates an SVG `<path>` string.
            *   Sets the path data, stroke color, and width on the SVG path.
    *   **Else if `icon_class` data is present:**
        *   Hides the `svg[data-role="button-sparkline"]` element.
        *   Shows/updates the `i[data-role="button-icon"]` element.
    *   Updates text and style class as before.
5.  **User Sees Live Change:** The button's icon, sparkline, or text updates in real-time.

## Data Flow: Dynamic Configuration Update (Full Board) & Live Navigation Update

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
    *   User (or script like `dynamic_board_controller.py`) triggers `POST` to `/api/v1/config/apply`.
    *   The `apply_staged_configuration` route handler:
        *   Moves configurations from `staged_*` to `current_*` in `app.state`.
        *   Re-initializes the main `app.state.action_registry` with the new `current_actions_config`.
        *   Clears the `staged_*` configurations and sets `pending_update_available = False`.
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
        *   HTMX swaps this new HTML into the `#page-navigation` element using `outerHTML` swap.
        *   `htmx.process()` is then called on the new `#page-navigation` element to initialize HTMX behaviors on the new links.
        *   Users on these clients see the navigation tabs update (e.g., new tab appears/disappears) without a full page reload.
5.  **Discarding the Staged Configuration:**
    *   User clicks "Discard".
    *   HTMX sends a `POST` request to `/api/v1/config/discard`.
    *   The `discard_staged_configuration` route handler:
        *   Clears the `staged_*` configurations and sets `pending_update_available = False`.
        *   Returns an HTML partial (`partials/update_banner.html` rendered as hidden) to clear the banner from the UI.

## Extensibility

*   **Adding New Buttons/Pages/Actions (Initial):** Via YAML files.
*   **Updating Full Configuration (Runtime):** Via the `/api/v1/config/stage` API.
*   **Pushing Live Button Content:** Via the `/api/v1/buttons/update_content` API, now supporting sparklines.
*   **Custom Styling:** Via `style.css`.

## Future Considerations

*   **Multi-line Sparklines:** Extend `SparklinePayload` and `renderSparkline` to support multiple data series with different colors.
*   **Static Sparkline Configuration:** Allow defining initial sparkline appearance (e.g., default data, viewbox) in `ui_config.yaml` via `ButtonConfig`.
*   **More SVG Customization:** Allow more SVG attributes (e.g., fill, different path types) to be sent via API.
*   (Other considerations remain as previously listed.)
