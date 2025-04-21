from typing import Dict, List, Optional, Type, TypeVar

from src.logging import Logger
from src.ws_display.program_runner import program_runner
from src.ws_display.program_runner_result import program_runner_result, ProgramFinishReason
from src.ws_display.render_result import render_result
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas
from src.ws_display.time_keeper import time_keeper

T = TypeVar('T', bound=program_runner)

class program_manager:
    """
    Class responsible for managing program runners.
    Handles program initialization, switching, and rendering.
    """
    def __init__(self, graphic_interface: GraphicInterface, time_keeper_instance: Optional[time_keeper] = None):
        """
        Initialize the program manager.
        
        Args:
            graphic_interface: The graphic interface to render on
            time_keeper_instance: Optional time keeper instance for time-related operations
        """
        self.logger = Logger.get_logger()
        self.graphic_interface = graphic_interface
        self.time_keeper = time_keeper_instance
        self.programs: List[program_runner] = []
        self.program_types: Dict[Type[program_runner], program_runner] = {}
        self.active_program: Optional[program_runner] = None
        self.program_start_time: float = 0 if not self.time_keeper else self.time_keeper.time()
        self.canvas: Optional[Canvas] = None
        
        # Initialize programs
        self.initialize_programs()
        
    def initialize_programs(self):
        """
        Initialize all available program runners.
        """
        # Create a canvas for rendering
        self.canvas = self.graphic_interface.CreateFrameCanvas()
        
        # Import program runners here to avoid circular imports
        from src.ws_display.workshop_runner import workshop_runner
        from src.ws_display.screensavers.gnome_message_runner import gnome_message_runner
        from src.ws_display.screensavers.eye_program_runner import eye_program_runner
        from src.ws_display.screensavers.teeth_program_runner import teeth_program_runner
        from src.ws_display.screensavers.care_bear_program_runner import care_bear_program_runner
        from src.ws_display.screensavers.burn_program_runner import burn_program_runner
        
        # Add program runners
        programs_to_add = [
            eye_program_runner(
                graphic_interface=self.graphic_interface,
                target_width=80,
                target_height=80,
            ),
            workshop_runner(
                graphic_interface=self.graphic_interface,
                time_keeper_instance=self.time_keeper
            ),
            gnome_message_runner(
                graphic_interface=self.graphic_interface,
            ),
            teeth_program_runner(
                graphic_interface=self.graphic_interface,
            ),
            care_bear_program_runner(
                graphic_interface=self.graphic_interface,
            ),
            burn_program_runner(
                graphic_interface=self.graphic_interface,
            )
        ]
        
        # Add programs to list and dictionary
        for program in programs_to_add:
            self.programs.append(program)
            self.program_types[type(program)] = program
        
        # Set default active program
        if self.programs:
            self.set_active_program(type(self.programs[0]))
    
    
    def get_program_by_type(self, program_type: Type[T]) -> Optional[T]:
        """
        Get a program runner by its type.
        
        Args:
            program_type: The type of the program runner to get
            
        Returns:
            The program runner instance or None if not found
        """
        return self.program_types.get(program_type)
    
    def set_active_program(self, program_type: Type[program_runner]) -> bool:
        """
        Set the active program by its type.
        
        Args:
            program_type: The type of the program to set as active
            
        Returns:
            True if the program was found and set as active, False otherwise
        """
        program = self.get_program_by_type(program_type)
        if program:
            self.active_program = program
            self.program_start_time = self.time_keeper.time() if self.time_keeper else 0
            self.logger.info(f"Set active program to {program_type.__name__}")
            return True
        else:
            self.logger.error(f"Program type {program_type.__name__} not found")
            return False
    
    def get_active_program(self) -> Optional[program_runner]:
        """
        Get the currently active program.
        
        Returns:
            The active program runner or None if no program is active
        """
        return self.active_program
    
    def get_screensaver_programs(self) -> List[program_runner]:
        """
        Get all programs that are screensavers.
        
        Returns:
            List of program runners that are screensavers
        """
        return [program for program in self.programs if program.is_screen_saver()]
    
    def run_program(self) -> program_runner_result:
        """
        Run the active program for one frame.
        
        Returns:
            A program_runner_result containing information about the program's execution
        """
        if not self.active_program or not self.canvas:
            # No active program or canvas, return empty result
            return program_runner_result(self.graphic_interface.CreateFrameCanvas())
        
        # Render the active program
        result = self.active_program.render(self.canvas)
        
        # Check if the program has finished on its own
        if result.finished:
            self.logger.info(f"Program {type(self.active_program).__name__} finished on its own")
            return program_runner_result(
                result.canvas,
                type(self.active_program),
                ProgramFinishReason.SELF_TERMINATED
            )
        
        # Check if the program's play duration has expired
        current_time = self.time_keeper.time() if self.time_keeper else 0
        play_duration = self.active_program.get_play_duration_seconds()
        
        if play_duration is not None and current_time - self.program_start_time >= play_duration:
            self.logger.info(f"Program {type(self.active_program).__name__} play duration expired")
            return program_runner_result(
                result.canvas,
                type(self.active_program),
                ProgramFinishReason.DURATION_EXPIRED
            )
        
        # Program is still running
        return program_runner_result(result.canvas)
