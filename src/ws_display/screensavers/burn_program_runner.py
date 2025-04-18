import time
from typing import List, Dict, Optional

from src.logging import Logger
from src.ws_display.program_runner import program_runner
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Color
from src.ws_display.render_result import render_result


class burn_program_runner(program_runner):
    """
    Program runner that displays the Burn images with "NOT A CULT" text.
    Shows burn.png in the center, alternating with burn2.png every second.
    Every 5 seconds, for 1 second, the display is inverted with a red background,
    black text, and the image tinted red.
    """
    def __init__(
        self,
        graphic_interface: GraphicInterface,
    ):
        """
        Initialize the Burn program runner.
        
        Args:
            graphic_interface: The graphic interface to render on
        """
        super().__init__(graphic_interface)
        self.logger = Logger.get_logger()
        
        # Image switching parameters
        self.current_image_index = 0  # 0 for burn.png, 1 for burn2.png
        self.last_image_switch_time = time.time()
        self.image_switch_interval = 1.0  # Switch images every 1 second
        
        # Inversion state parameters
        self.invert_active = False
        self.last_invert_start_time = time.time()
        self.invert_start_interval = 5.0  # Start inversion every 5 seconds
        self.invert_duration = 1.0  # Inversion lasts for 1 second
        
        # Colors
        self.COLOR_RED = Color(255, 0, 0)
        self.COLOR_BLACK = Color(0,0, 0)
        
        # Load images - will scale to a reasonable size
        self.images = []
        try:
            # Calculate image dimensions - uses a percentage of screen width
            target_width = int(self.graphic_interface.height * 0.9)
            
            # Load both burn images
            burn_img = self.graphic_interface.LoadImage(
                "burn", 
                target_width=target_width
            )
            burn2_img = self.graphic_interface.LoadImage(
                "burn2", 
                target_width=target_width
            )
            
            self.images = [burn_img, burn2_img]
            
        except Exception as e:
            self.logger.error(f"Failed to load burn images: {e}")
        
        # Load fonts
        try:
            # Default font (emil)
            self.default_font = self.graphic_interface.CreateFont()
            self.default_font.LoadFont("fonts/emil.ttf")
            
            # Inverted font (Glyphexon)
            self.inverted_font = self.graphic_interface.CreateFont()
            self.inverted_font.LoadFont("fonts/glyph.ttf")
        except Exception as e:
            self.logger.error(f"Failed to load fonts: {e}")
            # Try to load any available font as fallback
            self.default_font = self.graphic_interface.CreateFont()
            self.default_font.LoadFont("fonts/5x7.ttf")
            self.inverted_font = self.default_font
    
    def render(self, canvas: Canvas) -> render_result:
        """
        Render the Burn program with image switching and inversion effects.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            render_result containing the updated canvas and a finished flag
        """
        # Clear the canvas
        canvas.Clear()
        
        # Get current time
        current_time = time.time()
        
        # Check if we need to switch images
        if current_time - self.last_image_switch_time >= self.image_switch_interval:
            self.current_image_index = 1 - self.current_image_index  # Toggle between 0 and 1
            self.last_image_switch_time = current_time
        
        # Check inversion state
        if self.invert_active:
            # Check if inversion should end
            if current_time - self.last_invert_start_time >= self.invert_duration:
                self.invert_active = False
        else:
            # Check if inversion should start
            if current_time - self.last_invert_start_time >= self.invert_start_interval:
                self.invert_active = True
                self.last_invert_start_time = current_time
        
        # Set state based on inversion
        current_font = self.inverted_font if self.invert_active else self.default_font
        text_color = self.COLOR_BLACK if self.invert_active else self.COLOR_RED
        image_tint = self.COLOR_BLACK if self.invert_active else self.COLOR_RED
        
        # If inverted, draw red background
        if self.invert_active:
            for y in range(canvas.height):
                self.graphic_interface.DrawLine(canvas, 0, y, canvas.width - 1, y, self.COLOR_RED)
        
        # Render the current burn image if available
        if len(self.images) >= 2:
            current_image = self.images[self.current_image_index]
            
            # Calculate center positions
            center_x = canvas.width // 2
            center_y = canvas.height // 2 - 6
            
            # Render image at center of screen
            self.graphic_interface.RenderImage(
                canvas,
                current_image,
                center_x,
                center_y,
                origin="center-center",
                tint=image_tint
            )
            
            # Draw "NOT A CULT" text below the image
            text = "NOT A CULT"
            text_width = self.calculate_text_width(current_font, text)
            
            # Position text below image and centered horizontally
            text_x = center_x - text_width // 2
            text_y = canvas.height - self.default_font.height +1  # Adjust spacing as needed
            
            # Draw the text
            self.graphic_interface.DrawText(canvas, current_font, text_x, text_y, text_color, text)
        else:
            # If images failed to load, just show the text
            text = "NOT A CULT"
            text_width = self.calculate_text_width(current_font, text)
            
            # Center the text
            text_x = canvas.width // 2 - text_width // 2
            text_y = canvas.height // 2
            
            # Draw the text
            self.graphic_interface.DrawText(canvas, current_font, text_x, text_y, text_color, text)
        
        # Burn program never finishes on its own
        return render_result(canvas, False)
    
    def calculate_text_width(self, font, text: str) -> int:
        """
        Calculate the width of a string in the provided font.
        
        Args:
            font: The font to use for calculation
            text: The text to measure
            
        Returns:
            Width of the text in pixels
        """
        width = 0
        for char in text:
            width += font.CharacterWidth(ord(char))
        return width
