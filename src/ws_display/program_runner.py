from abc import ABC, abstractmethod

from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas


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
    def render(self, canvas: Canvas) -> Canvas:
        """
        Render the program on the canvas.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            Updated canvas
        """
        pass
