from abc import ABC, abstractmethod
from typing import Callable, List

class UserInput(ABC):
    """
    Abstract base class for user input handling.
    Provides a common interface for handling user input across different platforms.
    """
    
    def __init__(self):
        """
        Initialize the UserInput.
        """
        # Lists to store callback functions
        self._up_listeners: List[Callable[[], bool]] = []
        self._down_listeners: List[Callable[[], bool]] = []
        self._click_listeners: List[Callable[[], bool]] = []
    
    def registerUpListener(self, callback: Callable[[], bool]) -> None:
        """
        Register a callback function for scroll up events.
        The callback should return a boolean indicating whether other listeners should be called.
        
        Args:
            callback: Function to call when a scroll up event occurs
        """
        self._up_listeners.append(callback)
    
    def registerDownListener(self, callback: Callable[[], bool]) -> None:
        """
        Register a callback function for scroll down events.
        The callback should return a boolean indicating whether other listeners should be called.
        
        Args:
            callback: Function to call when a scroll down event occurs
        """
        self._down_listeners.append(callback)
    
    def registerClickListener(self, callback: Callable[[], bool]) -> None:
        """
        Register a callback function for click events.
        The callback should return a boolean indicating whether other listeners should be called.
        
        Args:
            callback: Function to call when a click event occurs
        """
        self._click_listeners.append(callback)
    
    def _handle_up_event(self) -> None:
        """
        Handle a scroll up event by calling all registered listeners in reverse order.
        If a listener returns False, subsequent listeners will not be called.
        """
        # Call listeners in reverse order (last registered is called first)
        for listener in reversed(self._up_listeners):
            # If the listener returns False, stop calling other listeners
            if not listener():
                break
    
    def _handle_down_event(self) -> None:
        """
        Handle a scroll down event by calling all registered listeners in reverse order.
        If a listener returns False, subsequent listeners will not be called.
        """
        # Call listeners in reverse order (last registered is called first)
        for listener in reversed(self._down_listeners):
            # If the listener returns False, stop calling other listeners
            if not listener():
                break
    
    def _handle_click_event(self) -> None:
        """
        Handle a click event by calling all registered listeners in reverse order.
        If a listener returns False, subsequent listeners will not be called.
        """
        # Call listeners in reverse order (last registered is called first)
        for listener in reversed(self._click_listeners):
            # If the listener returns False, stop calling other listeners
            if not listener():
                break
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the input handling.
        This method should be implemented by platform-specific subclasses.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up resources used by the input handling.
        This method should be implemented by platform-specific subclasses.
        """
        pass
