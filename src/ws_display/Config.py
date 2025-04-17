from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    # Panel configuration
    panel_width: Optional[int] = None
    panel_height: Optional[int] = None
    panel_count_x: Optional[int] = None
    panel_count_y: Optional[int] = None
    scan_mode: Optional[int] = None
    
    # Display configuration
    brightness_override: Optional[float] = None
    
    # Other configuration options can be added here
    
    def SetDefaults(self) -> None:
        """
        Set default values for any configuration parameters that are None.
        """
        if self.panel_width is None:
            self.panel_width = 64
        
        if self.panel_height is None:
            self.panel_height = 32
        
        if self.panel_count_x is None:
            self.panel_count_x = 2
        
        if self.panel_count_y is None:
            self.panel_count_y = 2
        
        if self.scan_mode is None:
            self.scan_mode = 8  # 1/8 scan mode
        
        if self.brightness_override is None:
            self.brightness_override = 1.0  # Full brightness
    
    @property
    def total_width(self) -> int:
        """
        Get the total width of the display in pixels.
        """
        return self.panel_width * self.panel_count_x if self.panel_width and self.panel_count_x else 0
    
    @property
    def total_height(self) -> int:
        """
        Get the total height of the display in pixels.
        """
        return self.panel_height * self.panel_count_y if self.panel_height and self.panel_count_y else 0
