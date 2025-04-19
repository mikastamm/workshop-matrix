from datetime import timedelta
from typing import Optional, Type

from src.logging import Logger
from src.ws_display.program_manager import program_manager
from src.ws_display.program_runner import program_runner
from src.ws_display.program_runner_result import program_runner_result, ProgramFinishReason
from src.ws_display.time_keeper import time_keeper
from src.ws_display.workshop_runner import workshop_runner
from src.ws_display.screensavers.burn_program_runner import burn_program_runner


class program_scheduler:
    """
    Class responsible for scheduling programs.
    Decides which program to run and when to switch between programs.
    """
    # Constants
    DISPLAY_SCREENSAVER_AFTER_SECONDS = 30.0  # Switch to screensaver after this many seconds
    
    def __init__(self, program_mgr: program_manager, time_keeper_instance: time_keeper):
        """
        Initialize the program scheduler.
        
        Args:
            program_mgr: The program manager to use for program switching
            time_keeper_instance: The time keeper instance to use for time-related operations
        """
        self.logger = Logger.get_logger()
        self.program_manager = program_mgr
        self.time_keeper = time_keeper_instance
        self.last_program_switch_time = self.time_keeper.time()
        self.last_screen_saver_index = 0

        # Set up burn program timing
        self.burn_start_time = self.time_keeper.now() + timedelta(minutes=3)
        self.burn_duration = timedelta(seconds=program_mgr.get_program_by_type(burn_program_runner).get_play_duration_seconds())
        self.burn_end_time = self.burn_start_time + self.burn_duration
        
        # Set initial program
        self._set_initial_program()
    
    def _set_initial_program(self):
        """
        Set the initial program to workshop runner.
        """
        # Find and set workshop runner as the active program
        for program_type in self.program_manager.program_types.keys():
            if issubclass(program_type, workshop_runner):
                self.program_manager.set_active_program(program_type)
                return
    
    def _should_run_burn_program(self) -> bool:
        """
        When the burn starts, we run the burn program.
        """
        current_time = self.time_keeper.now()
        return current_time >= self.burn_start_time and current_time < self.burn_end_time
    
    def _get_next_screensaver(self, current_program_type: Type[program_runner]) -> Optional[Type[program_runner]]:
        """
        Get the next screensaver program to display.

        """
        screensavers = self.program_manager.get_screensaver_programs()
        if not screensavers:
            return None
        
        screensaver = screensavers[self.last_screen_saver_index]
        if not screensaver:
            self.last_screen_saver_index = (self.last_screen_saver_index + 1 ) % len(screensavers) # skip to next
            return None
        self.last_screen_saver_index = (self.last_screen_saver_index + 1 ) % len(screensavers)
        
        return type(screensaver)
    
    def may_update_program(self, result: program_runner_result) -> None:
        """
        Update the active program based on the program result.
        
        Args:
            result: The result of running the active program
        """
        current_time = self.time_keeper.time()
        active_program = self.program_manager.get_active_program()

        if not active_program:
            # No active program, set initial program
            self._set_initial_program()
            return
        
     # Check if a program has finished
        if result.finished_program_type:
            self._set_initial_program()
            return
        # Check if we should run the burn program
        if self._should_run_burn_program():
            # Check if we're already running the burn program
            if not isinstance(active_program, burn_program_runner):
                # Switch to burn program
                for program_type in self.program_manager.program_types.keys():
                    if issubclass(program_type, burn_program_runner):
                        self.program_manager.set_active_program(program_type)
                        self.last_program_switch_time = current_time
                        return
            # Already running burn program, continue
            return
        elif isinstance(active_program, burn_program_runner):
            # Burn program is running but conditions no longer met, switch back to workshop
            for program_type in self.program_manager.program_types.keys():
                if issubclass(program_type, workshop_runner):
                    self.program_manager.set_active_program(program_type)
                    self.last_program_switch_time = current_time
                    return
        
   
            
        # Check if we should switch to a screensaver
        if not active_program.is_screen_saver():
            if current_time - self.last_program_switch_time >= self.DISPLAY_SCREENSAVER_AFTER_SECONDS:
                # Time to switch to a screensaver
                next_screensaver = self._get_next_screensaver(type(active_program))
                if next_screensaver:
                    self.program_manager.set_active_program(next_screensaver)
                    self.last_program_switch_time = current_time
