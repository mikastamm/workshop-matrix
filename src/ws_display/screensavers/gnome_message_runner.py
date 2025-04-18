from src.logging import Logger
from src.ws_display.program_runner import program_runner
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Color, Font
from src.ws_display.render_result import render_result


class gnome_message_runner(program_runner):
    """
    Program runner that displays a gnome image with a message.
    """
    def is_screen_saver(self) -> bool:
        """
        Screensaver programs can be choosen randomly, which happens automatically after some delay.
        Set this to false if you want full control over when to start the program.
        
        Returns:
            True if it is a screensaver, False otherwise
        """
        return True
    
    def get_play_duration_seconds(self):
        return 30.0

    def __init__(
        self,
        graphic_interface: GraphicInterface,
        message_font: Font,
    ):
        """
        Initialize the gnome message runner.
        
        Args:
            graphic_interface: The graphic interface to render on
            message_font: Font to use for the message display
        """
        super().__init__(graphic_interface)
        self.logger = Logger.get_logger()
        self.message_font = message_font
        
        # Set the message on two lines
        self.message_line1 = "Please stop"
        self.message_line2 = "licking gnomes"
        
        # Colors - red as requested
        self.text_color = Color(255, 0, 0)  # Red
        self.image_tint = Color(255, 0, 0)  # Red
        self.background_color = Color(0, 0, 0)  # Black background
    
    def render(self, canvas: Canvas) -> render_result:
        """
        Render the gnome image and message.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            render_result containing the updated canvas and a finished flag
        """
        # Clear the canvas
        canvas.Clear()
        
        try:
            # Load the gnome image
            gnome_img = self.graphic_interface.LoadImage("gnome")
            
            # Calculate the center of the screen
            center_x = canvas.width // 2
            center_y = canvas.height // 2 - 8  # Slightly above center to make room for text
            
            # Render the gnome image
            self.graphic_interface.RenderImage(
                canvas,
                gnome_img,
                center_x,
                center_y,
                origin="center-center",
                tint=self.image_tint
            )
            
            # Calculate the width of each line of the message
            message_line1_width = self.calculate_text_width(self.message_font, self.message_line1)
            message_line2_width = self.calculate_text_width(self.message_font, self.message_line2)
            
            # Calculate positions for centered text
            text_line1_x = center_x - message_line1_width // 2
            text_line1_y = center_y + gnome_img.height // 2 + 5  # Below the image
            
            text_line2_x = center_x - message_line2_width // 2
            text_line2_y = text_line1_y + self.message_font.height - 3  # Below the first line with spacing
            
            # Render both lines of the message
            self.graphic_interface.DrawText(
                canvas, self.message_font, text_line1_x, text_line1_y, self.text_color, self.message_line1
            )
            
            self.graphic_interface.DrawText(
                canvas, self.message_font, text_line2_x, text_line2_y, self.text_color, self.message_line2
            )
            
        except FileNotFoundError:
            # If image loading fails, show a fallback message
            self.logger.warning("Gnome image not found, using text-only fallback")
            
            center_x = canvas.width // 2
            center_y = canvas.height // 2
            
            # Calculate the width of each line of the message
            message_line1_width = self.calculate_text_width(self.message_font, self.message_line1)
            message_line2_width = self.calculate_text_width(self.message_font, self.message_line2)
            
            # Calculate positions for centered text
            text_line1_x = center_x - message_line1_width // 2
            text_line1_y = center_y - self.message_font.height
            
            text_line2_x = center_x - message_line2_width // 2
            text_line2_y = center_y + 2  # Below the first line with spacing
            
            # Render both lines of the message
            self.graphic_interface.DrawText(
                canvas, self.message_font, text_line1_x, text_line1_y, self.text_color, self.message_line1
            )
            
            self.graphic_interface.DrawText(
                canvas, self.message_font, text_line2_x, text_line2_y, self.text_color, self.message_line2
            )
        
        # Gnome message runner never finishes on its own
        return render_result(canvas, False)
    
    def calculate_text_width(self, font: Font, text: str) -> int:
        """
        Calculate the width of a text string in the given font.
        
        Args:
            font: Font to use for calculation
            text: Text to calculate width for
            
        Returns:
            Width of the text in pixels
        """
        width = 0
        for char in text:
            width += font.CharacterWidth(ord(char))
        return width
