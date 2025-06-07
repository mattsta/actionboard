# Visual Control Board - Examples

This directory contains example scripts that demonstrate how to interact with and control the Visual Control Board application programmatically.

## `dynamic_board_controller.py`

This script showcases the dynamic capabilities of the Visual Control Board API:

*   **Loading Initial Configuration:** It starts by loading the default `ui_config.yaml` and `actions_config.yaml` from the `config_examples/` directory.
*   **Adding a New Page (Tab):** Demonstrates how to add a new page to the UI by modifying the loaded UI configuration and applying it to the running VCB server.
*   **Adding a New Button:** Shows how to add a new button to the newly created page.
*   **Live Button Content Updates:** Continuously updates the text and icon of the newly added button in real-time using the `/api/v1/buttons/update_content` endpoint.

### Prerequisites

*   A running instance of the Visual Control Board server (e.g., `uvicorn src.visual_control_board.main:app --reload --host 0.0.0.0 --port 8000`).
*   Python 3.x installed.
*   Required Python packages:
    ```bash
    pip install requests pyyaml
    ```
    (These are likely already installed if you have the main VCB application's dependencies. `PyYAML` is in `pyproject.toml`, `requests` might need to be installed separately if not already present in your environment.)

### Running the Example

1.  Ensure the Visual Control Board server is running.
2.  Navigate to the root directory of the `visual-control-board` project in your terminal.
3.  Run the script:
    ```bash
    python examples/dynamic_board_controller.py
    ```

Observe the terminal output from the script and the changes in your Visual Control Board web interface. You should see a new tab appear, then a new button on that tab, and finally, the button's text and icon will start changing live.
