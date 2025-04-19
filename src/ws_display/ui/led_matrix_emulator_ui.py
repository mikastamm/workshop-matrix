import asyncio
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any

from src.logging import Logger
from src.ws_display.ui.led_matrix_ui import LedMatrixUI

class LedMatrixEmulatorUI(LedMatrixUI):
    """
    UI implementation for desktop platforms.
    Provides a Tkinter-based UI for controlling the LED matrix emulator.
    """
    
    def __init__(self):
        """
        Initialize the LedMatrixEmulatorUI.
        """
        self.logger = Logger.get_logger()
        self.root = None
        self.control_panels: Dict[tk.Widget, Any] = {}
        self.widgets: Dict[str, Any] = {}
        self.update_task = None
    
    def initialize(self, root_window: Optional[Any] = None) -> None:
        """
        Initialize the UI.
        
        Args:
            root_window: Optional Tkinter root window
        """
        if root_window is None:
            self.root = tk.Tk()
            self.root.title("Matrix Control Panel")
        else:
            self.root = root_window
        
        self.logger.info("Initialized LED Matrix Emulator UI")
    
    def create_control_panel(self, parent: Any) -> Any:
        """
        Create a control panel with UI elements.
        
        Args:
            parent: Parent widget
            
        Returns:
            The created control panel widget
        """
        control_frame = ttk.Frame(parent, padding="10")
        control_frame.pack(fill=tk.X, expand=False, pady=10)
        
        self.control_panels[parent] = control_frame
        return control_frame
    
    def add_button(self, parent: Any, text: str, command: Callable) -> None:
        """
        Add a button to the UI.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Function to call when the button is clicked
        """
        button = ttk.Button(parent, text=text, command=command)
        button.pack(side=tk.LEFT, padx=5)
        
        # Store the button for later reference
        self.widgets[f"button_{text}"] = button
    
    def add_timescale_slider(self, parent: Any, 
                            on_change: Callable[[float], None], 
                            initial_value: float = 1.0) -> None:
        """
        Add a timescale slider to the UI.
        
        Args:
            parent: Parent widget
            on_change: Function to call when the slider value changes
            initial_value: Initial slider value
        """
        timescale_frame = ttk.Frame(parent)
        timescale_frame.pack(side=tk.LEFT, padx=5)
        
        timescale_label = ttk.Label(timescale_frame, text=f"Time Scale: {initial_value:.1f}x")
        timescale_label.pack(side=tk.TOP)
        
        def timescale_change(value):
            timescale = float(value)
            on_change(timescale)
            timescale_label.config(text=f"Time Scale: {timescale:.1f}x")
        
        timescale_slider = ttk.Scale(timescale_frame, from_=1, to=100, orient=tk.HORIZONTAL, 
                               length=200, command=timescale_change)
        timescale_slider.pack(side=tk.BOTTOM)
        timescale_slider.set(initial_value)
        
        # Store the slider and label for later reference
        self.widgets["timescale_slider"] = timescale_slider
        self.widgets["timescale_label"] = timescale_label
    
    def update(self) -> None:
        """
        Update the UI. This method should be called periodically to process UI events.
        """
        if self.root:
            self.root.update()
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the UI.
        """
        if self.update_task:
            self.update_task.cancel()
            self.update_task = None
            
        if self.root:
            self.root.destroy()
            self.root = None
    
    def run_ui(self, app: Any) -> None:
        """
        Run the UI with the given application.
        This method handles Tkinter-specific UI initialization and setup.
        
        Args:
            app: The application instance to run with the UI
        """
        # Initialize UI
        self.initialize()
        
        # Create control panel
        control_panel = self.create_control_panel(self.root)
        
        # Add test button
        def button_click():
            print("Button pressed!")
        
        self.add_button(control_panel, "Test Button", button_click)
        
        # Add timescale slider
        def timescale_change(value):
            app.time_keeper.set_timescale(value)
            print(f"Time scale changed to: {value}")
        
        self.add_timescale_slider(control_panel, timescale_change, 1.0)
        
        # Set up a periodic task to update the UI
        async def update_ui():
            while True:
                self.update()
                await asyncio.sleep(0.01)
        
        # Start the update task
        self.update_task = asyncio.create_task(update_ui())
