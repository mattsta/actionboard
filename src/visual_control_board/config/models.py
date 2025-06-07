from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field


class ButtonActionParams(BaseModel):
    """
    Flexible model for action parameters.
    This model uses Pydantic's capability to allow arbitrary key-value pairs.
    This provides flexibility for actions to define their own expected parameters
    without needing a new Pydantic model for each action's parameter set.

    When an action is triggered, these parameters are passed as a dictionary
    to the corresponding action function. It is the responsibility of the
    action function to handle and validate these parameters as needed.

    For actions requiring specific, validated parameters, future enhancements could involve:
    1. Defining specific Pydantic models for those parameters and using them within
       the action function for validation.
    2. Implementing a discriminated union approach if a more complex, centralized
       validation scheme per action type is desired before dispatch.

    Example:
        If `action_params` in `ui_config.yaml` is:
        ```yaml
        action_params:
          url: "http://example.com"
          retries: 3
        ```
        The action function will receive `{"url": "http://example.com", "retries": 3}`.
    """

    class Config:
        extra = "allow"  # Allows any additional fields not explicitly defined.


class ButtonConfig(BaseModel):
    """Configuration for a single button in the UI."""

    id: str = Field(
        ..., description="Unique identifier for the button. Used for targeting actions."
    )
    text: str = Field(..., description="Text displayed on the button.")
    icon_class: Optional[str] = Field(
        default=None,
        description="CSS class for an icon (e.g., FontAwesome 'fas fa-rocket').",
    )
    style_class: Optional[str] = Field(
        default=None,
        description="Custom CSS class for additional button styling (e.g., 'button-primary', 'button-danger').",
    )

    action_id: str = Field(
        ...,
        description="Identifier of the action to be executed, as defined in actions_config.yaml.",
    )
    action_params: ButtonActionParams = Field(
        default_factory=ButtonActionParams,
        description="Parameters to pass to the action function. Structure depends on the action.",
    )

    dynamic_content_url: Optional[str] = Field(
        default=None,
        description="URL for dynamically fetching button content (e.g., text, icon). Deprecated in favor of WebSocket updates.",
    )


class PageConfig(BaseModel):
    """Configuration for a single page or view in the UI."""

    name: str = Field(
        ..., description="Display name of the page, often used as a title."
    )
    id: str = Field(..., description="Unique identifier for the page.")
    layout: str = Field(
        default="grid",
        description="Layout type for arranging buttons on the page (e.g., 'grid').",
    )
    grid_columns: Optional[int] = Field(
        default=3,
        gt=0,
        description="Number of columns if layout is 'grid'. Must be greater than 0.",
    )
    buttons: List[ButtonConfig] = Field(
        ..., description="List of buttons to display on this page."
    )


class UIConfig(BaseModel):
    """Root configuration model for the entire UI structure."""

    pages: List[PageConfig] = Field(
        ...,
        description="List of pages in the UI. The application now supports navigation between these pages.",
    )

    def find_button_and_page(
        self, button_id: str
    ) -> Optional[Tuple[PageConfig, ButtonConfig]]:
        """
        Finds a button by its ID across all pages and returns it along with its parent page.

        Args:
            button_id: The ID of the button to find.

        Returns:
            A tuple containing the PageConfig and ButtonConfig if found, otherwise None.
        """
        if not self.pages:
            return None
        for page in self.pages:
            if page.buttons:
                for button in page.buttons:
                    if button.id == button_id:
                        return page, button
        return None

    def find_page(self, page_id: str) -> Optional[PageConfig]:
        """
        Finds a page by its ID.

        Args:
            page_id: The ID of the page to find.

        Returns:
            The PageConfig if found, otherwise None.
        """
        if not self.pages:
            return None
        for page in self.pages:
            if page.id == page_id:
                return page
        return None


class ActionDefinition(BaseModel):
    """Defines a single action that can be triggered by a button."""

    id: str = Field(
        ...,
        description="Unique identifier for the action. Referenced by ButtonConfig.action_id.",
    )
    module: str = Field(
        ...,
        description="Python module path where the action function is defined (e.g., 'my_package.my_module').",
    )
    function: str = Field(
        ..., description="Name of the action function within the specified module."
    )


class ActionsConfig(BaseModel):
    """Root configuration model for all available actions."""

    actions: List[ActionDefinition] = Field(
        ..., description="List of all action definitions available to the application."
    )


class DynamicUpdateConfig(BaseModel):
    """
    Model for receiving a full UI and Actions configuration update via API.
    This allows external services to propose a new set of configurations.
    """

    ui_config: UIConfig = Field(..., description="The complete new UI configuration.")
    actions_config: ActionsConfig = Field(
        ..., description="The complete new Actions configuration."
    )


class ButtonContentUpdate(BaseModel):
    """
    Model for pushing live updates to a button's content via WebSocket.
    All fields are optional; only provided fields will be updated.
    """

    button_id: str = Field(..., description="The ID of the button to update.")
    text: Optional[str] = Field(default=None, description="New text for the button.")
    icon_class: Optional[str] = Field(
        default=None,
        description="New FontAwesome icon class. Send an empty string ('') to remove/hide the current icon.",
    )
    style_class: Optional[str] = Field(
        default=None,
        description="New custom CSS class for styling. Send an empty string ('') to remove the current custom style and revert to default button styling.",
    )
