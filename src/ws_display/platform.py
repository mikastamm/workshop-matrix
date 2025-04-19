import os
import platform
from typing import Optional, Callable

from src.logging import Logger
from src.ws_display.Config import Config
from src.ws_display.config_loader import get_config
from src.ws_display.renderer.graphic_interface import GraphicInterface

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
        return platform.machine().startswith('arm') and os.path.exists('/sys/firmware/devicetree/base/model')
    
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
                    'rows': config.panel_height,
                    'cols': config.panel_width,
                    'chain_length': config.panel_count_x,
                    'parallel': config.panel_count_y,
                    'hardware_mapping': 'adafruit-hat',  # Adjust as needed
                    'pwm_bits': 11,
                    'brightness': 100,
                    'scan_mode': config.scan_mode
                }
                
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
