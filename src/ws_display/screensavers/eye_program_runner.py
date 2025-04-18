import time
from typing import List, Optional

from src.logging import Logger
from src.ws_display.program_runner import program_runner
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Color
from src.ws_display.render_result import render_result


class eye_program_runner(program_runner):
    """
    Program runner that displays eye animation sequence.
    Displays eye images in sequence and ends when the closed eye is shown.
    """
    def __init__(
        self,
        graphic_interface: GraphicInterface,
        target_width: Optional[int] = None, 
        target_height: Optional[int] = None,
    ):
        """
        Initialize the eye program runner.
        
        Args:
            graphic_interface: The graphic interface to render on
            target_width: Optional width to scale the images to (in pixels)
            target_height: Optional height to scale the images to (in pixels)
        """
        self.current_image_name =""
        super().__init__(graphic_interface)
        self.logger = Logger.get_logger()
        
        # Eye image paths in sequence order
        self.image_names = ["eye", "eyeL", "eyeR","eyeClose"]
        
        # Preload images
        self.images = {}
        for image_name in self.image_names:
            try:
                self.images[image_name] = self.graphic_interface.LoadImage(
                    image_name, 
                    target_width=target_width, 
                    target_height=target_height
                )
            except FileNotFoundError:
                self.logger.warning(f"Eye image '{image_name}' not found")
                self.images[image_name] = None
        
        # State variables
        self.current_image_index = 0
        self.last_image_change_time = time.time()
        self.image_display_time = 1  # Display each image for 1.5 seconds
        
        # Colors
        self.image_tint = Color(255, 0, 0)  # Red tint
        self.background_color = Color(0, 0, 0)  # Black background
    
    def render(self, canvas: Canvas) -> render_result:
        """
        Render the current eye image in the sequence.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            render_result containing the updated canvas and a finished flag
        """
        # Clear the canvas
        canvas.Clear()
        
        # Check if it's time to change the image
        current_time = time.time()
        if current_time - self.last_image_change_time >= self.image_display_time:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_names)
            self.last_image_change_time = current_time
        
        # Get the current image name
        self.prev_image_name = self.current_image_name
        self.current_image_name = self.image_names[self.current_image_index]
        
        # Get the preloaded image
        eye_img = self.images.get(self.current_image_name)
        if eye_img:
            # Calculate the center of the screen
            center_x = canvas.width // 2
            center_y = canvas.height // 2
            
            # Render the eye image at the center
            self.graphic_interface.RenderImage(
                canvas,
                eye_img,
                center_x,
                center_y,
                origin="center-center",
                tint=self.image_tint
            )
        else:
            self.logger.warning(f"Eye image '{self.current_image_name}' could not be loaded")
        
        # Check if we should finish the program (when showing the closed eye)
        is_finished = self.prev_image_name == "eyeClose"
        if is_finished:
            self.prev_image_name = ""
        return render_result(canvas, is_finished)