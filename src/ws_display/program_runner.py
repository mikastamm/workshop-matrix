from abc import ABC, abstractmethod

from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas
from src.ws_display.render_result import render_result


class program_runner(ABC):
    """
    Abstract base class for different program display modes.
    """
    def __init__(self, graphic_interface: GraphicInterface):
        """
        Initialize the program runner.
        
        Args:
            graphic_interface: The graphic interface to render on
        """
        self.graphic_interface = graphic_interface
    
    @abstractmethod
    def render(self, canvas: Canvas) -> render_result:
        """
        Render the program on the canvas.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            render_result containing the updated canvas and a finished flag
        """
        pass
