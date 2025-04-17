import time
from datetime import datetime, timedelta
from typing import List, Callable, Optional, Tuple

from src.logging import Logger
from src.ws_display.workshop_loader import workshop_loader, Workshop, Workshops
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Font, Color

class workshop_runner:
    """
    Class responsible for rendering workshops on the display.
    """
    def __init__(
        self,
        graphic_interface: GraphicInterface,
        workshop_font: Font,
        location_font: Font,
        get_current_datetime: Callable[[], datetime],
        line_height: int,
        location_line_height: int,
        time_width: int = 40,
        chevron_width: int = 10,
        screen_margin: int = 3,
        location_display_time: int = 5,  # seconds to display each location
        workshop_update_interval: int = 30,  # seconds between workshop list updates
        future_time_limit: int = 24 * 60  # minutes (24 hours)
    ):
        """
        Initialize the workshop_runner.
        
        Args:
            graphic_interface: The graphic interface to render on
            workshop_font: Font to use for workshop names and times
            location_font: Font to use for location display
            get_current_datetime: Function that returns the current datetime
            line_height: Height of each workshop line
            location_line_height: Height of the location line
            time_width: Width in pixels for the time display
            chevron_width: Width in pixels for the chevron indicator
            location_display_time: Seconds to display each location before cycling
            workshop_update_interval: Seconds between workshop list updates
            future_time_limit: Maximum minutes in the future to display workshops
        """
        self.logger = Logger.get_logger()
        self.graphic_interface = graphic_interface
        self.workshop_font = workshop_font
        self.location_font = location_font
        self.get_current_datetime = get_current_datetime
        
        # Pixel dimensions
        self.line_height = line_height
        self.location_line_height = location_line_height
        self.time_width = time_width
        self.chevron_width = chevron_width
        self.screen_margin = screen_margin
        
        # Calculate how many workshops can fit on the screen
        self.total_height = graphic_interface.height
        self.available_height = self.total_height - self.location_line_height - (2 * self.screen_margin)
        self.max_workshops = self.available_height // self.line_height
        
        # Calculate available width for workshop names
        self.total_width = graphic_interface.width
        self.available_name_width = self.total_width - self.time_width - self.chevron_width - (2 * self.screen_margin)
        
        # Timing parameters
        self.location_display_time = location_display_time
        self.workshop_update_interval = workshop_update_interval
        self.future_time_limit = future_time_limit
        
        # State variables
        self.displayed_workshops: List[Workshop] = []
        self.current_location_index = 0
        self.last_location_change_time = time.time()
        self.last_workshop_update_time = 0
        
        # Colors - all red as requested
        self.text_color = Color(255, 0, 0)  # Red
        self.location_color = Color(255, 0, 0)  # Red
        self.chevron_color = Color(255, 0, 0)  # Red
        
        # Initialize workshop loader
        self.workshop_loader = workshop_loader(get_current_datetime)
        
        # Screen saver function (placeholder)
        self.screen_saver_fn = None
        
        self.logger.info("Initialized workshop_runner")
    
    def get_current_screen_saver(self) -> Callable[[Canvas], Canvas]:
        """
        Get a function that renders a screen saver animation.
        
        Returns:
            A function that takes a canvas and returns an updated canvas
        """
        # Simple bouncing text screen saver
        text = "No upcoming workshops"
        pos_x = 0
        pos_y = self.total_height // 2
        direction_x = 1
        direction_y = 1
        
        def screen_saver(canvas: Canvas) -> Canvas:
            nonlocal pos_x, pos_y, direction_x, direction_y
            
            canvas.Clear()
            
            # Draw the text
            self.graphic_interface.DrawText(
                canvas, self.workshop_font, pos_x, pos_y, self.text_color, text
            )
            
            # Update position
            pos_x += direction_x
            pos_y += direction_y
            
            # Bounce off edges
            if pos_x <= 0 or pos_x >= canvas.width - len(text) * 6:  # Approximate text width
                direction_x = -direction_x
            
            if pos_y <= self.workshop_font.height or pos_y >= canvas.height - 5:
                direction_y = -direction_y
            
            return canvas
        
        return screen_saver
    
    def may_update_workshops(self) -> bool:
        """
        Check if workshops need to be updated and update them if necessary.
        
        Returns:
            True if workshops were updated, False otherwise
        """
        current_time = time.time()
        
        # Check if enough time has passed since the last update
        if current_time - self.last_workshop_update_time < self.workshop_update_interval:
            return False
        
        self.last_workshop_update_time = current_time
        
        # Get all workshops
        all_workshops = self.workshop_loader.get_workshops()
        
        # Remove workshops that have already started
        self.displayed_workshops = [
            w for w in self.displayed_workshops 
            if w.minutes_until_workshop is not None and w.minutes_until_workshop > 0
        ]
        
        # Fill empty slots with upcoming workshops
        if len(self.displayed_workshops) < self.max_workshops:
            # Get upcoming workshops within the time limit
            upcoming = [
                w for w in all_workshops.get_upcoming_workshops() 
                if w.minutes_until_workshop is not None and w.minutes_until_workshop <= self.future_time_limit
            ]
            
            # Add workshops that aren't already displayed
            for workshop in upcoming:
                if workshop not in self.displayed_workshops and len(self.displayed_workshops) < self.max_workshops:
                    self.displayed_workshops.append(workshop)
        
        # Reset location index if we've removed the current workshop
        if self.current_location_index >= len(self.displayed_workshops) and self.displayed_workshops:
            self.current_location_index = 0
            self.last_location_change_time = current_time
        
        # Check if we need to activate screen saver
        if not self.displayed_workshops:
            if self.screen_saver_fn is None:
                self.logger.info("No upcoming workshops, activating screen saver")
                self.screen_saver_fn = self.get_current_screen_saver()
            return True
        else:
            self.screen_saver_fn = None
            return True
    
    def update_location_index(self) -> bool:
        """
        Update the index of the workshop whose location is being displayed.
        
        Returns:
            True if the index was updated, False otherwise
        """
        if not self.displayed_workshops:
            return False
        
        current_time = time.time()
        
        # Check if enough time has passed to change the location
        if current_time - self.last_location_change_time >= self.location_display_time:
            self.current_location_index = (self.current_location_index + 1) % len(self.displayed_workshops)
            self.last_location_change_time = current_time
            return True
        
        return False
    
    def format_time_until(self, minutes: Optional[float]) -> str:
        """
        Format the time until a workshop starts.
        
        Args:
            minutes: Minutes until the workshop starts
            
        Returns:
            Formatted time string in "T-XX" format, or "NOW" if started
        """
        if minutes is None:
            return "T-??"
        
        if minutes <= 0:
            return "NOW"
        
        return f"T-{int(minutes)}"
    
    def render_workshop_time(self, canvas: Canvas, x: int, y: int, workshop: Workshop) -> int:
        """
        Render the time until a workshop starts.
        
        Args:
            canvas: Canvas to render on
            x: X coordinate
            y: Y coordinate
            workshop: Workshop to render time for
            
        Returns:
            Width of the rendered text
        """
        time_text = self.format_time_until(workshop.minutes_until_workshop)
        return self.graphic_interface.DrawText(
            canvas, self.workshop_font, x, y, self.text_color, time_text
        )
    
    def calculate_text_width(self, font: Font, text: str) -> int:
        """
        Calculate the width of a text string in the given font.
        
        Args:
            font: Font to use for calculation
            text: Text to calculate width for
            
        Returns:
            Width of the text in pixels
        """
        width = 0
        for char in text:
            width += font.CharacterWidth(ord(char))
        return width
    
    def render_workshop_name(self, canvas: Canvas, x: int, y: int, workshop: Workshop, 
                            max_width: int, is_current: bool) -> int:
        """
        Render the name of a workshop.
        
        Args:
            canvas: Canvas to render on
            x: X coordinate
            y: Y coordinate
            workshop: Workshop to render name for
            max_width: Maximum width for the name
            is_current: Whether this workshop is currently showing its location
            
        Returns:
            Width of the rendered text
        """
        # Calculate available width for the name
        available_width = max_width - self.chevron_width
        
        # Calculate the total width of the workshop name
        name_width = self.calculate_text_width(self.workshop_font, workshop.title)
        
        # Determine if we need to scroll the text
        needs_scrolling = name_width > (available_width + 4)
        
        # Get current time for scrolling animation
        current_time = time.time()
        scroll_position = int((current_time * 30) % (name_width + available_width)) if needs_scrolling else 0
        
        # Render the workshop name with scrolling if needed
        if needs_scrolling:
            # Clip to available width
            self.graphic_interface.DrawText(
                canvas, self.workshop_font, x - scroll_position, y, self.text_color, workshop.title
            )
        else:
            # Render normally
            self.graphic_interface.DrawText(
                canvas, self.workshop_font, x, y, self.text_color, workshop.title
            )
        
        # Render chevron if this is the current workshop
        if is_current:
            chevron_x = x + available_width
            chevron_y = y
            
            # Draw a simple chevron (triangle) pointing inward
            self.graphic_interface.DrawLine(
                canvas, 
                chevron_x + 5, chevron_y - 3, 
                chevron_x, chevron_y, 
                self.chevron_color
            )
            self.graphic_interface.DrawLine(
                canvas, 
                chevron_x, chevron_y, 
                chevron_x + 5, chevron_y + 3, 
                self.chevron_color
            )
        
        return name_width
    
    def render_workshop(self, canvas: Canvas, pixel_offset: int, workshop: Workshop, is_current: bool) -> None:
        """
        Render a workshop line.
        
        Args:
            canvas: Canvas to render on
            pixel_offset: Y offset in pixels
            workshop: Workshop to render
            is_current: Whether this workshop is currently showing its location
        """
        # Apply screen margin
        y_position = pixel_offset + self.workshop_font.baseline + self.screen_margin
        
        # Render time
        time_width = self.render_workshop_time(
            canvas, self.screen_margin, y_position, workshop
        )
        
        # Render name
        name_x = self.screen_margin + self.time_width
        name_max_width = self.available_name_width
        
        self.render_workshop_name(
            canvas, name_x, y_position, 
            workshop, name_max_width, is_current
        )
    
    def render_location(self, canvas: Canvas) -> None:
        """
        Render the location of the currently selected workshop.
        
        Args:
            canvas: Canvas to render on
        """
        if not self.displayed_workshops or self.current_location_index >= len(self.displayed_workshops):
            return
        
        current_workshop = self.displayed_workshops[self.current_location_index]
        location_text = f"@ {current_workshop.location}" if current_workshop.location else "@ Unknown location"
        
        # Calculate y position for the location (at the bottom of the screen)
        y_pos = self.total_height - self.location_line_height + self.location_font.baseline
        
        # Render the location with screen margin
        self.graphic_interface.DrawText(
            canvas, self.location_font, self.screen_margin, y_pos, self.location_color, location_text
        )
    
    def render(self, canvas: Canvas) -> Canvas:
        """
        Render all workshops and the current location.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            Updated canvas
        """
        # Check if we need to update workshops
        self.may_update_workshops()
        
        # Update location index if needed
        self.update_location_index()
        
        # If we have no workshops to display, use screen saver
        if self.screen_saver_fn is not None:
            return self.screen_saver_fn(canvas)
        
        # Clear the canvas
        canvas.Clear()
        
        # Render each workshop
        for i, workshop in enumerate(self.displayed_workshops[:self.max_workshops]):
            is_current = (i == self.current_location_index)
            pixel_offset = i * self.line_height
            self.render_workshop(canvas, pixel_offset, workshop, is_current)
        
        # Render the current location
        self.render_location(canvas)
        
        return canvas
