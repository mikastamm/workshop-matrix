from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any, List, Literal
import os
from PIL import Image

class BlendMode(Enum):
    """
    Enum for different blend modes when rendering images.
    """
    NORMAL = 0
    MULTIPLY = 1
    INVERT_MULTIPLY = 2
    SUBTRACT = 3
    LIGHTER_COLOR = 4

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
    
    @abstractmethod
    def GetPixel(self, x: int, y: int) -> Color:
        """Get the color of a pixel on the canvas."""
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

class MatrixImage:
    """
    Class representing an image for the LED matrix.
    """
    def __init__(self, width: int, height: int, filepath: str):
        """
        Initialize a new matrix image.
        
        Args:
            width: Width of the image in pixels
            height: Height of the image in pixels
            filepath: Path to the image file
        """
        self._width = width
        self._height = height
        self.filepath = filepath
        self.pixel_data: List[List[Tuple[int, int, int]]] = []
    
    @property
    def width(self) -> int:
        """Get the width of the image."""
        return self._width
    
    @property
    def height(self) -> int:
        """Get the height of the image."""
        return self._height
        
    def load_pixel_data(self, img):
        """
        Load pixel data from an image.
        
        Args:
            img: PIL Image object
        """
        self.pixel_data = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Get pixel color (r, g, b)
                if x < img.width and y < img.height:
                    pixel = img.getpixel((x, y))
                    # Handle both RGB and RGBA formats
                    if len(pixel) == 4:  # RGBA
                        r, g, b, a = pixel
                        # If transparent, make it black
                        if a == 0:
                            r, g, b = 0, 0, 0
                    else:  # RGB
                        r, g, b = pixel
                    row.append((r, g, b))
                else:
                    # Default to black for out-of-bounds
                    row.append((0, 0, 0))
            self.pixel_data.append(row)


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
    
    def LoadImage(self, image_name: str, target_width: Optional[int] = None, target_height: Optional[int] = None) -> MatrixImage:
        """
        Load an image from the project's images directory.
        
        Args:
            image_name: Name of the image file without extension
            target_width: Optional width to scale the image to (in pixels)
            target_height: Optional height to scale the image to (in pixels)
            
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
        
        # Resize the image if target dimensions are specified
        if target_width is not None or target_height is not None:
            # Get original aspect ratio
            aspect_ratio = img.width / img.height
            
            # Calculate new dimensions respecting aspect ratio
            if target_width is not None and target_height is not None:
                # Both dimensions provided, use as is
                new_width = target_width
                new_height = target_height
            elif target_width is not None:
                # Only width provided, calculate height based on aspect ratio
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:  # target_height is not None
                # Only height provided, calculate width based on aspect ratio
                new_height = target_height
                new_width = int(target_height * aspect_ratio)
            
            # Resize using nearest neighbor resampling
            img = img.resize((new_width, new_height), Image.NEAREST)
        
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
                    
                    # Get pixel color from image
                    r, g, b = image.pixel_data[img_y][img_x]
                    
                    # Skip fully black (transparent) pixels
                    if r == 0 and g == 0 and b == 0:
                        continue
                    
                    # Apply tint if provided
                    if tint:
                        r = (r * tint.red) // 255
                        g = (g * tint.green) // 255
                        b = (b * tint.blue) // 255
                    
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
