from abc import ABC, abstractmethod
import tkinter as tk
from typing import Callable, Optional

class LedMatrixUI(ABC):
    """
    Abstract base class for LED Matrix UI implementations.
    Provides a common interface for UI functionality across different platforms.
    """
    
    @abstractmethod
    def initialize(self, root: Optional[tk.Tk] = None) -> None:
        """
        Initialize the UI.
        
        Args:
            root: Optional Tkinter root window
        """
        pass
    
    @abstractmethod
    def create_control_panel(self, parent: tk.Widget) -> tk.Widget:
        """
        Create a control panel with UI elements.
        
        Args:
            parent: Parent widget
            
        Returns:
            The created control panel widget
        """
        pass
    
    @abstractmethod
    def add_button(self, parent: tk.Widget, text: str, command: Callable) -> None:
        """
        Add a button to the UI.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Function to call when the button is clicked
        """
        pass
    
    @abstractmethod
    def add_timescale_slider(self, parent: tk.Widget, 
                            on_change: Callable[[float], None], 
                            initial_value: float = 1.0) -> None:
        """
        Add a timescale slider to the UI.
        
        Args:
            parent: Parent widget
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
