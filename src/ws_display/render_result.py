from src.ws_display.renderer.graphic_interface import Canvas

class render_result:
    """
    Class representing the result of rendering a program.
    Contains the canvas and a flag indicating if the program has finished.
    """
    def __init__(self, canvas: Canvas, finished: bool = False):
        """
        Initialize a render result.
        
        Args:
            canvas: The rendered canvas
            finished: Whether the program has finished (True) or should continue (False)
        """
        self.canvas = canvas
        self.finished = finished
