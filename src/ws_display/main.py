import asyncio
import os
import platform
import sys
import time
import tkinter as tk
from typing import Optional, cast

from src.logging import Logger
from src.ws_display.Config import Config
from src.ws_display.config_loader import get_config
from src.ws_display.renderer.graphic_interface import GraphicInterface, Color

class MatrixApp:
    def __init__(self):
        self.logger = Logger.get_logger()
        self.config = get_config()
        self.graphic_interface = self._create_graphic_interface()
        self.running = False
        self.renderer_task = None
    
    def _create_graphic_interface(self) -> GraphicInterface:
        """
        Create the appropriate GraphicInterface based on the platform.
        """
        # Check if we're on a Raspberry Pi
        is_raspberry_pi = platform.machine().startswith('arm') and os.path.exists('/sys/firmware/devicetree/base/model')
        
        if is_raspberry_pi:
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
            except ImportError as e:
                self.logger.error(f"Failed to import PiGraphicInterface: {e}")
                self.logger.warning("Falling back to EmulatedGraphicInterface")
                is_raspberry_pi = False
        
        if not is_raspberry_pi:
            self.logger.info("Using EmulatedGraphicInterface")
            from src.ws_display.renderer.emulated_graphics_interface import EmulatedGraphicInterface
            
            # Calculate total dimensions
            width = self.config.panel_width * self.config.panel_count_x
            height = self.config.panel_height * self.config.panel_count_y
            
            return EmulatedGraphicInterface(
                width=width,
                height=height,
                config_brightness_override=self.config.brightness_override,
                scale=8  # Adjust scale as needed
            )
    
    async def run_renderer(self):
        """
        Run the renderer loop with a scrolling text demo.
        """
        self.logger.info("Starting renderer")
        self.running = True
        
        # Create a font
        font = self.graphic_interface.CreateFont()
        try:
            # Try to load the font from the fonts directory
            font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                    "fonts", "5x7.ttf")
            if not os.path.exists(font_path):
                # Try BDF font if TTF not found
                font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                        "fonts", "5x7.bdf")
            
            font.LoadFont(font_path)
            self.logger.info(f"Loaded font: {font_path}")
        except Exception as e:
            self.logger.error(f"Failed to load font: {e}")
            return
        
        # Create colors
        yellow = Color(255, 255, 0)
        red = Color(255, 0, 0)
        green = Color(0, 255, 0)
        blue = Color(0, 0, 255)
        
        # Create a canvas
        offscreen_canvas = self.graphic_interface.CreateFrameCanvas()
        
        # Text to display
        text = "---TEST WORKSHOP MATRIX DISPLAY---"
        pos = offscreen_canvas.width
        
        try:
            while self.running:
                # Clear the canvas
                offscreen_canvas.Clear()
                
                # Draw scrolling text
                length = self.graphic_interface.DrawText(offscreen_canvas, font, pos, 10, yellow, text)
                
                # Draw some shapes for testing
                self.graphic_interface.DrawCircle(offscreen_canvas, 16, 30, 10, red)
                self.graphic_interface.DrawLine(offscreen_canvas, 40, 30, 80, 30, green)
                self.graphic_interface.DrawLine(offscreen_canvas, 60, 20, 60, 40, blue)
                
                # Update position
                pos -= 1
                if pos + length < 0:
                    pos = offscreen_canvas.width
                
                # Swap canvas
                offscreen_canvas = self.graphic_interface.SwapOnVSync(offscreen_canvas)
                
                # Sleep to control frame rate
                await asyncio.sleep(0.05)
        except Exception as e:
            self.logger.error(f"Error in renderer loop: {e}")
        finally:
            self.logger.info("Renderer stopped")
            self.running = False
    
    def restart_renderer(self):
        """
        Restart the renderer (called when configuration changes).
        """
        self.logger.info("Restarting renderer")
        
        # Stop the current renderer
        self.running = False
        if self.renderer_task and not self.renderer_task.done():
            # Wait for the task to complete
            # In a real implementation, you might want to use asyncio.wait_for with a timeout
            pass
        
        # Create a new graphic interface with updated config
        self.graphic_interface = self._create_graphic_interface()
        
        # Start a new renderer task
        self.renderer_task = asyncio.create_task(self.run_renderer())
    
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
    root.withdraw()  # Hide the root window
    
    app = MatrixApp()
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
