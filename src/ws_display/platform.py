import os
import platform
from typing import Optional, Callable

from src.logging import Logger
from src.ws_display.Config import Config
from src.ws_display.config_loader import get_config
from src.ws_display.renderer.graphic_interface import GraphicInterface
from src.ws_display.input.user_input import UserInput

class Platform:
    """
    Class responsible for platform-specific functionality.
    Determines whether we're running on a Raspberry Pi or desktop
    and provides appropriate implementations.
    """
    def __init__(self, config_loader: Callable[[], Config]):
        """
        Initialize the Platform class.
        
        Args:
            config_loader: Function that returns the configuration
        """
        self.logger = Logger.get_logger()
        self.config_loader = config_loader
        self._is_raspberry_pi = self._detect_raspberry_pi()
        
    def _detect_raspberry_pi(self) -> bool:
        """
        Detect if we're running on a Raspberry Pi.
        
        Returns:
            True if running on a Raspberry Pi, False otherwise
        """
        return platform.machine().startswith('arm') or platform.machine().startswith('aarch64')
    
    @property
    def is_raspberry_pi(self) -> bool:
        """
        Check if we're running on a Raspberry Pi.
        
        Returns:
            True if running on a Raspberry Pi, False otherwise
        """
        return self._is_raspberry_pi
    
    def get_graphics_library(self) -> GraphicInterface:
        """
        Get the appropriate GraphicInterface based on the platform.
        
        Returns:
            GraphicInterface implementation for the current platform
        """
        config = self.config_loader()
        
        if self.is_raspberry_pi:
            self.logger.info("Detected Raspberry Pi platform, using PiGraphicInterface")
            try:
                # Import here to avoid errors when not on a Pi
                from src.ws_display.renderer.pi_graphics_interface import PiGraphicInterface
                
                # Create matrix options
                matrix_options = {
                    'rows': 40,
                    'cols': 80,
                    'chain_length': 4,
                    'parallel': 1,
                    'hardware_mapping': 'adafruit-hat',
                    'pwm_bits': 11,
                    'gpio_slowdown': 2,
                    'scan_mode': 0,
                    'brightness': 100,
                    'pwm_lsb_nanoseconds': 130,
                    'led_rgb_sequence': 'RGB',
                    'show_refresh_rate': True,
                }

                
                print(config.scan_mode)
                print(config)
                return PiGraphicInterface(
                    config_brightness_override=config.brightness_override,
                    **matrix_options
                )
            except ImportError as e:
                self.logger.error(f"Failed to import PiGraphicInterface: {e}")
                self.logger.warning("Falling back to EmulatedGraphicInterface")
                self._is_raspberry_pi = False
        
        # If not on a Raspberry Pi or if Pi interface failed to load
        self.logger.info("Using EmulatedGraphicInterface")
        from src.ws_display.renderer.emulated_graphics_interface import EmulatedGraphicInterface
        
        # Calculate total dimensions
        width = config.panel_width * config.panel_count_x
        height = config.panel_height * config.panel_count_y
        
        return EmulatedGraphicInterface(
            width=width,
            height=height,
            config_brightness_override=config.brightness_override,
            scale=6,  # Adjust scale as needed
            pixel_spacing=0.4,  # Spacing between pixels (0.0 - 1.0)
            use_circles=True  # Whether to render pixels as circles
        )
    
    def get_ui(self):
        """
        Get the appropriate UI implementation based on the platform.
        
        Returns:
            LedMatrixUI implementation for the current platform
        """
        if self.is_raspberry_pi:
            from src.ws_display.ui.pi_led_matrix_ui import PiLedMatrixUI
            return PiLedMatrixUI()
        else:
            from src.ws_display.ui.led_matrix_emulator_ui import LedMatrixEmulatorUI
            return LedMatrixEmulatorUI()
    
    def get_user_input(self) -> UserInput:
        """
        Get the appropriate UserInput implementation based on the platform.
        
        Returns:
            UserInput implementation for the current platform
        """
        if self.is_raspberry_pi:
            self.logger.info("Using Pi user input")
            from src.ws_display.input.pi_user_input import PiUserInput
            return PiUserInput()
        else:
            self.logger.info("Using desktop user input")
            from src.ws_display.input.desktop_user_input import DesktopUserInput
            return DesktopUserInput()
