from typing import Optional

from src.logging import Logger
from src.ws_display.input.user_input import UserInput

# GPIO pin definitions for the rotary encoder
CLK_GPIO = 17  # GPIO pin for the CLK signal
DT_GPIO = 18   # GPIO pin for the DT signal
SW_GPIO = 27   # GPIO pin for the switch signal

class PiUserInput(UserInput):
    """
    Raspberry Pi implementation of UserInput using the pigpio_encoder library.
    Uses a rotary encoder with a push button for input.
    """
    
    def __init__(self):
        """
        Initialize the PiUserInput.
        """
        super().__init__()
        self.logger = Logger.get_logger()
        self._initialized = False
        self._rotary = None
    
    def initialize(self) -> None:
        """
        Initialize the input handling by setting up the rotary encoder.
        """
        if self._initialized:
            return
        
        try:
            # Import here to avoid errors when not on a Pi
            from pigpio_encoder.rotary import Rotary
            
            # Create the rotary encoder object
            self._rotary = Rotary(
                clk_gpio=CLK_GPIO,
                dt_gpio=DT_GPIO,
                sw_gpio=SW_GPIO
            )
            
            # Set up the rotary encoder for up/down events
            self._rotary.setup_rotary(
                min=0,
                max=100,
                scale=1,
                debounce=300,  # 300ms debounce
                up_callback=self._handle_up_event,
                down_callback=self._handle_down_event
            )
            
            # Set up the switch for click events
            self._rotary.setup_switch(
                debounce=300,  # 300ms debounce
                long_press=False,  # We don't need long press for now
                sw_short_callback=self._handle_click_event
            )
            
            self._initialized = True
            self.logger.info("Initialized Pi user input")
        except ImportError as e:
            self.logger.error(f"Failed to import pigpio_encoder: {e}")
            self.logger.warning("Pi user input not available")
        except Exception as e:
            self.logger.error(f"Failed to initialize Pi user input: {e}")
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the input handling.
        """
        if not self._initialized or self._rotary is None:
            return
        
        # No explicit cleanup needed for pigpio_encoder
        # The library handles cleanup internally
        
        self._initialized = False
        self._rotary = None
        self.logger.info("Cleaned up Pi user input")
