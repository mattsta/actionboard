from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ButtonActionParams(BaseModel):
    """
    Flexible model for action parameters.
    Allows any key-value pairs. For more specific validation,
    consider creating distinct models per action type in the future.
    """
    # Allows any key-value pairs by Pydantic's default extra='allow' if no fields defined,
    # or use RootModel for direct dict if preferred.
    # For now, this empty model with default_factory=dict in ButtonConfig works.
    pass

class ButtonConfig(BaseModel):
    id: str
    text: str
    icon_class: Optional[str] = None  # e.g., FontAwesome class like "fas fa-rocket"
    style_class: Optional[str] = None # Custom CSS class for additional styling
    
    # action_id links to a single action defined in actions_config.yaml.
    # For future "tree of actions" or sequences, this model would need to evolve
    # e.g., action_id: Union[str, List[str], ActionSequenceConfig]
    action_id: str 
    action_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # For future dynamic content updates (e.g., button text/icon changes based on external state).
    # Implementation of polling/push updates for this URL is future work.
    dynamic_content_url: Optional[str] = None 

class PageConfig(BaseModel):
    name: str
    id: str
    layout: str = "grid" # "grid", "flex", etc.
    grid_columns: Optional[int] = Field(default=3, gt=0) # Relevant if layout is "grid"
    buttons: List[ButtonConfig]

class UIConfig(BaseModel):
    pages: List[PageConfig]

class ActionDefinition(BaseModel):
    id: str
    module: str
    function: str

class ActionsConfig(BaseModel):
    actions: List[ActionDefinition]

