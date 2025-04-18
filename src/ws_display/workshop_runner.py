import time
from datetime import datetime, timedelta
from typing import List, Callable, Optional, Tuple, Dict

from src.logging import Logger
from src.ws_display.workshop_loader import workshop_loader, Workshop, Workshops
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Font, Color
from src.ws_display.program_runner import program_runner
from src.ws_display.render_result import render_result

class workshop_runner(program_runner):
    """
    Class responsible for rendering workshops on the display.
    """
    def __init__(
        self,
        graphic_interface: GraphicInterface,
        time_font: Font,
        name_font: Font,  # Separate font for workshop names
        location_font: Font,
        get_current_datetime: Callable[[], datetime],
        line_height: int,
        location_line_height: int,
        time_width: int = 40,
        chevron_width: int = 10,
        screen_margin: int = 3,
        time_block_margin: int = 2,  # margin between time block and name area
        location_display_time: int = 5,  # seconds to display each location
        workshop_update_interval: int = 30,  # seconds between workshop list updates
        future_time_limit: int = 24 * 60,  # minutes (24 hours)
        scroll_speed: float = 10.0,  # pixels per second for scrolling text
        min_current_time: float = 6.0,  # minimum time to display workshop as current (seconds)
        max_current_time: float = 12.0  # maximum time to display workshop as current (seconds)
    ):
        """
        Initialize the workshop_runner.
        
        Args:
            graphic_interface: The graphic interface to render on
            time_font: Font to use for time display
            name_font: Font to use for workshop names
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
        super().__init__(graphic_interface)
        self.logger = Logger.get_logger()
        self.time_font = time_font
        self.name_font = name_font
        self.location_font = location_font
        self.get_current_datetime = get_current_datetime
        
        # Pixel dimensions
        self.line_height = line_height
        self.location_line_height = location_line_height
        self.time_width = time_width
        self.chevron_width = chevron_width
        self.screen_margin = screen_margin
        self.time_block_margin = time_block_margin
        
        # Calculate how many workshops can fit on the screen
        self.total_height = graphic_interface.height
        self.available_height = self.total_height - self.location_line_height - (2 * self.screen_margin)
        self.max_workshops = self.available_height // self.line_height
        
        # Calculate available width for workshop names
        self.total_width = graphic_interface.width
        self.available_name_width = (self.total_width - self.time_width - self.chevron_width - 
                                    (2 * self.screen_margin) - self.time_block_margin)
        
        # Calculate column dimensions for external use
        self._time_column_width = self.screen_margin + self.time_width + self.time_block_margin
        self._chevron_column_width = self.chevron_width
        
        # Timing parameters
        self.location_display_time = location_display_time
        self.workshop_update_interval = workshop_update_interval
        self.future_time_limit = future_time_limit
        
        # State variables
        self.displayed_workshops: List[Workshop] = []
        self.current_location_index = 0
        self.last_location_change_time = time.time()
        self.last_workshop_update_time = 0
        
        # Scrolling state variables
        self.min_current_time = min_current_time
        self.max_current_time = max_current_time
        self.scroll_start_times: Dict[int, float] = {}  # Maps workshop index to scroll start time
        self.scroll_directions: Dict[int, int] = {}  # Maps workshop index to scroll direction (1 or -1)
        
        # Colors - all red as requested
        self.text_color = Color(255, 0, 0)  # Red
        self.location_color = Color(255, 0, 0)  # Red
        self.chevron_color = Color(255, 0, 0)  # Red
        self.background_color = Color(0, 0, 0)  # Black background
        
        # Scrolling configuration
        self.scroll_speed = scroll_speed  # pixels per second
        
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
                canvas, self.name_font, pos_x, pos_y, self.text_color, text
            )
            
            # Update position
            pos_x += direction_x
            pos_y += direction_y
            
            # Bounce off edges
            if pos_x <= 0 or pos_x >= canvas.width - len(text) * 6:  # Approximate text width
                direction_x = -direction_x
            
            if pos_y <= self.name_font.height or pos_y >= canvas.height - 5:
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
        current_index = self.current_location_index
        current_workshop = self.displayed_workshops[current_index]
        
        # Calculate how long this workshop has been displayed
        workshop_display_time = current_time - self.last_location_change_time
        
        # Check if we need to switch workshops
        should_switch = False
        
        # Get the width of the workshop name
        name_width = self.calculate_text_width(self.name_font, current_workshop.title)
        
        # Check if this workshop needs scrolling
        needs_scrolling = name_width > self.available_name_width
        
        if needs_scrolling:
            # Always switch after max time
            if workshop_display_time >= self.max_current_time:
                # Clear scrolling state for this workshop
                self.scroll_start_times.pop(current_index, None)
                self.scroll_directions.pop(current_index, None)
                should_switch = True
        else:
            # For non-scrolling workshops, use standard display time
            if workshop_display_time >= self.location_display_time:
                should_switch = True
        
        # Switch to next workshop if needed
        if should_switch:
            self.current_location_index = (self.current_location_index + 1) % len(self.displayed_workshops)
            self.last_location_change_time = current_time
            # Initialize scroll state for the new workshop
            new_index = self.current_location_index
            self.scroll_start_times[new_index] = current_time
            self.scroll_directions[new_index] = 1  # Start scrolling forward
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
            return "??"
        
        if minutes <= 0:
            return "NOW"
        
        return f"{int(minutes)}"
    
    def render_workshop_time(self, canvas: Canvas, x: int, y: int, workshop: Workshop) -> int:
        """
        Render the time until a workshop starts with a black background.
        
        Args:
            canvas: Canvas to render on
            x: X coordinate
            y: Y coordinate
            workshop: Workshop to render time for
            
        Returns:
            Width of the rendered text
        """
        time_text = self.format_time_until(workshop.minutes_until_workshop)
        
        # Calculate the width of the time text
        time_width = self.calculate_text_width(self.time_font, time_text)
        
        # Draw a black background rectangle for the time that covers the full line height
        # and extends to the left edge of the screen and a bit into the name area
        for i in range(x + time_width + self.time_block_margin):
            for j in range(-self.time_font.height, self.line_height - self.time_font.baseline):
                self.graphic_interface.DrawLine(
                    canvas,
                    i, y + j,
                    i, y + j,
                    self.background_color
                )
        
        # Draw the time text on top of the black background
        return self.graphic_interface.DrawText(
            canvas, self.time_font, x, y, self.text_color, time_text
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
                            max_width: int, is_current: bool, workshop_index: int) -> int:
        """
        Render the name of a workshop.
        
        Args:
            canvas: Canvas to render on
            x: X coordinate
            y: Y coordinate
            workshop: Workshop to render name for
            max_width: Maximum width for the name
            is_current: Whether this workshop is currently showing its location
            workshop_index: Index of this workshop in the displayed_workshops list
            
        Returns:
            Width of the rendered text
        """
        # Calculate available width for the name
        available_width = max_width
        
        # Calculate the total width of the workshop name
        name_width = self.calculate_text_width(self.name_font, workshop.title)
        
        # Determine if we need to scroll the text
        needs_scrolling = name_width > available_width
        
        # Default to static position for workshop names
        scroll_position = 0
        
        # Only scroll if this is the current workshop and it needs scrolling
        if is_current and needs_scrolling:
            # Get current time
            current_time = time.time()
            
            # Get or initialize the scroll start time
            if workshop_index not in self.scroll_start_times:
                self.scroll_start_times[workshop_index] = current_time
                self.scroll_directions[workshop_index] = 1  # Start with forward scrolling
            
            start_time = self.scroll_start_times[workshop_index]
            
            # Calculate elapsed time since the scroll started
            elapsed_time = current_time - start_time
            
            # Maximum scroll distance (when text is fully scrolled)
            max_scroll = name_width - available_width + 20  # Add a small buffer
            
            # Calculate time to reach max scroll at target speed
            time_to_max_scroll = max_scroll / self.scroll_speed
            
            # Time to reach the target speed (25% of total scroll time or 1 second, whichever is less)
            acceleration_time = min(time_to_max_scroll * 0.25, 1.0)
            
            direction = self.scroll_directions[workshop_index]
            
            # Check if minimum display time has elapsed
            workshop_display_time = current_time - self.last_location_change_time
            
            if elapsed_time <= acceleration_time:
                # Ease-in: Accelerate to target speed
                progress = elapsed_time / acceleration_time
                current_speed = self.scroll_speed * progress
                distance = elapsed_time * current_speed / 2  # Average speed over time
                scroll_position = direction * distance
            else:
                # Constant speed after acceleration
                # Distance covered during acceleration phase
                accel_distance = acceleration_time * self.scroll_speed / 2
                
                # Distance covered at constant speed
                constant_time = elapsed_time - acceleration_time
                constant_distance = constant_time * self.scroll_speed
                
                # Total distance
                distance = accel_distance + constant_distance
                
                # Check if we've reached the end of the scroll
                if distance >= max_scroll:
                    # If min display time hasn't elapsed, reverse direction
                    if workshop_display_time < self.min_current_time:
                        # Calculate how far past max_scroll we are
                        excess = distance - max_scroll
                        
                        # Reverse direction
                        if direction == 1:
                            self.scroll_directions[workshop_index] = -1
                            # Start scrolling from the end
                            self.scroll_start_times[workshop_index] = current_time
                            scroll_position = max_scroll
                        else:
                            # If already scrolling backward and reached start
                            if excess >= max_scroll:
                                self.scroll_directions[workshop_index] = 1
                                self.scroll_start_times[workshop_index] = current_time
                                scroll_position = 0
                            else:
                                # Continue scrolling backward
                                scroll_position = max_scroll - excess
                    else:
                        # Min display time elapsed, cap at max_scroll
                        scroll_position = max_scroll
                else:
                    # Normal scrolling within bounds
                    scroll_position = direction * distance
            
            # Ensure scroll position is always positive when going forward
            if direction == 1:
                scroll_position = max(0, min(scroll_position, max_scroll))
            else:
                # When going backward, we want to go from max_scroll to 0
                scroll_position = max(0, min(max_scroll - scroll_position, max_scroll))
        else:
            scroll_position = 0
        
        # Render the workshop name with scrolling if needed
        if needs_scrolling:
            # Clip to available width
            self.graphic_interface.DrawText(
                canvas, self.name_font, x - scroll_position, y, self.text_color, workshop.title
            )
        else:
            # Render normally
            self.graphic_interface.DrawText(
                canvas, self.name_font, x, y, self.text_color, workshop.title
            )
        
        return name_width
    
    @property
    def time_column_width(self) -> int:
        """
        Get the width of the time column (from left edge of the screen to the end of the time column's black rectangle).
        
        Returns:
            Width of the time column in pixels
        """
        return self._time_column_width
    
    @property
    def chevron_column_width(self) -> int:
        """
        Get the width of the chevron column (from start of the chevron column to the right edge of the screen).
        
        Returns:
            Width of the chevron column in pixels
        """
        return self._chevron_column_width
    
    def render_chevron(self, canvas: Canvas, x: int, y: int, is_current: bool) -> None:
        """
        Render a chevron indicator with a black background.
        
        Args:
            canvas: Canvas to render on
            x: X coordinate
            y: Y coordinate
            is_current: Whether to render the chevron
        """
        # Always draw the black background for the chevron column
        # extending to the right edge of the screen
        for i in range(x, canvas.width):
            for j in range(-self.name_font.height, self.line_height - self.name_font.baseline):
                self.graphic_interface.DrawLine(
                    canvas,
                    i, y + j,
                    i, y + j,
                    self.background_color
                )
        
        # Only draw the chevron if this is the current workshop
        if is_current:
            try:
                # Try to load the chevron image
                chevron_img = self.graphic_interface.LoadImage("chevron")
                
                # Calculate center position
                chevron_x = x + 5
                chevron_y = y
                
                # Render the chevron image with tinting in the chevron color
                self.graphic_interface.RenderImage(
                    canvas, 
                    chevron_img, 
                    chevron_x, 
                    chevron_y, 
                    origin="left-mid", 
                    tint=self.chevron_color
                )
            except FileNotFoundError:
                # If image loading fails, fall back to pixel-based chevron
                self.logger.warning("Chevron image not found, using pixel-based fallback")
                
                # Calculate center of chevron area
                chevron_x = x + 2
                chevron_y = y
                
                # Draw a filled triangular chevron with SetPixel
                # Base height of the triangle
                height = 7
                
                # Draw the filled triangle
                for i in range(4):
                    for j in range(i+1):
                        # Left side of triangle
                        canvas.SetPixel(
                            chevron_x + i, 
                            chevron_y - j, 
                            self.chevron_color
                        )
                        # Right side of triangle (skip corner pixels for rounding)
                        if not (i == 0 and j == 0) and not (i == 3 and j == 3):
                            canvas.SetPixel(
                                chevron_x + i, 
                                chevron_y + j, 
                                self.chevron_color
                            )
                
                # Add two more pixels on the right side to complete the triangle
                for j in range(3):
                    canvas.SetPixel(
                        chevron_x + 4, 
                        chevron_y - j, 
                        self.chevron_color
                    )
                    canvas.SetPixel(
                        chevron_x + 4, 
                        chevron_y + j, 
                        self.chevron_color
                    )
    
    def calculate_time_width(self) -> int:
        """
        Calculate the fixed width of the time display area.
        
        Returns:
            Fixed width of the time display in pixels (3 characters wide + margin)
        """
        # Calculate width based on 3 characters (e.g., "999")
        three_char_width = self.calculate_text_width(self.time_font, "999")
        return three_char_width
    
    def render_workshop(self, canvas: Canvas, pixel_offset: int, workshop: Workshop, is_current: bool, workshop_index: int) -> None:
        """
        Render a workshop line.
        
        Args:
            canvas: Canvas to render on
            pixel_offset: Y offset in pixels
            workshop: Workshop to render
            is_current: Whether this workshop is currently showing its location
        """
        # Apply screen margin
        name_y_position = pixel_offset + self.name_font.baseline + self.screen_margin
        time_y_position = pixel_offset + self.time_font.baseline + self.screen_margin
        
        # Use fixed time width for positioning
        fixed_time_width = self.calculate_time_width()
        
        # Render name first (it goes in the middle)
        name_x = self.screen_margin + fixed_time_width + self.time_block_margin
        name_max_width = self.available_name_width
        
        self.render_workshop_name(
            canvas, name_x, name_y_position, 
            workshop, name_max_width, is_current, workshop_index
        )
        
        # Render chevron (it goes on the right)
        chevron_x = self.screen_margin + self.time_width + self.available_name_width
        self.render_chevron(canvas, chevron_x, name_y_position, is_current)
        
        # Render time last (it goes on the left, but renders on top of everything)
        self.render_workshop_time(
            canvas, self.screen_margin, time_y_position, workshop
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
    
    def render(self, canvas: Canvas) -> render_result:
        """
        Render all workshops and the current location.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            render_result containing the updated canvas and a finished flag
        """
        # Check if we need to update workshops
        self.may_update_workshops()
        
        # Update location index if needed
        self.update_location_index()
        
        # If we have no workshops to display, use screen saver
        if self.screen_saver_fn is not None:
            updated_canvas = self.screen_saver_fn(canvas)
            return render_result(updated_canvas, False)  # Screen saver never finishes
        
        # Clear the canvas
        canvas.Clear()
        
        # Render each workshop
        for i, workshop in enumerate(self.displayed_workshops[:self.max_workshops]):
            is_current = (i == self.current_location_index)
            pixel_offset = i * self.line_height
            self.render_workshop(canvas, pixel_offset, workshop, is_current, i)
        
        # Render the current location
        self.render_location(canvas)
        
        # Workshop runner never finishes on its own
        return render_result(canvas, False)
