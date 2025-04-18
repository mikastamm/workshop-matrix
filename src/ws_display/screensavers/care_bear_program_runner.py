import time
from typing import List, Dict, Optional

from src.logging import Logger
from src.ws_display.program_runner import program_runner
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Color
from src.ws_display.render_result import render_result


class care_bear_program_runner(program_runner):
    """
    Program runner that displays the Care Bears image with scrolling text.
    Shows the Care Bears image in the center with "CARE BEARS" scrolling text
    above and below in different colors.
    """
    def __init__(
        self,
        graphic_interface: GraphicInterface,
    ):
        """
        Initialize the Care Bears program runner.
        
        Args:
            graphic_interface: The graphic interface to render on
        """
        super().__init__(graphic_interface)
        self.logger = Logger.get_logger()
        
        # Scrolling text parameters
        self.scroll_text = "CARE BEARS "  # Space at the end for better readability during scrolling
        self.scroll_speed = 10  # pixels per second
        self.scroll_positions = {"top": 0, "bottom": 0}
        self.last_update_time = time.time()
        
        # Image positioning
        self.image_width_percent = 0.9  # 90% of available width
        
        # Colors for text in sequence: green, yellow, red, pink, blue
        self.colors = [
            Color(0, 255, 0),    # Green
            Color(255, 255, 0),  # Yellow
            Color(255, 0, 0),    # Red
            Color(255, 0, 255),  # Pink
            Color(0, 0, 255),    # Blue
        ]
        
        # Load font - use a known working font (emil)
        self.font = self.graphic_interface.CreateFont()
        self.font.LoadFont("TenThinGuys")
       
    
    def render(self, canvas: Canvas) -> render_result:
        """
        Render the Care Bears image with scrolling text.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            render_result containing the updated canvas and a finished flag
        """
        # Clear the canvas
        canvas.Clear()
        
        # Update scroll positions
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Move scroll positions based on elapsed time and speed
        pixels_to_move = int(elapsed_time * self.scroll_speed)
        self.scroll_positions["top"] = (self.scroll_positions["top"] + pixels_to_move) % self.calculate_scroll_width()
        # Move bottom scroll in the opposite direction
        self.scroll_positions["bottom"] = (self.scroll_positions["bottom"] - pixels_to_move) % self.calculate_scroll_width()
        
        # Load and render Care Bears image
        try:
            # Calculate image dimensions (90% of screen width)
            image_width = int(canvas.width * self.image_width_percent)
            care_bears_img = self.graphic_interface.LoadImage(
                "care-bears", 
                target_width=image_width
            )
            
            # Calculate center positions
            center_x = canvas.width // 2
            center_y = canvas.height // 2
            
            # Render image at center of screen
            self.graphic_interface.RenderImage(
                canvas,
                care_bears_img,
                center_x,
                center_y,
                origin="center-center",
            )
            
            # Draw scrolling text at the top of the screen
            top_y = self.font.baseline + 2  # Just enough margin from the top edge
            self.render_scrolling_text(canvas, top_y, self.scroll_positions["top"])
            
            # Draw scrolling text at the bottom of the screen
            # Position text so its baseline is a few pixels from the bottom edge
            bottom_y = canvas.height - self.font.height + self.font.baseline - 2
            self.render_scrolling_text(canvas, bottom_y, self.scroll_positions["bottom"])
            
        except FileNotFoundError:
            self.logger.warning("Care Bears image not found")
            
            # Render the scrolling text at top and bottom if image is missing
            top_y = self.font.baseline + 2  # Just enough margin from the top edge
            self.render_scrolling_text(canvas, top_y, self.scroll_positions["top"])
            
            # Position text so its baseline is a few pixels from the bottom edge
            bottom_y = canvas.height - self.font.height + self.font.baseline - 2
            self.render_scrolling_text(canvas, bottom_y, self.scroll_positions["bottom"])
        
        # Care Bears program never finishes on its own
        return render_result(canvas, False)
    
    def calculate_text_width(self, text: str) -> int:
        """
        Calculate the width of a string in the current font.
        
        Args:
            text: The text to measure
            
        Returns:
            Width of the text in pixels
        """
        width = 0
        for char in text:
            width += self.font.CharacterWidth(ord(char))
        return width
    
    def calculate_scroll_width(self) -> int:
        """
        Calculate the total width needed for scrolling text.
        
        Returns:
            Total width of the scrolling text in pixels
        """
        return self.calculate_text_width(self.scroll_text)
    
    def render_scrolling_text(self, canvas: Canvas, y: int, position: int) -> None:
        """
        Render the scrolling text with different colors for each word.
        
        Args:
            canvas: Canvas to render on
            y: Y position for the text
            position: Current scroll position
        """
        # Draw multiple copies of the text to fill the screen width
        text_width = self.calculate_scroll_width()
        repetitions = (canvas.width // text_width) + 2  # +2 to ensure screen is filled
        
        # Start drawing from the scroll position
        x = -position
        
        # Repeat the text across the screen
        for i in range(repetitions):
            # Render each word with a different color
            current_x = x + (i * text_width)
            self.render_colored_text(canvas, current_x, y)
    
    def render_colored_text(self, canvas: Canvas, x: int, y: int) -> None:
        """
        Render "CARE BEARS" with each word having a different color.
        
        Args:
            canvas: Canvas to render on
            x: X position to start rendering
            y: Y position for the text
        """
        words = self.scroll_text.split()
        current_x = x
        
        for i, word in enumerate(words):
            # Select color based on word index (cycling through colors)
            color_index = i % len(self.colors)
            color = self.colors[color_index]
            
            # Draw the word
            width = self.graphic_interface.DrawText(canvas, self.font, current_x, y, color, word)
            
            # Add space after the word
            current_x += width + self.font.CharacterWidth(ord(' '))
