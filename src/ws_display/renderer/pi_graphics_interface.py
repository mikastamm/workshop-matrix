from typing import Any, Optional, cast, List, Tuple, Literal
import os
from PIL import Image

from src.logging import Logger
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Font, Color, MatrixImage, BlendMode

class PiCanvas(Canvas):
    def __init__(self, rgbmatrix_canvas: Any):
        self._canvas = rgbmatrix_canvas
        # Create a pixel cache to track pixel values (needed for GetPixel)
        self._pixel_cache = {}
    
    def Clear(self) -> None:
        self._canvas.Clear()
        self._pixel_cache.clear()
    
    def SetPixel(self, x: int, y: int, color: Color) -> None:
        self._canvas.SetPixel(x, y, color.red, color.green, color.blue)
        # Update pixel cache
        self._pixel_cache[(x, y)] = (color.red, color.green, color.blue)
    
    def GetPixel(self, x: int, y: int) -> Color:
        # Check if pixel is in cache
        if (x, y) in self._pixel_cache:
            r, g, b = self._pixel_cache[(x, y)]
            return Color(r, g, b)
        # If not in cache, return black
        return Color(0, 0, 0)
    
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
    
    def LoadImage(self, image_name: str) -> MatrixImage:
        """
        Load an image from the project's images directory.
        
        Args:
            image_name: Name of the image file without extension
            
        Returns:
            A MatrixImage object containing the image data
        """
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        # Check for png first, then bmp
        img_path = os.path.join(project_root, "images", f"{image_name}.png")
        if not os.path.exists(img_path):
            img_path = os.path.join(project_root, "images", f"{image_name}.bmp")
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Image {image_name} not found in project images directory")
        
        # Load the image using PIL
        img = Image.open(img_path)
        
        # Create MatrixImage
        matrix_img = MatrixImage(img.width, img.height, img_path)
        matrix_img.load_pixel_data(img)
        
        return matrix_img
    
    def RenderImage(self, canvas: Canvas, image: MatrixImage, x: int, y: int, 
                   origin: Literal["center-center", "left-mid", "left-top", "left-bot", 
                                  "right-mid", "right-top", "right-bot"] = "center-center",
                   tint: Optional[Color] = None,
                   blend_mode: BlendMode = BlendMode.NORMAL) -> None:
        """
        Render an image on the canvas with optional blend modes.
        
        Args:
            canvas: Canvas to render on
            image: MatrixImage to render
            x: X coordinate
            y: Y coordinate
            origin: Origin point of the image relative to coordinates
            tint: Optional color to tint the image with
            blend_mode: Blend mode to use when compositing image onto canvas
        """
        if not isinstance(canvas, PiCanvas):
            raise TypeError("Canvas must be a PiCanvas")
            
        # Calculate offsets based on origin
        offset_x, offset_y = 0, 0
        
        if origin == "center-center":
            offset_x = -image.width // 2
            offset_y = -image.height // 2
        elif origin == "left-mid":
            offset_x = 0
            offset_y = -image.height // 2
        elif origin == "left-top":
            offset_x = 0
            offset_y = 0
        elif origin == "left-bot":
            offset_x = 0
            offset_y = -image.height
        elif origin == "right-mid":
            offset_x = -image.width
            offset_y = -image.height // 2
        elif origin == "right-top":
            offset_x = -image.width
            offset_y = 0
        elif origin == "right-bot":
            offset_x = -image.width
            offset_y = -image.height
        
        # Render image pixel by pixel
        for img_y in range(image.height):
            for img_x in range(image.width):
                # Calculate canvas coordinates
                canvas_x = x + img_x + offset_x
                canvas_y = y + img_y + offset_y
                
                # Check if the pixel is within canvas bounds
                if (0 <= canvas_x < canvas.width and 
                    0 <= canvas_y < canvas.height and 
                    img_y < len(image.pixel_data) and 
                    img_x < len(image.pixel_data[img_y])):
                    
                    # Get pixel color
                    r, g, b = image.pixel_data[img_y][img_x]
                    
                    # Apply tint if provided
                    if tint:
                        r = (r * tint.red) // 255
                        g = (g * tint.green) // 255
                        b = (b * tint.blue) // 255
                    
                    # Skip fully black (transparent) pixels
                    if r == 0 and g == 0 and b == 0:
                        continue
                    
                    # Apply blend mode
                    if blend_mode == BlendMode.NORMAL:
                        # Just set the pixel with image color
                        canvas.SetPixel(canvas_x, canvas_y, Color(r, g, b))
                    else:
                        # Get the canvas pixel's current color
                        canvas_color = canvas.GetPixel(canvas_x, canvas_y)
                        
                        # Perform blending based on selected mode
                        if blend_mode == BlendMode.MULTIPLY:
                            # Multiply: multiply each channel
                            blended_r = (r * canvas_color.red) // 255
                            blended_g = (g * canvas_color.green) // 255
                            blended_b = (b * canvas_color.blue) // 255
                            
                        elif blend_mode == BlendMode.INVERT_MULTIPLY:
                            # Invert Multiply: invert image, then multiply
                            inv_r = 255 - r
                            inv_g = 255 - g
                            inv_b = 255 - b
                            blended_r = (inv_r * canvas_color.red) // 255
                            blended_g = (inv_g * canvas_color.green) // 255
                            blended_b = (inv_b * canvas_color.blue) // 255
                            
                        elif blend_mode == BlendMode.SUBTRACT:
                            # Subtract: canvas - image (clamped to 0)
                            blended_r = max(0, canvas_color.red - r)
                            blended_g = max(0, canvas_color.green - g)
                            blended_b = max(0, canvas_color.blue - b)
                            
                        elif blend_mode == BlendMode.LIGHTER_COLOR:
                            # Lighter Color: take the color with higher brightness
                            img_brightness = r + g + b
                            canvas_brightness = canvas_color.red + canvas_color.green + canvas_color.blue
                            
                            if img_brightness > canvas_brightness:
                                blended_r, blended_g, blended_b = r, g, b
                            else:
                                blended_r = canvas_color.red
                                blended_g = canvas_color.green
                                blended_b = canvas_color.blue
                        
                        # Set the blended pixel on canvas if not fully black
                        if blended_r > 0 or blended_g > 0 or blended_b > 0:
                            canvas.SetPixel(canvas_x, canvas_y, Color(blended_r, blended_g, blended_b))
