import asyncio
import os
import platform
import sys
import tkinter as tk
from tkinter import ttk
from typing import Optional

from src.logging import Logger
from src.ws_display.Config import Config
from src.ws_display.config_loader import get_config
from src.ws_display.program_manager import program_manager
from src.ws_display.program_scheduler import program_scheduler
from src.ws_display.renderer.graphic_interface import GraphicInterface
from src.ws_display.time_keeper import time_keeper

class MatrixApp:
    def __init__(self):
        self.logger = Logger.get_logger()
        self.config = get_config()
        self.graphic_interface = self._create_graphic_interface()
        self.time_keeper = time_keeper()
        self.program_mgr = program_manager(self.graphic_interface, self.time_keeper)
        self.program_scheduler = program_scheduler(self.program_mgr, self.time_keeper)
        self.running = False
        self.renderer_task = None
    
    def _create_graphic_interface(self) -> GraphicInterface:
        """
        Create the appropriate GraphicInterface based on the platform.
        """
        # Check if we're on a Raspberry Pi
        self.is_raspberry_pi = platform.machine().startswith('arm') and os.path.exists('/sys/firmware/devicetree/base/model')
        
        if self.is_raspberry_pi:
            self.logger.info("Detected Raspberry Pi platform, using PiGraphicInterface")
            try:
                # Import here to avoid errors when not on a Pi
                from src.ws_display.renderer.pi_graphics_interface import PiGraphicInterface
                
                # Create matrix options
                matrix_options = {
                    'rows': self.config.panel_height,
                    'cols': self.config.panel_width,
                    'chain_length': self.config.panel_count_x,
                    'parallel': self.config.panel_count_y,
                    'hardware_mapping': 'adafruit-hat',  # Adjust as needed
                    'pwm_bits': 11,
                    'brightness': 100,
                    'scan_mode': self.config.scan_mode
                }
                
                return PiGraphicInterface(
                    config_brightness_override=self.config.brightness_override,
                    **matrix_options
                )
                self.is_raspberry_pi = True
            except ImportError as e:
                self.s_raspberry_pi = False
        
        if not self.is_raspberry_pi:
            self.logger.info("Using EmulatedGraphicInterface")
            from src.ws_display.renderer.emulated_graphics_interface import EmulatedGraphicInterface
            
            # Calculate total dimensions
            width = self.config.panel_width * self.config.panel_count_x
            height = self.config.panel_height * self.config.panel_count_y
            
            return EmulatedGraphicInterface(
                width=width,
                height=height,
                config_brightness_override=self.config.brightness_override,
                scale=6,  # Adjust scale as needed
                pixel_spacing=0.4,  # Spacing between pixels (0.0 - 1.0)
                use_circles=True  # Whether to render pixels as circles
            )
    
    # This method is no longer needed as font loading is handled by program_manager
        
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
    
    # Create a frame for controls
    control_frame = ttk.Frame(root, padding="10")
    control_frame.pack(fill=tk.X, expand=False, pady=10)
    
    app = MatrixApp()
    
    # Add a button
    def button_click():
        print("Button pressed!")
    
    test_button = ttk.Button(control_frame, text="Test Button", command=button_click)
    test_button.pack(side=tk.LEFT, padx=5)
    
    # Add a timescale slider
    timescale_frame = ttk.Frame(control_frame)
    timescale_frame.pack(side=tk.LEFT, padx=5)
    
    timescale_label = ttk.Label(timescale_frame, text="Time Scale: 1.0x")
    timescale_label.pack(side=tk.TOP)
    
    def timescale_change(value):
        timescale = float(value)
        app.time_keeper.set_timescale(timescale)
        timescale_label.config(text=f"Time Scale: {timescale:.1f}x")
        print(f"Time scale changed to: {timescale}")
    
    timescale_slider = ttk.Scale(timescale_frame, from_=1, to=100, orient=tk.HORIZONTAL, 
                           length=200, command=timescale_change)
    timescale_slider.pack(side=tk.BOTTOM)
    timescale_slider.set(1)  # Set initial value to 1
    try:
        # Set up a periodic task to update the Tkinter event loop
        async def update_tk():
            while True:
                root.update()
                await asyncio.sleep(0.01)
        
        # Start the update task
        update_task = asyncio.create_task(update_tk())
        
        # Run the main application
        await app.run()
    except Exception as e:
        Logger.get_logger().error(f"Application error: {e}")
    finally:
        # Clean up
        root.destroy()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print(f"Application error: {e}")
