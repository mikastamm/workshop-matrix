from enum import Enum
from typing import Optional, Type

from src.ws_display.program_runner import program_runner
from src.ws_display.renderer.graphic_interface import Canvas


class ProgramFinishReason(Enum):
    """
    Enum representing the reason why a program finished.
    """
    SELF_TERMINATED = 0  # Program returned finished=True in render_result
    DURATION_EXPIRED = 1  # Program's play duration expired
    FORCED_TERMINATION = 2  # Program was forcibly terminated (e.g., by scheduler)


class program_runner_result:
    """
    Class representing the result of running a program.
    Contains information about the finished program and the reason for finishing.
    """
    def __init__(
        self,
        canvas: Canvas,
        finished_program_type: Optional[Type[program_runner]] = None,
        finish_reason: Optional[ProgramFinishReason] = None
    ):
        """
        Initialize a program runner result.
        
        Args:
            canvas: The rendered canvas
            finished_program_type: The type of the program that finished
            finish_reason: The reason why the program finished
        """
        self.canvas = canvas
        self.finished_program_type = finished_program_type
        self.finish_reason = finish_reason
