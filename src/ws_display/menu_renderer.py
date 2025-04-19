from typing import List, Dict, Optional, Tuple
from src.ws_display.renderer.graphic_interface import GraphicInterface, Canvas, Font, Color
from src.ws_display.render_result import render_result

class MenuRendererConfig:
    """
    Configuration class for MenuRenderer.
    Contains all the rendering options.
    """
    def __init__(
        self,
        line_height: int,
        location_line_height: int,
        time_width: int = 40,
        chevron_width: int = 10,
        screen_margin: int = 3,
        time_block_margin: int = 2,
        scroll_speed: float = 10.0,
        min_current_time: float = 6.0,
        max_current_time: float = 12.0
    ):
        """
        Initialize the MenuRendererConfig.
        
        Args:
            line_height: Height of each menu item line
            location_line_height: Height of the description line
            time_width: Width in pixels for the value display
            chevron_width: Width in pixels for the chevron indicator
            screen_margin: Margin around the screen
            time_block_margin: Margin between value block and name area
            scroll_speed: Pixels per second for scrolling text
            min_current_time: Minimum time to display item as current (seconds)
            max_current_time: Maximum time to display item as current (seconds)
        """
        self.line_height = line_height
        self.location_line_height = location_line_height
        self.time_width = time_width
        self.chevron_width = chevron_width
        self.screen_margin = screen_margin
        self.time_block_margin = time_block_margin
        self.scroll_speed = scroll_speed
        self.min_current_time = min_current_time
        self.max_current_time = max_current_time


class MenuItem:
    """
    Class representing a menu item.
    """
    def __init__(
        self,
        value_text: str,
        name_text: str,
        description_text: str
    ):
        """
        Initialize a menu item.
        
        Args:
            value_text: The text to display in the value column
            name_text: The text to display in the name column
            description_text: The text to display in the description row when selected
        """
        self.value_text = value_text
        self.name_text = name_text
        self.description_text = description_text


class MenuRenderer:
    """
    Class responsible for rendering a menu of items on the display.
    """
    def __init__(
        self,
        graphic_interface: GraphicInterface,
        value_font: Font,
        name_font: Font,
        description_font: Font,
        config: MenuRendererConfig,
        get_current_time: callable
    ):
        """
        Initialize the MenuRenderer.
        
        Args:
            graphic_interface: The graphic interface to render on
            value_font: Font to use for value display
            name_font: Font to use for item names
            description_font: Font to use for description display
            config: Configuration for the renderer
            get_current_time: Function that returns the current time in seconds
        """
        self.graphic_interface = graphic_interface
        self.value_font = value_font
        self.name_font = name_font
        self.description_font = description_font
        self.config = config
        self.get_current_time = get_current_time
        
        # Pixel dimensions
        self.total_height = graphic_interface.height
        self.total_width = graphic_interface.width
        
        # Calculate how many items can fit on the screen
        self.available_height = self.total_height - self.config.location_line_height - (2 * self.config.screen_margin)
        self.max_items = self.available_height // self.config.line_height
        
        # Calculate available width for item names
        self.available_name_width = (self.total_width - self.config.time_width - self.config.chevron_width - 
                                    (2 * self.config.screen_margin) - self.config.time_block_margin)
        
        # Calculate column dimensions for external use
        self._time_column_width = self.config.screen_margin + self.config.time_width + self.config.time_block_margin
        self._chevron_column_width = self.config.chevron_width
        
        # State variables
        self.menu_items: List[MenuItem] = []
        self.active_item_index = 0
        self.last_active_change_time = self.get_current_time()
        
        # Scrolling state variables
        self.scroll_start_times: Dict[int, float] = {}  # Maps item index to scroll start time
        self.scroll_directions: Dict[int, int] = {}  # Maps item index to scroll direction (1 or -1)
        
        # Colors - all red as requested
        self.text_color = Color(255, 0, 0)  # Red
        self.description_color = Color(255, 0, 0)  # Red
        self.chevron_color = Color(255, 0, 0)  # Red
        self.background_color = Color(0, 0, 0)  # Black background
    
    def set_menu_items(self, items: List[MenuItem]) -> None:
        """
        Set the menu items to display.
        
        Args:
            items: List of menu items
        """
        self.menu_items = items
        if self.active_item_index >= len(items) and items:
            self.active_item_index = 0
            self.last_active_change_time = self.get_current_time()
    
    def set_active_item(self, index: int) -> None:
        """
        Set the active item by index.
        
        Args:
            index: Index of the item to set as active
        """
        if 0 <= index < len(self.menu_items):
            self.active_item_index = index
            self.last_active_change_time = self.get_current_time()
            # Initialize scroll state for the new active item
            self.scroll_start_times[index] = self.get_current_time()
            self.scroll_directions[index] = 1  # Start scrolling forward
    
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
    
    def calculate_time_width(self) -> int:
        """
        Calculate the fixed width of the value display area.
        
        Returns:
            Fixed width of the value display in pixels (3 characters wide + margin)
        """
        # Calculate width based on 3 characters (e.g., "999")
        three_char_width = self.calculate_text_width(self.value_font, "999")
        return three_char_width
    
    def render_value(self, canvas: Canvas, x: int, y: int, value_text: str) -> int:
        """
        Render the value text with a black background.
        
        Args:
            canvas: Canvas to render on
            x: X coordinate
            y: Y coordinate
            value_text: Value text to render
            
        Returns:
            Width of the rendered text
        """
        # Calculate the width of the value text
        value_width = self.calculate_text_width(self.value_font, value_text)
        
        # Draw a black background rectangle for the value that covers the full line height
        # and extends to the left edge of the screen and a bit into the name area
        for i in range(x + value_width + self.config.time_block_margin):
            for j in range(-self.value_font.height, self.config.line_height - self.value_font.baseline):
                self.graphic_interface.DrawLine(
                    canvas,
                    i, y + j,
                    i, y + j,
                    self.background_color
                )
        
        # Draw the value text on top of the black background
        return self.graphic_interface.DrawText(
            canvas, self.value_font, x, y, self.text_color, value_text
        )
    
    def render_name(self, canvas: Canvas, x: int, y: int, name_text: str, 
                   max_width: int, is_active: bool, item_index: int) -> int:
        """
        Render the name of a menu item.
        
        Args:
            canvas: Canvas to render on
            x: X coordinate
            y: Y coordinate
            name_text: Name text to render
            max_width: Maximum width for the name
            is_active: Whether this item is currently active
            item_index: Index of this item in the menu_items list
            
        Returns:
            Width of the rendered text
        """
        # Calculate available width for the name
        available_width = max_width
        
        # Calculate the total width of the item name
        name_width = self.calculate_text_width(self.name_font, name_text)
        
        # Determine if we need to scroll the text
        needs_scrolling = name_width > available_width
        
        # Default to static position for item names
        scroll_position = 0
        
        # Only scroll if this is the active item and it needs scrolling
        if is_active and needs_scrolling:
            # Get current time
            current_time = self.get_current_time()
            
            # Get or initialize the scroll start time
            if item_index not in self.scroll_start_times:
                self.scroll_start_times[item_index] = current_time
                self.scroll_directions[item_index] = 1  # Start with forward scrolling
            
            start_time = self.scroll_start_times[item_index]
            
            # Calculate elapsed time since the scroll started
            elapsed_time = current_time - start_time
            
            # Maximum scroll distance (when text is fully scrolled)
            max_scroll = name_width - available_width + 20  # Add a small buffer
            
            # Calculate time to reach max scroll at target speed
            time_to_max_scroll = max_scroll / self.config.scroll_speed
            
            # Time to reach the target speed (25% of total scroll time or 1 second, whichever is less)
            acceleration_time = min(time_to_max_scroll * 0.25, 1.0)
            
            direction = self.scroll_directions[item_index]
            
            # Check if minimum display time has elapsed
            item_display_time = current_time - self.last_active_change_time
            
            if elapsed_time <= acceleration_time:
                # Ease-in: Accelerate to target speed
                progress = elapsed_time / acceleration_time
                current_speed = self.config.scroll_speed * progress
                distance = elapsed_time * current_speed / 2  # Average speed over time
                scroll_position = direction * distance
            else:
                # Constant speed after acceleration
                # Distance covered during acceleration phase
                accel_distance = acceleration_time * self.config.scroll_speed / 2
                
                # Distance covered at constant speed
                constant_time = elapsed_time - acceleration_time
                constant_distance = constant_time * self.config.scroll_speed
                
                # Total distance
                distance = accel_distance + constant_distance
                
                # Check if we've reached the end of the scroll
                if distance >= max_scroll:
                    # If min display time hasn't elapsed, reverse direction
                    if item_display_time < self.config.min_current_time:
                        # Calculate how far past max_scroll we are
                        excess = distance - max_scroll
                        
                        # Reverse direction
                        if direction == 1:
                            self.scroll_directions[item_index] = -1
                            # Start scrolling from the end
                            self.scroll_start_times[item_index] = current_time
                            scroll_position = max_scroll
                        else:
                            # If already scrolling backward and reached start
                            if excess >= max_scroll:
                                self.scroll_directions[item_index] = 1
                                self.scroll_start_times[item_index] = current_time
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
        
        # Render the item name with scrolling if needed
        if needs_scrolling:
            # Clip to available width
            self.graphic_interface.DrawText(
                canvas, self.name_font, x - scroll_position, y, self.text_color, name_text
            )
        else:
            # Render normally
            self.graphic_interface.DrawText(
                canvas, self.name_font, x, y, self.text_color, name_text
            )
        
        return name_width
    
    def render_chevron(self, canvas: Canvas, x: int, y: int, is_active: bool) -> None:
        """
        Render a chevron indicator with a black background.
        
        Args:
            canvas: Canvas to render on
            x: X coordinate
            y: Y coordinate
            is_active: Whether to render the chevron
        """
        # Always draw the black background for the chevron column
        # extending to the right edge of the screen
        for i in range(x, canvas.width):
            for j in range(-self.name_font.height, self.config.line_height - self.name_font.baseline):
                self.graphic_interface.DrawLine(
                    canvas,
                    i, y + j,
                    i, y + j,
                    self.background_color
                )
        
        # Only draw the chevron if this is the active item
        if is_active:
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
    
    def render_menu_item(self, canvas: Canvas, pixel_offset: int, item: MenuItem, is_active: bool, item_index: int) -> None:
        """
        Render a menu item line.
        
        Args:
            canvas: Canvas to render on
            pixel_offset: Y offset in pixels
            item: MenuItem to render
            is_active: Whether this item is currently active
            item_index: Index of this item in the menu_items list
        """
        # Apply screen margin
        name_y_position = pixel_offset + self.name_font.baseline + self.config.screen_margin
        value_y_position = pixel_offset + self.value_font.baseline + self.config.screen_margin
        
        # Use fixed value width for positioning
        fixed_value_width = self.calculate_time_width()
        
        # Render name first (it goes in the middle)
        name_x = self.config.screen_margin + fixed_value_width + self.config.time_block_margin
        name_max_width = self.available_name_width
        
        self.render_name(
            canvas, name_x, name_y_position, 
            item.name_text, name_max_width, is_active, item_index
        )
        
        # Render chevron (it goes on the right)
        chevron_x = self.config.screen_margin + self.config.time_width + self.available_name_width
        self.render_chevron(canvas, chevron_x, name_y_position, is_active)
        
        # Render value last (it goes on the left, but renders on top of everything)
        self.render_value(
            canvas, self.config.screen_margin, value_y_position, item.value_text
        )
    
    def render_description(self, canvas: Canvas) -> None:
        """
        Render the description of the currently selected item.
        
        Args:
            canvas: Canvas to render on
        """
        if not self.menu_items or self.active_item_index >= len(self.menu_items):
            return
        
        active_item = self.menu_items[self.active_item_index]
        description_text = active_item.description_text
        
        # Calculate y position for the description (at the bottom of the screen)
        y_pos = self.total_height - self.config.location_line_height + self.description_font.baseline
        
        # Render the description with screen margin
        self.graphic_interface.DrawText(
            canvas, self.description_font, self.config.screen_margin, y_pos, self.description_color, description_text
        )
    
    def render(self, canvas: Canvas) -> render_result:
        """
        Render all menu items and the current description.
        
        Args:
            canvas: Canvas to render on
            
        Returns:
            render_result containing the updated canvas and a finished flag
        """
        # Clear the canvas
        canvas.Clear()
        
        # Render each menu item
        for i, item in enumerate(self.menu_items[:self.max_items]):
            is_active = (i == self.active_item_index)
            pixel_offset = i * self.config.line_height
            self.render_menu_item(canvas, pixel_offset, item, is_active, i)
        
        # Render the current description
        self.render_description(canvas)
        
        # Menu renderer never finishes on its own
        return render_result(canvas, False)
