import os
import yaml
from datetime import datetime
from typing import List, Callable, Optional
from dataclasses import dataclass

from src.logging import Logger

@dataclass
class Workshop:
    """
    Class representing a workshop with properties from the YAML file
    and additional calculated properties.
    """
    title: str
    location: Optional[str]
    host: Optional[str]
    description: str
    startTime: Optional[str]
    durationHours: Optional[float]
    
    # Reference to the function that provides current datetime
    _get_current_datetime: Callable[[], datetime]
    
    @property
    def minutes_until_workshop(self) -> Optional[float]:
        """
        Calculate the minutes until the workshop starts.
        Returns None if the workshop has no start time.
        """
        if not self.startTime:
            return None
        
        try:
            # Get current time from the provided function
            current_time = self._get_current_datetime()
            
            # Parse the workshop start time
            workshop_time = datetime.fromisoformat(self.startTime)
            
            # Calculate the time difference in minutes
            time_diff = workshop_time - current_time
            minutes = time_diff.total_seconds() / 60
            
            return minutes
        except Exception as e:
            logger = Logger.get_logger()
            logger.error(f"Error calculating minutes until workshop '{self.title}': {e}")
            return None


class Workshops:
    """
    Class containing a collection of Workshop instances.
    """
    def __init__(self, workshops: List[Workshop], get_current_datetime: Callable[[], datetime]):
        """
        Initialize the Workshops class with a list of Workshop instances.
        
        Args:
            workshops: List of Workshop instances
            get_current_datetime: Function that returns the current datetime
        """
        self.workshops = workshops
        self._get_current_datetime = get_current_datetime
        
        logger = Logger.get_logger()
        logger.info(f"Initialized Workshops with {len(workshops)} workshops")
    
    def get_upcoming_workshops(self, max_count: Optional[int] = None) -> List[Workshop]:
        """
        Get a list of upcoming workshops sorted by start time.
        
        Args:
            max_count: Maximum number of workshops to return
            
        Returns:
            List of upcoming workshops sorted by start time
        """
        # Filter workshops with a valid start time and positive minutes until start
        upcoming = [w for w in self.workshops 
                   if w.startTime and w.minutes_until_workshop is not None and w.minutes_until_workshop > 0]
        
        # Sort by start time (minutes until workshop)
        upcoming.sort(key=lambda w: w.minutes_until_workshop)
        
        # Limit the number of results if specified
        if max_count is not None:
            upcoming = upcoming[:max_count]
            
        return upcoming
    
    def get_current_workshops(self) -> List[Workshop]:
        """
        Get a list of currently ongoing workshops.
        
        Returns:
            List of currently ongoing workshops
        """
        current = []
        
        for workshop in self.workshops:
            if (workshop.startTime and workshop.durationHours and 
                workshop.minutes_until_workshop is not None):
                
                minutes_until = workshop.minutes_until_workshop
                duration_minutes = workshop.durationHours * 60
                
                # Workshop is ongoing if it has started but not yet ended
                if minutes_until <= 0 and minutes_until > -duration_minutes:
                    current.append(workshop)
        
        return current


class workshop_loader:
    """
    Class for loading workshops from a YAML file.
    """
    def __init__(self, get_current_datetime: Callable[[], datetime]):
        """
        Initialize the workshop_loader with a function to get the current datetime.
        
        Args:
            get_current_datetime: Function that returns the current datetime
        """
        self._get_current_datetime = get_current_datetime
        self.logger = Logger.get_logger()
        self.logger.info("Initialized workshop_loader")
    
    def get_workshops(self) -> Workshops:
        """
        Load workshops from the YAML file and return a Workshops instance.
        
        Returns:
            Workshops instance containing Workshop objects
        """
        workshops_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                     "data", "workshops.yaml")
        
        self.logger.info(f"Loading workshops from {workshops_path}")
        
        try:
            with open(workshops_path, 'r') as file:
                data = yaml.safe_load(file)
                
                if not data:
                    self.logger.warning("No workshops found in YAML file")
                    return Workshops([], self._get_current_datetime)
                
                workshop_list = []
                
                for workshop_data in data:
                    # Create Workshop instance with the current datetime function
                    workshop = Workshop(
                        title=workshop_data.get('title', 'Untitled Workshop'),
                        location=workshop_data.get('location'),
                        host=workshop_data.get('host'),
                        description=workshop_data.get('description', ''),
                        startTime=workshop_data.get('startTime'),
                        durationHours=workshop_data.get('durationHours'),
                        _get_current_datetime=self._get_current_datetime
                    )
                    workshop_list.append(workshop)
                
                self.logger.info(f"Loaded {len(workshop_list)} workshops")
                return Workshops(workshop_list, self._get_current_datetime)
                
        except Exception as e:
            self.logger.error(f"Error loading workshops: {e}")
            return Workshops([], self._get_current_datetime)
