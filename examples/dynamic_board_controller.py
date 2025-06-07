import requests
import time
import random
import yaml
from pathlib import Path
import sys
import math

# --- Configuration ---
VCB_SERVER_URL = "http://localhost:8000"  # Base URL of your VCB server
VCB_API_BASE_URL = f"{VCB_SERVER_URL}/api/v1"
CONFIG_STAGE_URL = f"{VCB_API_BASE_URL}/config/stage"
CONFIG_APPLY_URL = f"{VCB_API_BASE_URL}/config/apply"
BUTTON_UPDATE_URL = f"{VCB_API_BASE_URL}/buttons/update_content"

# Determine project root and paths to example configurations
# Assumes this script is in an 'examples' directory at the project root.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
EXAMPLE_UI_CONFIG_PATH = PROJECT_ROOT / "config_examples" / "ui_config.yaml"
EXAMPLE_ACTIONS_CONFIG_PATH = PROJECT_ROOT / "config_examples" / "actions_config.yaml"

# Global dictionary to hold the current state of UI and Actions configurations
# This script modifies this local representation and then pushes the whole thing.
current_config = {"ui_config": None, "actions_config": None}

# --- Helper Functions ---


def load_initial_configs_from_examples():
    """Loads UI and Actions configurations from the project's example files."""
    print("Loading initial configurations from example files...")
    try:
        if not EXAMPLE_UI_CONFIG_PATH.exists():
            print(f"ERROR: Example UI config not found at {EXAMPLE_UI_CONFIG_PATH}")
            sys.exit(1)
        if not EXAMPLE_ACTIONS_CONFIG_PATH.exists():
            print(
                f"ERROR: Example Actions config not found at {EXAMPLE_ACTIONS_CONFIG_PATH}"
            )
            sys.exit(1)

        with open(EXAMPLE_UI_CONFIG_PATH, "r") as f:
            current_config["ui_config"] = yaml.safe_load(f)
        with open(EXAMPLE_ACTIONS_CONFIG_PATH, "r") as f:
            current_config["actions_config"] = yaml.safe_load(f)

        if current_config["ui_config"] and current_config["actions_config"]:
            print("Successfully loaded initial example configurations.")
        else:
            print(
                "ERROR: Failed to load or parse one or both example configuration files."
            )
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: Could not load initial configurations: {e}")
        sys.exit(1)


def stage_and_apply_current_config():
    """Stages and then applies the global 'current_config' to the VCB server."""
    if not current_config["ui_config"] or not current_config["actions_config"]:
        print("ERROR: UI or Actions config is not loaded. Cannot apply.")
        return False

    payload = {
        "ui_config": current_config["ui_config"],
        "actions_config": current_config["actions_config"],
    }
    try:
        print("Staging new configuration...")
        response_stage = requests.post(CONFIG_STAGE_URL, json=payload, timeout=10)
        response_stage.raise_for_status()
        print(
            f"Configuration staged successfully. Server response: {response_stage.status_code}"
        )

        print("Applying staged configuration...")
        response_apply = requests.post(CONFIG_APPLY_URL, timeout=10)
        response_apply.raise_for_status()
        print(
            f"Configuration applied successfully. Server response: {response_apply.json()}"
        )
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to stage or apply configuration.")
        if hasattr(e, "response") and e.response is not None:
            print(
                f"Status Code: {e.response.status_code}, Response: {e.response.text[:500]}"
            )
        else:
            print(f"Error details: {e}")
        return False


def add_new_page(page_id: str, page_name: str, columns: int = 2):
    """Adds a new page to the 'current_config["ui_config"]'."""
    print(f"\nAttempting to add new page: ID='{page_id}', Name='{page_name}'")
    ui_conf = current_config["ui_config"]
    if "pages" not in ui_conf or not isinstance(ui_conf["pages"], list):
        ui_conf["pages"] = []

    # Check if page already exists
    if any(p.get("id") == page_id for p in ui_conf["pages"]):
        print(f"Page with ID '{page_id}' already exists. Skipping addition.")
        return True  # Considered success as the page is there

    new_page = {
        "name": page_name,
        "id": page_id,
        "layout": "grid",
        "grid_columns": columns,
        "buttons": [],
    }
    ui_conf["pages"].append(new_page)
    print(f"Page '{page_name}' added to local configuration.")
    # This function now only modifies the local config.
    # stage_and_apply_current_config() should be called after all modifications are done.
    return True


def add_button_to_page(
    page_id: str,
    button_id: str,
    button_text: str,
    action_id: str = "log_current_time_action",
    icon: str = "fas fa-cube",
    style_class: str = None,
):
    """Adds a new button to a specified page in 'current_config["ui_config"]'."""
    print(f"\nAttempting to add button: ID='{button_id}' to Page ID='{page_id}'")
    ui_conf = current_config["ui_config"]

    target_page = None
    for p in ui_conf.get("pages", []):
        if p.get("id") == page_id:
            target_page = p
            break

    if not target_page:
        print(f"ERROR: Page with ID '{page_id}' not found. Cannot add button.")
        return False

    if "buttons" not in target_page or not isinstance(target_page["buttons"], list):
        target_page["buttons"] = []

    # Check if button already exists
    if any(b.get("id") == button_id for b in target_page["buttons"]):
        print(
            f"Button with ID '{button_id}' already exists on page '{page_id}'. Skipping addition."
        )
        return True  # Considered success

    new_button = {
        "id": button_id,
        "text": button_text,
        "icon_class": icon,
        "action_id": action_id,
        "action_params": {},
    }
    if style_class:
        new_button["style_class"] = style_class

    target_page["buttons"].append(new_button)
    print(
        f"Button '{button_text}' added to page '{target_page.get('name')}' in local configuration."
    )
    # Note: stage_and_apply_current_config() is not called here, assuming it's called after all modifications.
    return True


def send_button_content_update(
    button_id: str,
    text: str = None,
    icon_class: str = None,
    style_class: str = None,
    sparkline_payload: dict = None,
):
    """Sends a live content update for a specific button, optionally with sparkline data."""
    payload = {"button_id": button_id}
    has_update = False

    if text is not None:
        payload["text"] = text
        has_update = True
    if icon_class is not None:
        payload["icon_class"] = icon_class
        has_update = True
    if style_class is not None:
        payload["style_class"] = style_class
        has_update = True
    if sparkline_payload is not None:
        payload["sparkline"] = sparkline_payload
        has_update = True

    if not has_update:
        # print(f"No content changes specified for button '{button_id}'. Skipping update.")
        return False

    try:
        response = requests.post(BUTTON_UPDATE_URL, json=payload, timeout=5)
        response.raise_for_status()
        # print(f"Button '{button_id}' content update sent. Response: {response.json().get('message')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to update button '{button_id}' content.")
        if hasattr(e, "response") and e.response is not None:
            print(
                f"Status Code: {e.response.status_code}, Response: {e.response.text[:200]}"
            )
        else:
            print(f"Error details: {e}")
        return False


# --- Demo Specific Data ---
sparkline_data_points = []
MAX_SPARKLINE_POINTS = 30
ICONS_TO_CYCLE = [
    "fas fa-hourglass-start",
    "fas fa-hourglass-half",
    "fas fa-hourglass-end",
    "fas fa-sync fa-spin",
    "fas fa-bolt",
    "fas fa-star",
]
SPARKLINE_BASE_COLOR = (
    "#FFC107"  # Amber/Yellow - good contrast on green "button-success"
)


def generate_next_sparkline_value():
    """Generates a new value for the sparkline, simulating a time series."""
    if not sparkline_data_points:
        return random.uniform(10, 20)

    last_value = sparkline_data_points[-1]
    change = random.uniform(-2.5, 2.7)
    new_value = last_value + change
    return max(0, min(new_value, 30))


def update_sparkline_data_list():
    """Adds a new data point and keeps the list at a max size."""
    global sparkline_data_points
    new_val = generate_next_sparkline_value()
    sparkline_data_points.append(new_val)
    if len(sparkline_data_points) > MAX_SPARKLINE_POINTS:
        sparkline_data_points.pop(0)


def initialize_sparkline_data():
    global sparkline_data_points
    sparkline_data_points = [
        random.uniform(5, 25) for _ in range(MAX_SPARKLINE_POINTS // 2)
    ]


def run_all_demos(
    icon_text_button_id: str, sparkline_button_id: str, duration_seconds: int = 60
):
    print(f"\n--- Starting All Demos (Duration: {duration_seconds}s) ---")

    initialize_sparkline_data()
    icon_idx = 0

    start_time = time.time()
    last_icon_text_update_time = 0
    last_sparkline_update_time = 0

    try:
        while time.time() - start_time < duration_seconds:
            current_loop_time = time.time()

            # --- Icon/Text Demo Update (every 2 seconds) ---
            if current_loop_time - last_icon_text_update_time >= 2:
                time_str = time.strftime("%H:%M:%S")
                random_val = random.randint(100, 999)
                new_text_content = f"Icon: {random_val} @ {time_str}"
                new_icon_class = ICONS_TO_CYCLE[icon_idx % len(ICONS_TO_CYCLE)]

                print(
                    f'Updating ICON/TEXT for \'{icon_text_button_id}\': Text "{new_text_content}", Icon "{new_icon_class}"'
                )
                send_button_content_update(
                    icon_text_button_id,
                    text=new_text_content,
                    icon_class=new_icon_class,
                )

                icon_idx += 1
                last_icon_text_update_time = current_loop_time

            # --- Sparkline Demo Update (every 0.5 seconds) ---
            if current_loop_time - last_sparkline_update_time >= 0.5:
                update_sparkline_data_list()
                sparkline_payload = {
                    "data": list(sparkline_data_points),
                    "color": SPARKLINE_BASE_COLOR,
                    "stroke_width": 2,
                }
                sparkline_text = f"Data Points: {len(sparkline_data_points)}"

                # print(f"Updating SPARKLINE for '{sparkline_button_id}': Color {sparkline_payload['color']}, Points {len(sparkline_payload['data'])}")
                send_button_content_update(
                    sparkline_button_id,
                    text=sparkline_text,
                    sparkline_payload=sparkline_payload,
                )
                last_sparkline_update_time = current_loop_time

            time.sleep(0.1)  # Main loop interval

    except KeyboardInterrupt:
        print("\nLive update demos interrupted by user.")
    finally:
        print("--- All Demos Finished ---")
        send_button_content_update(
            icon_text_button_id, text="Icon Demo Done", icon_class="fas fa-stop-circle"
        )
        send_button_content_update(
            sparkline_button_id, text="Sparkline Done", sparkline_payload={"data": []}
        )  # Clear sparkline


# --- Main Execution ---
if __name__ == "__main__":
    print("Visual Control Board - Dynamic Controller Example")
    print(f"Targeting VCB Server at: {VCB_SERVER_URL}")
    print("----------------------------------------------")

    load_initial_configs_from_examples()

    # 1. Add a new page
    demo_page_id = "dynamic_demo_page"
    if not add_new_page(page_id=demo_page_id, page_name="Live Demos", columns=2):
        # If add_new_page now returns True even if page exists, this check is fine.
        # If it returns False on existing page, then stage_and_apply_current_config() might not be called.
        # The current add_new_page returns True if page exists, but doesn't call apply.
        # We need to call apply after all modifications.
        pass  # Page will be added or already exists.

    # 2. Add buttons to this new page
    # Button for Icon/Text Demo
    icon_text_demo_button_id = "icon_text_live_button"
    add_button_to_page(
        page_id=demo_page_id,
        button_id=icon_text_demo_button_id,
        button_text="Icon/Text Demo",
        action_id="log_current_time_action",
        icon="fas fa-image",
        style_class="button-secondary",
    )

    # Button for Sparkline Demo
    sparkline_demo_button_id = "sparkline_live_button"
    add_button_to_page(
        page_id=demo_page_id,
        button_id=sparkline_demo_button_id,
        button_text="Sparkline Demo",
        action_id="log_current_time_action",  # Can be any valid action
        icon=None,  # Start with no icon, sparkline will be added
        style_class="button-success",
    )

    # Apply the new page and buttons configuration
    if not stage_and_apply_current_config():
        print("Failed to apply new page/buttons configuration. Exiting.")
        sys.exit(1)

    print("Pausing for 3 seconds for UI to update with new page and buttons...")
    time.sleep(3)

    # 3. Run live updates on the new buttons
    run_all_demos(
        icon_text_button_id=icon_text_demo_button_id,
        sparkline_button_id=sparkline_demo_button_id,
        duration_seconds=60,
    )

    print("\n----------------------------------------------")
    print("Dynamic controller script finished.")
