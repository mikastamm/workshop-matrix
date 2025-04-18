from typing import Optional

from src.logging import Logger
from src.ws_display.program_runner import program_runner
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Color
from src.ws_display.render_result import render_result


class teeth_program_runner(program_runner):
    """
    Program runner that displays teeth image at full width and height.
    """
    def __init__(
        self,
        graphic_interface: GraphicInterface,
    ):
        """
        Initialize the teeth program runner.
        
        Args:
            graphic_interface: The graphic interface to render on
        """
        super().__init__(graphic_interface)
        self.logger = Logger.get_logger()
        
        # Colors
        self.image_tint = Color(0, 0,255)  # Red tint
        self.background_color = Color(0, 0, 0)  # Black background
    
    def render(self, canvas: Canvas) -> render_result:
        """
        Render the teeth image at full width and height.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            render_result containing the updated canvas and a finished flag
        """
        # Clear the canvas
        canvas.Clear()
        
        try:
            # Load the teeth image at full size
            teeth_img = self.graphic_interface.LoadImage(
                "teeth", 
                target_width=canvas.width,
                target_height=canvas.height
            )
            
            # Calculate the center of the screen
            center_x = canvas.width // 2
            center_y = canvas.height // 2
            
            # Render the teeth image at the center, covering the full display
            self.graphic_interface.RenderImage(
                canvas,
                teeth_img,
                center_x,
                center_y,
                origin="center-center",
                tint=self.image_tint
            )
            
        except FileNotFoundError:
            self.logger.warning("Teeth image not found")
        
        # Teeth program never finishes on its own
        return render_result(canvas, False)
