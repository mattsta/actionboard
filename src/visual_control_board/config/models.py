from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ButtonActionParams(BaseModel):
    """
    Flexible model for action parameters.
    This model uses Pydantic's capability to allow arbitrary key-value pairs
    (extra='allow' is the default behavior when no specific fields are defined,
    or when inheriting from BaseModel directly).
    This provides flexibility for actions to define their own expected parameters
    without needing a new Pydantic model for each action's parameter set.

    For actions requiring specific, validated parameters, you could in the future:
    1. Define specific Pydantic models for those parameters.
    2. Implement a discriminated union or a more complex validation scheme within
       the action execution logic if type-safe parameter parsing per action is desired.
    
    Currently, parameters are passed as a dictionary to the action function,
    and it's up to the action function to handle them.
    """
    # Pydantic's default behavior for extra fields is 'allow',
    # so any key-value pairs provided in `action_params` will be captured.
    # No specific fields are defined here to maintain maximum flexibility.
    # Example: {"url": "http://example.com", "retries": 3}
    class Config:
        extra = "allow"


class ButtonConfig(BaseModel):
    id: str = Field(..., description="Unique identifier for the button.")
    text: str = Field(..., description="Text displayed on the button.")
    icon_class: Optional[str] = Field(default=None, description="CSS class for an icon (e.g., FontAwesome 'fas fa-rocket').")
    style_class: Optional[str] = Field(default=None, description="Custom CSS class for additional button styling.")
    
    action_id: str = Field(..., description="Identifier of the action to be executed, defined in actions_config.yaml.")
    action_params: ButtonActionParams = Field(default_factory=ButtonActionParams, description="Parameters to pass to the action function.")
    
    # For future dynamic content updates (e.g., button text/icon changes based on external state).
    # Implementation of polling/push updates for this URL is future work.
    dynamic_content_url: Optional[str] = Field(default=None, description="URL for dynamically fetching button content (future feature).")

class PageConfig(BaseModel):
    name: str = Field(..., description="Display name of the page.")
    id: str = Field(..., description="Unique identifier for the page.")
    layout: str = Field(default="grid", description="Layout type for the page (e.g., 'grid', 'flex').")
    grid_columns: Optional[int] = Field(default=3, gt=0, description="Number of columns if layout is 'grid'.")
    buttons: List[ButtonConfig] = Field(..., description="List of buttons on this page.")

class UIConfig(BaseModel):
    pages: List[PageConfig] = Field(..., description="List of pages in the UI.")

class ActionDefinition(BaseModel):
    id: str = Field(..., description="Unique identifier for the action.")
    module: str = Field(..., description="Python module path where the action function is defined.")
    function: str = Field(..., description="Name of the action function within the module.")

class ActionsConfig(BaseModel):
    actions: List[ActionDefinition] = Field(..., description="List of action definitions.")

