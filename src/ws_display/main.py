import asyncio
import os
import sys
import tkinter as tk
from typing import Optional

from src.logging import Logger
from src.ws_display.Config import Config
from src.ws_display.config_loader import get_config
from src.ws_display.platform import Platform
from src.ws_display.program_manager import program_manager
from src.ws_display.program_scheduler import program_scheduler
from src.ws_display.renderer.graphic_interface import GraphicInterface
from src.ws_display.time_keeper import time_keeper
from src.ws_display.ui.led_matrix_ui import LedMatrixUI
from src.ws_display.input.user_input import UserInput

class MatrixApp:
    def __init__(self):
        self.logger = Logger.get_logger()
        self.config = get_config()
        
        # Create platform instance
        self.platform = Platform(get_config)
        
        # Get appropriate graphics library, UI, and user input for the platform
        self.graphic_interface = self.platform.get_graphics_library()
        self.ui = self.platform.get_ui()
        self.user_input = self.platform.get_user_input()
        
        # Create time keeper and program manager
        self.time_keeper = time_keeper()
        self.program_mgr = program_manager(self.graphic_interface, self.time_keeper)
        self.program_scheduler = program_scheduler(self.program_mgr, self.time_keeper)
        
        # Initialize user input
        self.setup_user_input()
        
        # Initialize state
        self.running = False
        self.renderer_task = None
    
    async def run_renderer(self):
        """
        Run the renderer loop using the program manager and scheduler.
        """
        self.logger.info("Starting renderer")
        self.running = True
        
        # Main rendering loop
        while self.running:
            # Run the active program and get the result
            result = self.program_mgr.run_program()
            
            # Let the scheduler decide if we need to switch programs
            self.program_scheduler.may_update_program(result)
            
            # Swap canvas
            canvas = self.graphic_interface.SwapOnVSync(result.canvas)
            
            # Sleep to control frame rate
            await asyncio.sleep(0.015)
    
    def setup_user_input(self):
        """
        Set up user input handlers.
        """
        # Initialize user input
        self.user_input.initialize()
        
        # Current brightness level (0.0 - 1.0)
        self.brightness = 1.0
        
        # Register up listener to increase brightness
        def on_up():
            self.brightness = min(1.0, self.brightness + 0.05)
            self.graphic_interface.set_brightness(self.brightness)
            return True  # Allow other listeners to be called
        
        # Register down listener to decrease brightness
        def on_down():
            self.brightness = max(0.1, self.brightness - 0.05)
            self.graphic_interface.set_brightness(self.brightness)
            return True  # Allow other listeners to be called
        
        # Register click listener (placeholder for now)
        def on_click():
            return True  # Allow other listeners to be called
        
        # Register the listeners
        self.user_input.registerUpListener(on_up)
        self.user_input.registerDownListener(on_down)
        self.user_input.registerClickListener(on_click)
    
    async def run(self):
        """
        Run the application.
        """
        # Start the renderer
        self.renderer_task = asyncio.create_task(self.run_renderer())
        
        # Keep the application running
        while True:
            await asyncio.sleep(1)

async def main():
    # Initialize Tkinter root window
    root = tk.Tk()
    root.title("Matrix Control Panel")
    
    app = MatrixApp()
    
    # Initialize UI
    app.ui.initialize(root)
    
    # Create control panel
    control_panel = app.ui.create_control_panel(root)
    
    # Add test button
    def button_click():
        print("Button pressed!")
    
    app.ui.add_button(control_panel, "Test Button", button_click)
    
    # Add timescale slider
    def timescale_change(value):
        app.time_keeper.set_timescale(value)
        print(f"Time scale changed to: {value}")
    
    app.ui.add_timescale_slider(control_panel, timescale_change, 1.0)
    
    try:
        # Set up a periodic task to update the UI
        async def update_ui():
            while True:
                app.ui.update()
                await asyncio.sleep(0.01)
        
        # Start the update task
        update_task = asyncio.create_task(update_ui())
        
        # Run the main application
        await app.run()
    except Exception as e:
        Logger.get_logger().error(f"Application error: {e}")
    finally:
        # Clean up
        app.ui.cleanup()
        app.user_input.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print(f"Application error: {e}")
