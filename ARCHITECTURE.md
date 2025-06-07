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

(Remains as previously described.)

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

(Remains as previously described.)

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
