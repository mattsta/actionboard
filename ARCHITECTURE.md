# Visual Control Board - Architecture

This document outlines the architecture of the Visual Control Board application.

## Overview

The Visual Control Board is a web application designed to provide a customizable, grid-based interface of buttons. Clicking a button on the web UI triggers a predefined action on the server. The system emphasizes configurability and extensibility. Initial UI and action definitions are loaded from YAML files, and the entire configuration can be dynamically updated via an API. Furthermore, individual button content (text, icon, style) can be updated in real-time via WebSockets.

It leverages:
-   **Python**, **FastAPI**, **HTMX**, **Jinja2**, **YAML**, **Pydantic**, **WebSockets**, and **`uv`**.

## Core Components

1.  **Configuration System (`src/visual_control_board/config`, `project_root/user_config/`, `project_root/config_examples/`)**
    *   **Pydantic Models (`models.py`):** Define structures for `UIConfig`, `ActionsConfig`, `ButtonConfig`, `DynamicUpdateConfig` (for full config updates), and `ButtonContentUpdate` (for live individual button updates).
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
        *   Standard UI routes (`/`, `/action/{button_id}`).
        *   **Dynamic Configuration API (`/api/v1/config/` prefix):** For staging and applying full UI/action configuration updates (see previous descriptions).
        *   **Live Button Update API (`/api/v1/buttons/` prefix):**
            *   `POST /update_content`: Accepts a `ButtonContentUpdate` payload. Uses the `LiveUpdateManager` to broadcast this update to all connected WebSocket clients.
        *   **WebSocket Endpoint (`/ws/button_updates`):**
            *   Clients connect here to receive live updates. The `LiveUpdateManager` handles these connections.
    *   **Dependencies (`dependencies.py`):** Provide access to configurations, action registry, pending update flag, and the `LiveUpdateManager`.
    *   **HTML Templates (`templates/`):**
        *   `index.html`: Main page. Includes JavaScript to establish a WebSocket connection, listen for messages, and dynamically update button DOM elements based on received data.
        *   `partials/button.html`: Modified to include `data-` attributes for easier JS targeting of text, icon, and style properties.
        *   Other partials (`toast.html`, `update_banner.html`).
    *   **Static Assets (`static/`):** CSS, etc.

## Data Flow: Live Button Content Update

1.  **Client Connection:**
    *   User loads `index.html`.
    *   Client-side JavaScript establishes a WebSocket connection to `/ws/button_updates`.
    *   The `LiveUpdateManager` on the server accepts and stores this connection.
2.  **External Trigger for Update:**
    *   An external service (or an internal process) sends an HTTP `POST` request to `/api/v1/buttons/update_content`.
    *   The request body contains a JSON payload matching `ButtonContentUpdate` (e.g., `{"button_id": "temp_sensor_1", "text": "23.5°C"}`).
3.  **Backend Broadcast:**
    *   The `push_button_content_update` route handler receives the payload.
    *   It calls a method on the `LiveUpdateManager` (e.g., `broadcast_button_update`) with the update data.
    *   The `LiveUpdateManager` iterates through all active WebSocket connections and sends a JSON message (e.g., `{"type": "button_content_update", "payload": {"button_id": "temp_sensor_1", "text": "23.5°C"}}`) to each.
4.  **Client-Side DOM Update:**
    *   The JavaScript in `index.html` (listening on the WebSocket) receives the message.
    *   It parses the JSON data.
    *   It finds the HTML element for the specified `button_id` (e.g., `<button id="btn-temp_sensor_1">...</button>`).
    *   It updates the button's content directly in the DOM:
        *   Changes the text of the `span[data-role="button-text"]`.
        *   Updates the class of the `i[data-role="button-icon"]` or creates/removes it.
        *   Modifies the `classList` of the main button element to reflect the new `style_class`, using `data-current-style-class` to manage the previous dynamic style.
5.  **User Sees Live Change:** The button's appearance on the user's screen updates in real-time without a page reload.

## Data Flow: Dynamic Configuration Update (Full Board)

(This remains as previously described, involving staging, applying, and client-side page refresh via `HX-Refresh`.)

## Extensibility

*   **Adding New Buttons/Pages/Actions (Initial):** Via YAML files.
*   **Updating Full Configuration (Runtime):** Via the `/api/v1/config/stage` API.
*   **Pushing Live Button Content:** Via the `/api/v1/buttons/update_content` API.
*   **Custom Styling:** Via `style.css`.

## Future Considerations

*   **WebSocket Authentication/Authorization:** Secure the WebSocket endpoint if sensitive data is involved or if updates should be restricted.
*   **Scalability of `LiveUpdateManager`:** For a large number of connections, the in-memory list in `LiveUpdateManager` might become a bottleneck. Consider using a message broker like Redis Pub/Sub for broadcasting in such scenarios.
*   **More Sophisticated Client-Side State Management:** For very complex UIs with many live-updating elements, a more structured client-side approach (e.g., a minimal JavaScript framework or state management library) might be beneficial, though the goal here is to keep client-side JS light.
