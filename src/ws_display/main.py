import asyncio
import os
import platform
import sys
import time
import tkinter as tk
from typing import Optional, cast, List

from src.logging import Logger
from src.ws_display.Config import Config
from src.ws_display.config_loader import get_config
from src.ws_display.renderer.graphic_interface import Font, GraphicInterface, Color
from src.ws_display.program_runner import program_runner
from src.ws_display.workshop_runner import workshop_runner
from src.ws_display.screensavers.gnome_message_runner import gnome_message_runner
from src.ws_display.screensavers.eye_program_runner import eye_program_runner
from src.ws_display.screensavers.teeth_program_runner import teeth_program_runner
from src.ws_display.screensavers.care_bear_program_runner import care_bear_program_runner
from src.ws_display.render_result import render_result
from src.ws_display.renderer.emulated_graphics_interface import EmulatedFont

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
    
    # Font size only for testing and only for emulated graphics interface
    def load_font(self, font_name: str, font_size=16) -> Optional[Font]: 
        font = self.graphic_interface.CreateFont()
        try:
            # Try to load the font from the fonts directory
            if not self.is_raspberry_pi:
                font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                        "fonts", font_name+".ttf")
            else:
                font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                        "fonts", font_name+".bdf")
            
            font.LoadFont(font_path)
            if isinstance(font, EmulatedFont):
                font._font_size = font_size  # Set font size for emulated graphics interface
            self.logger.info(f"Loaded font: {font_path}")
            return font
        except Exception as e:
            self.logger.error(f"Failed to load font: {e}")
            return
        
    async def run_renderer(self):
        """
        Run the renderer loop with workshop display.
        """
        self.logger.info("Starting renderer")
        self.running = True
        
        # Create fonts - using different fonts for time and name
        time_font = self.load_font("emil")
        name_font = self.load_font("emil")  # Different font for workshop names
        location_font = self.load_font("emil")
        
        # Create a canvas
        offscreen_canvas = self.graphic_interface.CreateFrameCanvas()
        
        # Lambda to get current datetime
        from datetime import datetime
        get_current_datetime = lambda: datetime.now()
        
        # Configure workshop runner
        line_height = 15  # Height for each workshop line
        location_line_height = 15  # Height for the location line at the bottom
        
        # Create program runners
        programs: List[program_runner] = []
        
      
        
        # Add eye program runner
        eye = eye_program_runner(
            graphic_interface=self.graphic_interface,
            target_width=80,  # Scale eye images to reasonable size
            target_height=80,  # Scale eye images to reasonable size
        )

          # Add workshop runner
        workshop = workshop_runner(
            graphic_interface=self.graphic_interface,
            time_font=time_font,
            name_font=name_font,
            location_font=location_font,
            get_current_datetime=get_current_datetime,
            line_height=line_height,
            location_line_height=location_line_height,
            screen_margin=3,  # Add screen margin as requested
            time_block_margin=2,  # Margin between time block and workshop name
            scroll_speed=5.0,  # Slower scrolling speed (pixels per second)
            min_current_time=6.0,  # Minimum time to display a workshop as current (seconds)
            max_current_time=12.0  # Maximum time to display a workshop as current (seconds)
        )
                # Add gnome message runner
        gnome = gnome_message_runner(
            graphic_interface=self.graphic_interface,
            message_font=name_font,
        )
        
        # Add teeth program runner
        teeth = teeth_program_runner(
            graphic_interface=self.graphic_interface,
        )
        
        # Add care bears program runner
        care_bears = care_bear_program_runner(
            graphic_interface=self.graphic_interface,
        )
        
        programs.append(care_bears)
        programs.append(teeth)
        programs.append(eye)
        programs.append(workshop)
        programs.append(gnome)
        
        # Program switching state
        current_program_index = 0
        last_program_switch_time = time.time()
        program_switch_interval = 30.0  # Switch programs every 10 seconds
        
        while self.running:
            # Get the current program runner
            current_program = programs[current_program_index]
            
            # Render using the current program runner
            result = current_program.render(offscreen_canvas)
            
            # Check if the program has finished
            if result.finished:
                self.logger.info(f"Program {current_program_index} finished, switching to next program")
                current_program_index = (current_program_index + 1) % len(programs)
                last_program_switch_time = time.time()
            else:
                # Check if we need to switch programs based on time
                current_time = time.time()
                if current_time - last_program_switch_time >= program_switch_interval:
                    current_program_index = (current_program_index + 1) % len(programs)
                    last_program_switch_time = current_time
                    self.logger.info(f"Switching to program {current_program_index}")
            
            # Swap canvas
            offscreen_canvas = self.graphic_interface.SwapOnVSync(result.canvas)
            
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
