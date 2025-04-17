from datetime import datetime
from src.ws_display.workshop_loader import workshop_loader
from src.logging import Logger

def main():
    # Get the logger
    logger = Logger.get_logger()
    logger.info("Starting workshop loader test")
    
    # Create a lambda function to get the current datetime
    get_current_datetime = lambda: datetime.now()
    
    # Create a workshop_loader instance
    loader = workshop_loader(get_current_datetime)
    
    # Load workshops
    workshops = loader.get_workshops()
    
    # Print information about all workshops
    logger.info(f"Loaded {len(workshops.workshops)} workshops")
    
    # Print upcoming workshops
    upcoming = workshops.get_upcoming_workshops(5)  # Get top 5 upcoming workshops
    logger.info(f"Upcoming workshops ({len(upcoming)}):")
    for workshop in upcoming:
        minutes = workshop.minutes_until_workshop
        hours = minutes / 60 if minutes is not None else None
        
        if hours is not None:
            time_str = f"{int(hours)}h {int(minutes % 60)}m"
        else:
            time_str = "Unknown"
            
        logger.info(f"- {workshop.title} by {workshop.host or 'Unknown'} in {time_str}")
    
    # Print current workshops
    current = workshops.get_current_workshops()
    logger.info(f"Current workshops ({len(current)}):")
    for workshop in current:
        logger.info(f"- {workshop.title} by {workshop.host or 'Unknown'} at {workshop.location or 'Unknown location'}")

if __name__ == "__main__":
    main()
