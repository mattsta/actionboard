import requests
import time
import random
import yaml
from pathlib import Path
import sys

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
current_config = {
    "ui_config": None,
    "actions_config": None
}

# --- Helper Functions ---

def load_initial_configs_from_examples():
    """Loads UI and Actions configurations from the project's example files."""
    print("Loading initial configurations from example files...")
    try:
        if not EXAMPLE_UI_CONFIG_PATH.exists():
            print(f"ERROR: Example UI config not found at {EXAMPLE_UI_CONFIG_PATH}")
            sys.exit(1)
        if not EXAMPLE_ACTIONS_CONFIG_PATH.exists():
            print(f"ERROR: Example Actions config not found at {EXAMPLE_ACTIONS_CONFIG_PATH}")
            sys.exit(1)
            
        with open(EXAMPLE_UI_CONFIG_PATH, 'r') as f:
            current_config["ui_config"] = yaml.safe_load(f)
        with open(EXAMPLE_ACTIONS_CONFIG_PATH, 'r') as f:
            current_config["actions_config"] = yaml.safe_load(f)
        
        if current_config["ui_config"] and current_config["actions_config"]:
            print("Successfully loaded initial example configurations.")
        else:
            print("ERROR: Failed to load or parse one or both example configuration files.")
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
        "actions_config": current_config["actions_config"]
    }
    try:
        print("Staging new configuration...")
        response_stage = requests.post(CONFIG_STAGE_URL, json=payload, timeout=10)
        response_stage.raise_for_status()
        print(f"Configuration staged successfully. Server response: {response_stage.status_code}")

        print("Applying staged configuration...")
        response_apply = requests.post(CONFIG_APPLY_URL, timeout=10)
        response_apply.raise_for_status()
        print(f"Configuration applied successfully. Server response: {response_apply.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to stage or apply configuration.")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}, Response: {e.response.text[:500]}")
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
        return True # Considered success as the page is there

    new_page = {
        "name": page_name,
        "id": page_id,
        "layout": "grid",
        "grid_columns": columns,
        "buttons": []
    }
    ui_conf["pages"].append(new_page)
    print(f"Page '{page_name}' added to local configuration.")
    return stage_and_apply_current_config()

def add_button_to_page(page_id: str, button_id: str, button_text: str, 
                       action_id: str = "log_current_time_action", icon: str = "fas fa-cube"):
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
        print(f"Button with ID '{button_id}' already exists on page '{page_id}'. Skipping addition.")
        return True # Considered success

    new_button = {
        "id": button_id,
        "text": button_text,
        "icon_class": icon,
        "action_id": action_id, # Ensure this action_id exists in actions_config
        "action_params": {} 
    }
    target_page["buttons"].append(new_button)
    print(f"Button '{button_text}' added to page '{target_page.get('name')}' in local configuration.")
    return stage_and_apply_current_config()

def send_button_content_update(button_id: str, text: str = None, icon_class: str = None, style_class: str = None):
    """Sends a live content update for a specific button."""
    payload = {"button_id": button_id}
    if text is not None:
        payload["text"] = text
    if icon_class is not None:
        payload["icon_class"] = icon_class
    if style_class is not None:
        payload["style_class"] = style_class
    
    if len(payload) == 1: # Only button_id was provided
        print(f"No content changes specified for button '{button_id}'. Skipping update.")
        return False

    try:
        response = requests.post(BUTTON_UPDATE_URL, json=payload, timeout=5)
        response.raise_for_status()
        # print(f"Button '{button_id}' content update sent. Response: {response.json().get('message')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to update button '{button_id}' content.")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}, Response: {e.response.text[:200]}")
        else:
            print(f"Error details: {e}")
        return False

def run_live_update_demo(button_id: str, duration_seconds: int = 30):
    """Runs a demo of live text and icon updates for a button."""
    print(f"\n--- Starting Live Update Demo for Button ID: '{button_id}' (Duration: {duration_seconds}s) ---")
    
    icons_to_cycle = ["fas fa-hourglass-start", "fas fa-hourglass-half", "fas fa-hourglass-end", "fas fa-sync fa-spin", "fas fa-bolt"]
    icon_index = 0
    
    start_time = time.time()
    last_text_update_time = 0
    last_icon_update_time = 0

    try:
        while time.time() - start_time < duration_seconds:
            current_time = time.time()

            # Update text every 1 second
            if current_time - last_text_update_time >= 1:
                time_str = time.strftime("%H:%M:%S")
                random_val = random.randint(100, 999)
                new_text_content = f"Live: {random_val} @ {time_str}"
                print(f"Updating text for '{button_id}': \"{new_text_content}\"")
                send_button_content_update(button_id, text=new_text_content)
                last_text_update_time = current_time

            # Update icon every 3 seconds
            if current_time - last_icon_update_time >= 3:
                new_icon_class = icons_to_cycle[icon_index % len(icons_to_cycle)]
                print(f"Updating icon for '{button_id}': \"{new_icon_class}\"")
                send_button_content_update(button_id, icon_class=new_icon_class)
                icon_index += 1
                last_icon_update_time = current_time
            
            time.sleep(0.2) # Loop interval

    except KeyboardInterrupt:
        print("\nLive update demo interrupted by user.")
    finally:
        print("--- Live Update Demo Finished ---")
        # Reset button to a final state
        send_button_content_update(button_id, text="Demo Complete", icon_class="fas fa-check-circle", style_class="")


# --- Main Execution ---
if __name__ == "__main__":
    print("Visual Control Board - Dynamic Controller Example")
    print(f"Targeting VCB Server at: {VCB_SERVER_URL}")
    print("----------------------------------------------")

    load_initial_configs_from_examples()

    # 1. Add a new page
    demo_page_id = "dynamic_demo_page"
    if add_new_page(page_id=demo_page_id, page_name="Dynamic Demo Page", columns=1):
        print("Pausing for 2 seconds for UI to update...")
        time.sleep(2)

        # 2. Add a button to this new page
        demo_button_id = "live_update_button"
        if add_button_to_page(page_id=demo_page_id, 
                              button_id=demo_button_id, 
                              button_text="Live Demo Button",
                              action_id="log_current_time_action", # Assumes this action exists
                              icon="fas fa-rocket"):
            print("Pausing for 2 seconds for UI to update...")
            time.sleep(2)

            # 3. Run live updates on the new button
            run_live_update_demo(button_id=demo_button_id, duration_seconds=20)
        else:
            print(f"Could not add button '{demo_button_id}', skipping live update demo.")
    else:
        print(f"Could not add page '{demo_page_id}', skipping further demonstrations.")

    print("\n----------------------------------------------")
    print("Dynamic controller script finished.")
