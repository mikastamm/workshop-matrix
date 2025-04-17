from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any

class Color:
    def __init__(self, red: int = 0, green: int = 0, blue: int = 0):
        self._red = max(0, min(255, red))
        self._green = max(0, min(255, green))
        self._blue = max(0, min(255, blue))
    
    @property
    def red(self) -> int:
        return self._red
    
    @red.setter
    def red(self, value: int) -> None:
        self._red = max(0, min(255, value))
    
    @property
    def green(self) -> int:
        return self._green
    
    @green.setter
    def green(self, value: int) -> None:
        self._green = max(0, min(255, value))
    
    @property
    def blue(self) -> int:
        return self._blue
    
    @blue.setter
    def blue(self, value: int) -> None:
        self._blue = max(0, min(255, value))

class Font(ABC):
    @abstractmethod
    def LoadFont(self, file: str) -> None:
        """Load a font from a file."""
        pass
    
    @abstractmethod
    def CharacterWidth(self, char: int) -> int:
        """Get the width of a character."""
        pass
    
    @abstractmethod
    def DrawGlyph(self, canvas: Any, x: int, y: int, color: Color, char: int) -> int:
        """Draw a glyph on the canvas."""
        pass
    
    @property
    @abstractmethod
    def height(self) -> int:
        """Get the height of the font."""
        pass
    
    @property
    @abstractmethod
    def baseline(self) -> int:
        """Get the baseline of the font."""
        pass

class Canvas(ABC):
    @abstractmethod
    def Clear(self) -> None:
        """Clear the canvas."""
        pass
    
    @abstractmethod
    def SetPixel(self, x: int, y: int, color: Color) -> None:
        """Set a pixel on the canvas."""
        pass
    
    @property
    @abstractmethod
    def width(self) -> int:
        """Get the width of the canvas."""
        pass
    
    @property
    @abstractmethod
    def height(self) -> int:
        """Get the height of the canvas."""
        pass

class GraphicInterface(ABC):
    def __init__(self, config_brightness_override: float = 1.0):
        self._brightness = 1.0
        self._config_brightness_override = config_brightness_override
    
    @abstractmethod
    def CreateFrameCanvas(self) -> Canvas:
        """Create a new frame canvas."""
        pass
    
    @abstractmethod
    def SwapOnVSync(self, canvas: Canvas) -> Canvas:
        """Swap the canvas on VSync."""
        pass
    
    @abstractmethod
    def DrawText(self, canvas: Canvas, font: Font, x: int, y: int, color: Color, text: str) -> int:
        """Draw text on the canvas."""
        pass
    
    @abstractmethod
    def DrawCircle(self, canvas: Canvas, x: int, y: int, r: int, color: Color) -> None:
        """Draw a circle on the canvas."""
        pass
    
    @abstractmethod
    def DrawLine(self, canvas: Canvas, x1: int, y1: int, x2: int, y2: int, color: Color) -> None:
        """Draw a line on the canvas."""
        pass
    
    @abstractmethod
    def CreateFont(self) -> Font:
        """Create a new font instance."""
        pass
    
    @property
    def width(self) -> int:
        """Get the width of the display."""
        return 0
    
    @property
    def height(self) -> int:
        """Get the height of the display."""
        return 0
    
    def set_brightness(self, brightness: float) -> None:
        """
        Set the brightness of the display.
        
        Args:
            brightness: A value between 0.0 and 1.0.
        """
        self._brightness = max(0.0, min(1.0, brightness))
    
    @property
    def effective_brightness(self) -> float:
        """
        Get the effective brightness (product of brightness and config_brightness_override).
        
        Returns:
            A value between 0.0 and 1.0.
        """
        return self._brightness * self._config_brightness_override
