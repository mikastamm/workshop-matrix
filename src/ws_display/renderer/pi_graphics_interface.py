from typing import Any, Optional, cast

from src.logging import Logger
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Font, Color

class PiCanvas(Canvas):
    def __init__(self, rgbmatrix_canvas: Any):
        self._canvas = rgbmatrix_canvas
    
    def Clear(self) -> None:
        self._canvas.Clear()
    
    def SetPixel(self, x: int, y: int, color: Color) -> None:
        self._canvas.SetPixel(x, y, color.red, color.green, color.blue)
    
    @property
    def width(self) -> int:
        return self._canvas.width
    
    @property
    def height(self) -> int:
        return self._canvas.height
    
    def _get_canvas(self) -> Any:
        """Get the underlying rgbmatrix canvas."""
        return self._canvas

class PiFont(Font):
    def __init__(self):
        # Import here to avoid errors when not on a Pi
        from rgbmatrix import graphics
        self._font = graphics.Font()
        self._loaded = False
    
    def LoadFont(self, file: str) -> None:
        if not self._font.LoadFont(file):
            raise Exception(f"Couldn't load font {file}")
        self._loaded = True
    
    def CharacterWidth(self, char: int) -> int:
        if not self._loaded:
            raise Exception("Font not loaded")
        return self._font.CharacterWidth(char)
    
    def DrawGlyph(self, canvas: Any, x: int, y: int, color: Color, char: int) -> int:
        if not self._loaded:
            raise Exception("Font not loaded")
        
        # Import here to avoid errors when not on a Pi
        from rgbmatrix import graphics
        
        # Convert our Color to rgbmatrix Color
        rgb_color = graphics.Color(color.red, color.green, color.blue)
        
        # Get the underlying rgbmatrix canvas
        if isinstance(canvas, PiCanvas):
            rgb_canvas = canvas._get_canvas()
        else:
            raise TypeError("Canvas must be a PiCanvas")
        
        return self._font.DrawGlyph(rgb_canvas, x, y, rgb_color, char)
    
    @property
    def height(self) -> int:
        if not self._loaded:
            raise Exception("Font not loaded")
        return self._font.height()
    
    @property
    def baseline(self) -> int:
        if not self._loaded:
            raise Exception("Font not loaded")
        return self._font.baseline()

class PiGraphicInterface(GraphicInterface):
    def __init__(self, config_brightness_override: float = 1.0, **matrix_options):
        super().__init__(config_brightness_override)
        
        # Import here to avoid errors when not on a Pi
        from rgbmatrix import RGBMatrix, RGBMatrixOptions
        
        # Configure matrix options
        options = RGBMatrixOptions()
        
        # Set options from kwargs
        for key, value in matrix_options.items():
            if hasattr(options, key):
                setattr(options, key, value)
        
        # Create the matrix
        self._matrix = RGBMatrix(options=options)
        
        # Import graphics module
        from rgbmatrix import graphics
        self._graphics = graphics
        
        # Set initial brightness
        self._update_brightness()
        
        Logger.get_logger().info(f"Initialized PiGraphicInterface with dimensions {self.width}x{self.height}")
    
    def CreateFrameCanvas(self) -> Canvas:
        return PiCanvas(self._matrix.CreateFrameCanvas())
    
    def SwapOnVSync(self, canvas: Canvas) -> Canvas:
        if not isinstance(canvas, PiCanvas):
            raise TypeError("Canvas must be a PiCanvas")
        
        return PiCanvas(self._matrix.SwapOnVSync(canvas._get_canvas()))
    
    def DrawText(self, canvas: Canvas, font: Font, x: int, y: int, color: Color, text: str) -> int:
        if not isinstance(canvas, PiCanvas):
            raise TypeError("Canvas must be a PiCanvas")
        
        if not isinstance(font, PiFont):
            raise TypeError("Font must be a PiFont")
        
        # Convert our Color to rgbmatrix Color
        rgb_color = self._graphics.Color(color.red, color.green, color.blue)
        
        # Draw the text
        return self._graphics.DrawText(canvas._get_canvas(), font._font, x, y, rgb_color, text)
    
    def DrawCircle(self, canvas: Canvas, x: int, y: int, r: int, color: Color) -> None:
        if not isinstance(canvas, PiCanvas):
            raise TypeError("Canvas must be a PiCanvas")
        
        # Convert our Color to rgbmatrix Color
        rgb_color = self._graphics.Color(color.red, color.green, color.blue)
        
        # Draw the circle
        self._graphics.DrawCircle(canvas._get_canvas(), x, y, r, rgb_color)
    
    def DrawLine(self, canvas: Canvas, x1: int, y1: int, x2: int, y2: int, color: Color) -> None:
        if not isinstance(canvas, PiCanvas):
            raise TypeError("Canvas must be a PiCanvas")
        
        # Convert our Color to rgbmatrix Color
        rgb_color = self._graphics.Color(color.red, color.green, color.blue)
        
        # Draw the line
        self._graphics.DrawLine(canvas._get_canvas(), x1, y1, x2, y2, rgb_color)
    
    def CreateFont(self) -> Font:
        return PiFont()
    
    @property
    def width(self) -> int:
        return self._matrix.width
    
    @property
    def height(self) -> int:
        return self._matrix.height
    
    def set_brightness(self, brightness: float) -> None:
        super().set_brightness(brightness)
        self._update_brightness()
    
    def _update_brightness(self) -> None:
        """Update the matrix brightness based on the effective brightness."""
        # rgbmatrix brightness is 0-100
        brightness_percent = int(self.effective_brightness * 100)
        self._matrix.brightness = brightness_percent
