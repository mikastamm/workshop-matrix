import time
from datetime import datetime, timedelta
from typing import Optional

class time_keeper:
    """
    Class that provides wrappers for time.time() and datetime.now() with the ability to scale time.
    """
    def __init__(self, initial_timescale: float = 1.0):
        """
        Initialize the time keeper with a given timescale.
        
        Args:
            initial_timescale: Initial time scale factor (default: 1.0)
        """
        self._timescale = initial_timescale
        self._last_real_time = time.time()
        self._last_returned_time = self._last_real_time
        
        self._last_real_datetime = datetime.now()
        self._last_returned_datetime = self._last_real_datetime
    
    def set_timescale(self, timescale: float) -> None:
        """
        Set the time scale factor.
        
        Args:
            timescale: New time scale factor
        """
        if timescale <= 0:
            raise ValueError("Timescale must be positive")
        
        # Update the last times before changing the timescale
        self.time()
        self.now()
        
        self._timescale = timescale
    
    def get_timescale(self) -> float:
        """
        Get the current time scale factor.
        
        Returns:
            Current time scale factor
        """
        return self._timescale
    
    def time(self) -> float:
        """
        Get the current scaled time.
        
        Returns:
            Current scaled time in seconds since the epoch
        """
        current_real_time = time.time()
        real_time_diff = current_real_time - self._last_real_time
        scaled_time_diff = real_time_diff * self._timescale
        
        self._last_real_time = current_real_time
        self._last_returned_time += scaled_time_diff
        
        return self._last_returned_time
    
    def now(self) -> datetime:
        """
        Get the current scaled datetime.
        
        Returns:
            Current scaled datetime
        """
        current_real_datetime = datetime.now()
        real_datetime_diff = (current_real_datetime - self._last_real_datetime).total_seconds()
        scaled_datetime_diff = real_datetime_diff * self._timescale
        
        self._last_real_datetime = current_real_datetime
        self._last_returned_datetime += timedelta(seconds=scaled_datetime_diff)
        
        return self._last_returned_datetime
