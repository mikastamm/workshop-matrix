from abc import ABC, abstractmethod
from typing import Callable, Optional, Any

class LedMatrixUI(ABC):
    """
    Abstract base class for LED Matrix UI implementations.
    Provides a common interface for UI functionality across different platforms.
    """
    
    @abstractmethod
    def initialize(self, root_window: Optional[Any] = None) -> None:
        """
        Initialize the UI.
        
        Args:
            root_window: Optional root window (platform-specific)
        """
        pass
    
    @abstractmethod
    def create_control_panel(self, parent: Any) -> Any:
        """
        Create a control panel with UI elements.
        
        Args:
            parent: Parent widget (platform-specific)
            
        Returns:
            The created control panel widget (platform-specific)
        """
        pass
    
    @abstractmethod
    def add_button(self, parent: Any, text: str, command: Callable) -> None:
        """
        Add a button to the UI.
        
        Args:
            parent: Parent widget (platform-specific)
            text: Button text
            command: Function to call when the button is clicked
        """
        pass
    
    @abstractmethod
    def add_timescale_slider(self, parent: Any, 
                            on_change: Callable[[float], None], 
                            initial_value: float = 1.0) -> None:
        """
        Add a timescale slider to the UI.
        
        Args:
            parent: Parent widget (platform-specific)
            on_change: Function to call when the slider value changes
            initial_value: Initial slider value
        """
        pass
    
    @abstractmethod
    def update(self) -> None:
        """
        Update the UI. This method should be called periodically to process UI events.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up resources used by the UI.
        """
        pass
    
    @abstractmethod
    def run_ui(self, app: Any) -> None:
        """
        Run the UI with the given application.
        This method should handle platform-specific UI initialization and setup.
        
        Args:
            app: The application instance to run with the UI
        """
        pass
