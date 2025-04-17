import os
import time
from typing import Any, Dict, Optional, Tuple, cast
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk, ImageFont
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.logging import Logger
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Font, Color

class EmulatedCanvas(Canvas):
    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height
        self._image = Image.new('RGB', (width, height), color=(0, 0, 0))
        self._draw = ImageDraw.Draw(self._image)
    
    def Clear(self) -> None:
        self._draw.rectangle([(0, 0), (self._width, self._height)], fill=(0, 0, 0))
    
    def SetPixel(self, x: int, y: int, color: Color) -> None:
        if 0 <= x < self._width and 0 <= y < self._height:
            self._image.putpixel((x, y), (color.red, color.green, color.blue))
    
    @property
    def width(self) -> int:
        return self._width
    
    @property
    def height(self) -> int:
        return self._height
    
    @property
    def image(self) -> Image.Image:
        """Get the underlying PIL Image."""
        return self._image
    
    @property
    def draw(self) -> ImageDraw.ImageDraw:
        """Get the underlying PIL ImageDraw."""
        return self._draw

class EmulatedFont(Font):
    def __init__(self):
        self._font = None
        self._font_path = None
        self._font_size = 10  # Default size
        self._loaded = False
    
    def LoadFont(self, file: str) -> None:
        try:
            # Check if it's a BDF font
            if file.lower().endswith('.bdf'):
                # For BDF fonts, we'll use a simple approximation with a default font
                # since PIL doesn't directly support BDF
                self._font_path = None
                self._loaded = True
                Logger.get_logger().warning(f"BDF fonts not fully supported in emulation. Using approximation for {file}")
            else:
                # For TTF/OTF fonts
                self._font_path = file
                self._font = ImageFont.truetype(file, self._font_size)
                self._loaded = True
                Logger.get_logger().info(f"Loaded font {file}")
        except Exception as e:
            Logger.get_logger().error(f"Couldn't load font {file}: {e}")
            raise Exception(f"Couldn't load font {file}: {e}")
    
    def CharacterWidth(self, char: int) -> int:
        if not self._loaded:
            raise Exception("Font not loaded")
        
        if self._font:
            # For TTF/OTF fonts
            char_str = chr(char)
            bbox = self._font.getbbox(char_str)
            return bbox[2] - bbox[0]
        else:
            # Approximation for BDF fonts
            return self._font_size // 2
    
    def DrawGlyph(self, canvas: Any, x: int, y: int, color: Color, char: int) -> int:
        if not self._loaded:
            raise Exception("Font not loaded")
        
        if not isinstance(canvas, EmulatedCanvas):
            raise TypeError("Canvas must be an EmulatedCanvas")
        
        char_str = chr(char)
        
        if self._font:
            # For TTF/OTF fonts
            canvas.draw.text((x, y - self.baseline), char_str, fill=(color.red, color.green, color.blue), font=self._font)
            return self.CharacterWidth(char)
        else:
            # Approximation for BDF fonts
            canvas.draw.text((x, y - self.baseline), char_str, fill=(color.red, color.green, color.blue))
            return self.CharacterWidth(char)
    
    @property
    def height(self) -> int:
        if not self._loaded:
            raise Exception("Font not loaded")
        
        if self._font:
            # For TTF/OTF fonts
            return self._font.getbbox("Áy")[3]  # Use a string with ascenders and descenders
        else:
            # Approximation for BDF fonts
            return self._font_size
    
    @property
    def baseline(self) -> int:
        if not self._loaded:
            raise Exception("Font not loaded")
        
        if self._font:
            # For TTF/OTF fonts - approximate baseline as 80% of height
            return int(self.height * 0.8)
        else:
            # Approximation for BDF fonts
            return int(self._font_size * 0.8)

class EmulatedGraphicInterface(GraphicInterface):
    def __init__(self, width: int, height: int, config_brightness_override: float = 1.0, scale: int = 8, 
                 pixel_spacing: float = 0.4, use_circles: bool = True):
        super().__init__(config_brightness_override)
        self._width = width
        self._height = height
        self._scale = scale  # Scale factor for display (makes the small matrix more visible)
        self._pixel_spacing = pixel_spacing  # Spacing between pixels (0.0 - 1.0)
        self._use_circles = use_circles  # Whether to render pixels as circles
        
        # We'll create the window when needed
        self._root = None
        self._tk_canvas = None
        self._current_photo = None
        self._window_created = False
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        Logger.get_logger().info(f"Initialized EmulatedGraphicInterface with dimensions {width}x{height}, scale {scale}")
    
    def _ensure_window_created(self):
        """Ensure the window is created if it doesn't exist yet."""
        if not self._window_created:
            # Create the window in the main thread
            self._root = tk.Toplevel()
            self._root.title("LED Matrix Emulator")
            self._root.geometry(f"{self._width * self._scale}x{self._height * self._scale}")
            self._root.deiconify()  # Make sure the window is visible
            self._root.lift()  # Bring window to front
            
            # Create a canvas to display the image
            self._tk_canvas = tk.Canvas(self._root, width=self._width * self._scale, height=self._height * self._scale)
            self._tk_canvas.pack()
            
            self._window_created = True
            Logger.get_logger().info("Created Tkinter window for LED Matrix Emulator")
    
    def CreateFrameCanvas(self) -> Canvas:
        return EmulatedCanvas(self._width, self._height)
    
    def SwapOnVSync(self, canvas: Canvas) -> Canvas:
        if not isinstance(canvas, EmulatedCanvas):
            raise TypeError("Canvas must be an EmulatedCanvas")
        
        # Apply brightness adjustment
        adjusted_image = self._adjust_brightness(canvas.image)
        
        # Create a new image with gutters between pixels
        if self._pixel_spacing > 0 or self._use_circles:
            # Calculate pixel and gutter sizes
            pixel_size = self._scale
            gutter_size = int(pixel_size * self._pixel_spacing)
            
            # Calculate the total size with gutters
            display_width = self._width * (pixel_size + gutter_size)
            display_height = self._height * (pixel_size + gutter_size)
            
            # Create a black background image
            display_image = Image.new('RGB', (display_width, display_height), color=(0, 0, 0))
            draw = ImageDraw.Draw(display_image)
            
            # Draw each pixel as a circle or square with spacing
            for x in range(self._width):
                for y in range(self._height):
                    pixel_color = adjusted_image.getpixel((x, y))
                    if pixel_color != (0, 0, 0):  # Only draw non-black pixels
                        # Calculate position with gutters
                        pixel_x = x * (pixel_size + gutter_size) + gutter_size // 2
                        pixel_y = y * (pixel_size + gutter_size) + gutter_size // 2
                        
                        if self._use_circles:
                            # Draw a circle for each pixel
                            radius = pixel_size // 2
                            center_x = pixel_x + radius
                            center_y = pixel_y + radius
                            draw.ellipse(
                                [(center_x - radius, center_y - radius), 
                                 (center_x + radius, center_y + radius)], 
                                fill=pixel_color
                            )
                        else:
                            # Draw a square for each pixel
                            draw.rectangle(
                                [(pixel_x, pixel_y), 
                                 (pixel_x + pixel_size, pixel_y + pixel_size)], 
                                fill=pixel_color
                            )
            
            scaled_image = display_image
        else:
            # Just scale the image without gutters
            scaled_image = adjusted_image.resize((self._width * self._scale, self._height * self._scale), Image.NEAREST)
        
        # Save the image to a file in the runtime_artifacts directory
        os.makedirs("runtime_artifacts", exist_ok=True)
        scaled_image.save("runtime_artifacts/current_display.png")
        
        # If the window is created, update it
        if self._window_created and self._root and self._tk_canvas:
            try:
                # Update window size if needed
                if self._tk_canvas.winfo_width() != scaled_image.width or self._tk_canvas.winfo_height() != scaled_image.height:
                    self._tk_canvas.config(width=scaled_image.width, height=scaled_image.height)
                    self._root.geometry(f"{scaled_image.width}x{scaled_image.height}")
                
                # Convert to PhotoImage and display
                self._current_photo = ImageTk.PhotoImage(scaled_image)
                self._tk_canvas.delete("all")
                self._tk_canvas.create_image(0, 0, image=self._current_photo, anchor=tk.NW)
                self._root.update()
            except tk.TclError:
                # Window was closed
                self._window_created = False
        else:
            # Try to create the window
            try:
                self._ensure_window_created()
            except Exception as e:
                Logger.get_logger().warning(f"Could not create window: {e}")
        
        # Create a new canvas for the next frame
        return EmulatedCanvas(self._width, self._height)
    
    def _adjust_brightness(self, image: Image.Image) -> Image.Image:
        """Adjust the image brightness based on the effective brightness."""
        if self.effective_brightness >= 1.0:
            return image
        
        # Create a copy of the image
        adjusted = image.copy()
        
        # Apply brightness adjustment
        brightness = self.effective_brightness
        if brightness <= 0:
            return Image.new('RGB', image.size, (0, 0, 0))
        
        # Use PIL's point method to adjust brightness
        enhancer = Image.new('RGB', image.size, (0, 0, 0))
        return Image.blend(enhancer, adjusted, brightness)
    
    def DrawText(self, canvas: Canvas, font: Font, x: int, y: int, color: Color, text: str) -> int:
        if not isinstance(canvas, EmulatedCanvas):
            raise TypeError("Canvas must be an EmulatedCanvas")
        
        if not isinstance(font, EmulatedFont):
            raise TypeError("Font must be an EmulatedFont")
        
        # For pixel-perfect rendering without anti-aliasing, we'll draw each character pixel by pixel
        width = 0
        for char in text:
            # Draw each character as individual pixels
            for i in range(len(char)):
                # Get the character's bitmap representation
                if font._font:
                    # For TTF fonts, render to a small temporary image and extract pixels
                    temp_img = Image.new('RGB', (font._font_size, font._font_size), color=(0, 0, 0))
                    temp_draw = ImageDraw.Draw(temp_img)
                    temp_draw.text((0, 0), char, fill=(255, 255, 255), font=font._font)
                    
                    # Copy non-black pixels to the canvas
                    char_width = 0
                    for px in range(temp_img.width):
                        for py in range(temp_img.height):
                            pixel = temp_img.getpixel((px, py))
                            if pixel[0] > 128:  # If bright enough (not black or dark gray)
                                canvas.SetPixel(x + width + px, y - font.baseline + py, color)
                                char_width = max(char_width, px + 1)
                    
                    width += char_width + 1  # Add spacing
                else:
                    # For BDF or missing fonts, use a simple fixed-width approach
                    char_width = font._font_size // 2
                    # Draw a simple block for the character
                    for px in range(char_width):
                        for py in range(font._font_size):
                            canvas.SetPixel(x + width + px, y - font.baseline + py, color)
                    width += char_width + 1  # Add spacing
        
        return width
    
    def DrawCircle(self, canvas: Canvas, x: int, y: int, r: int, color: Color) -> None:
        if not isinstance(canvas, EmulatedCanvas):
            raise TypeError("Canvas must be an EmulatedCanvas")
        
        # Draw the circle
        canvas.draw.ellipse([(x - r, y - r), (x + r, y + r)], outline=(color.red, color.green, color.blue))
    
    def DrawLine(self, canvas: Canvas, x1: int, y1: int, x2: int, y2: int, color: Color) -> None:
        if not isinstance(canvas, EmulatedCanvas):
            raise TypeError("Canvas must be an EmulatedCanvas")
        
        # Draw the line
        canvas.draw.line([(x1, y1), (x2, y2)], fill=(color.red, color.green, color.blue))
    
    def CreateFont(self) -> Font:
        return EmulatedFont()
    
    @property
    def width(self) -> int:
        return self._width
    
    @property
    def height(self) -> int:
        return self._height
    
    def __del__(self) -> None:
        """Clean up resources when the object is deleted."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)
