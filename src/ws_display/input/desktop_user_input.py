import keyboard
from typing import Callable, Dict, Any

from src.logging import Logger
from src.ws_display.input.user_input import UserInput

class DesktopUserInput(UserInput):
    """
    Desktop implementation of UserInput using the keyboard library.
    Maps keyboard keys to input events.
    """
    
    def __init__(self):
        """
        Initialize the DesktopUserInput.
        """
        super().__init__()
        self.logger = Logger.get_logger()
        self._initialized = False
        self._key_handlers: Dict[str, Callable[[], None]] = {}
    
    def initialize(self) -> None:
        """
        Initialize the input handling by registering keyboard event handlers.
        """
        if self._initialized:
            return
        
        # Define key mappings
        self._key_handlers = {
            'up': self._handle_up_event,
            'down': self._handle_down_event,
            'enter': self._handle_click_event
        }
        
        # Register keyboard event handlers
        for key, handler in self._key_handlers.items():
            keyboard.on_press_key(key, lambda e, handler=handler: handler())
        
        self._initialized = True
        self.logger.info("Initialized desktop user input")
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the input handling.
        """
        if not self._initialized:
            return
        
        # Unregister keyboard event handlers
        for key in self._key_handlers.keys():
            keyboard.unhook_key(key)
        
        self._initialized = False
        self.logger.info("Cleaned up desktop user input")
