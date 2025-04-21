from datetime import datetime, timedelta
from typing import List, Callable, Optional, Tuple, Dict

from src.logging import Logger
from src.ws_display.time_keeper import time_keeper
from src.ws_display.workshop_loader import workshop_loader, Workshop, Workshops
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Font, Color
from src.ws_display.program_runner import program_runner
from src.ws_display.render_result import render_result
from src.ws_display.menu_renderer import MenuRenderer, MenuRendererConfig, MenuItem

class workshop_runner(program_runner):
    """
    Class responsible for rendering workshops on the display.
    """
    def is_screen_saver(self) -> bool:
        """
        Workshop runner is not a screensaver, it's the main display.
        
        Returns:
            False as this is not a screensaver
        """
        return False
        
    def get_play_duration_seconds(self) -> Optional[float]:
        """
        Get the duration in seconds that this program should play before switching to another program.
        
        Returns:
            None as the workshop runner should run indefinitely until interrupted
        """
        return None
        
    def __init__(self, graphic_interface: GraphicInterface, time_keeper_instance: time_keeper):
        """
        Initialize the workshop_runner.
        
        Args:
            graphic_interface: The graphic interface to render on
            time_keeper_instance: Time keeper instance for time-related operations
        """
        super().__init__(graphic_interface)
        self.logger = Logger.get_logger()
        
        # Store time keeper instance
        self.time_keeper = time_keeper_instance
        self.get_current_datetime = self.time_keeper.now
        
        # Load fonts
        self.time_font = self._load_font(graphic_interface, "emil")
        self.name_font = self._load_font(graphic_interface, "emil")
        self.location_font = self._load_font(graphic_interface, "emil")
        
        # Set constant values
        line_height = 15
        location_line_height = 15
        time_width = 40
        chevron_width = 10
        screen_margin = 3
        time_block_margin = 2  # margin between time block and name area
        scroll_speed = 5.0  # pixels per second for scrolling text
        min_current_time = 6.0  # minimum time to display workshop as current (seconds)
        max_current_time = 12.0  # maximum time to display workshop as current (seconds)
        
        # Create menu renderer configuration
        self.menu_renderer_config = MenuRendererConfig(
            line_height=line_height,
            location_line_height=location_line_height,
            time_width=time_width,
            chevron_width=chevron_width,
            screen_margin=screen_margin,
            time_block_margin=time_block_margin,
            scroll_speed=scroll_speed,
            min_current_time=min_current_time,
            max_current_time=max_current_time
        )
        
        # Create menu renderer
        self.menu_renderer = MenuRenderer(
            graphic_interface=graphic_interface,
            value_font=self.time_font,
            name_font=self.name_font,
            description_font=self.location_font,
            config=self.menu_renderer_config,
            get_current_time=self.time_keeper.time
        )
        
        # Store some config values for later use
        self.line_height = line_height
        self.location_line_height = location_line_height
        self.total_height = graphic_interface.height
        self.total_width = graphic_interface.width
        self.max_workshops = self.menu_renderer.max_items
        
        # Timing parameters
        self.location_display_time = 5  # seconds to display each location
        self.workshop_update_interval = 30  # seconds between workshop list updates
        self.future_time_limit = 24 * 60  # minutes (24 hours)
        
        # State variables
        self.displayed_workshops: List[Workshop] = []
        self.current_location_index = 0
        self.last_location_change_time = self.time_keeper.time()
        self.last_workshop_update_time = 0
        
        # Initialize workshop loader
        self.workshop_loader = workshop_loader(self.time_keeper)
        
        # Screen saver function (placeholder)
        self.screen_saver_fn = None
        
        self.logger.info("Initialized workshop_runner")
    
    def _load_font(self, graphic_interface: GraphicInterface, font_name: str, font_size: int = 16) -> Font:
        """
        Load a font from the fonts directory.
        
        Args:
            graphic_interface: The graphic interface to use for font creation
            font_name: Name of the font file without extension
            font_size: Font size (only used for emulated graphics interface)
            
        Returns:
            Loaded font or None if loading failed
        """
        import os
        
        font = graphic_interface.CreateFont()
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Create the font path with .ttf extension (will be converted to .bdf if needed by PiFont)
            font_path = os.path.join(project_root, "fonts", font_name + ".ttf")
            
            font.LoadFont(font_path)
            self.logger.info(f"Loaded font: {font_path}")
            return font
        except Exception as e:
            self.logger.error(f"Failed to load font: {e}")
            return None
    
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
                canvas, self.name_font, pos_x, pos_y, self.menu_renderer.text_color, text
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
        current_time = self.time_keeper.time()
        
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
            # Update the menu items in the menu renderer
            self.update_menu_items()
            return True
    
    def update_location_index(self) -> bool:
        """
        Update the index of the workshop whose location is being displayed.
        
        Returns:
            True if the index was updated, False otherwise
        """
        if not self.displayed_workshops:
            return False
        
        current_time = self.time_keeper.time()
        current_index = self.current_location_index
        current_workshop = self.displayed_workshops[current_index]
        
        # Calculate how long this workshop has been displayed
        workshop_display_time = current_time - self.last_location_change_time
        
        # Check if we need to switch workshops
        should_switch = False
        
        # Get the width of the workshop name
        name_width = self.menu_renderer.calculate_text_width(self.name_font, current_workshop.title)
        
        # Check if this workshop needs scrolling
        needs_scrolling = name_width > self.menu_renderer.available_name_width
        
        if needs_scrolling:
            # Always switch after max time
            if workshop_display_time >= self.menu_renderer_config.max_current_time:
                should_switch = True
        else:
            # For non-scrolling workshops, use standard display time
            if workshop_display_time >= self.location_display_time:
                should_switch = True
        
        # Switch to next workshop if needed
        if should_switch:
            self.current_location_index = (self.current_location_index + 1) % len(self.displayed_workshops)
            self.last_location_change_time = current_time
            # Update the active item in the menu renderer
            self.menu_renderer.set_active_item(self.current_location_index)
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
    
    def update_menu_items(self) -> None:
        """
        Update the menu items in the menu renderer based on the current workshops.
        """
        menu_items = []
        
        for workshop in self.displayed_workshops:
            # Create a menu item for each workshop
            value_text = self.format_time_until(workshop.minutes_until_workshop)
            name_text = workshop.title
            description_text = f"@ {workshop.location}" if workshop.location else "@ Unknown location"
            
            menu_item = MenuItem(
                value_text=value_text,
                name_text=name_text,
                description_text=description_text
            )
            
            menu_items.append(menu_item)
        
        # Update the menu items in the menu renderer
        self.menu_renderer.set_menu_items(menu_items)
        
        # Set the active item to the current location index
        if menu_items and self.current_location_index < len(menu_items):
            self.menu_renderer.set_active_item(self.current_location_index)
    
    @property
    def time_column_width(self) -> int:
        """
        Get the width of the time column (from left edge of the screen to the end of the time column's black rectangle).
        
        Returns:
            Width of the time column in pixels
        """
        return self.menu_renderer.time_column_width
    
    @property
    def chevron_column_width(self) -> int:
        """
        Get the width of the chevron column (from start of the chevron column to the right edge of the screen).
        
        Returns:
            Width of the chevron column in pixels
        """
        return self.menu_renderer.chevron_column_width
    
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
        
        # Use the menu renderer to render the menu
        return self.menu_renderer.render(canvas)
