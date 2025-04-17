import gradio as gr
import os
from typing import Callable, Optional

from src.logging import Logger
from src.ws_display.Config import Config

class WebUI:
    def __init__(self, config: Config, restart_callback: Optional[Callable] = None):
        """
        Initialize the Gradio web UI.
        
        Args:
            config: The configuration instance.
            restart_callback: Optional callback to restart the renderer when config changes.
        """
        self.config = config
        self.restart_callback = restart_callback
        self.logger = Logger.get_logger()
        self.app = None
    
    def _save_config(self, panel_width: int, panel_height: int, panel_count_x: int, 
                    panel_count_y: int, scan_mode: int, brightness_override: float) -> str:
        """
        Save the configuration and restart the renderer if needed.
        
        Returns:
            A message indicating the result.
        """
        # Update config
        self.config.panel_width = panel_width
        self.config.panel_height = panel_height
        self.config.panel_count_x = panel_count_x
        self.config.panel_count_y = panel_count_y
        self.config.scan_mode = scan_mode
        self.config.brightness_override = brightness_override
        
        # Save config
        try:
            from src.ws_display.config_loader import get_config
            get_config()  # This will save the config
            
            # Restart renderer if callback provided
            if self.restart_callback:
                self.restart_callback()
            
            return "Configuration saved successfully. Renderer restarted."
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return f"Error saving configuration: {e}"
    
    def create_app(self) -> gr.Blocks:
        """
        Create the Gradio app.
        
        Returns:
            The Gradio Blocks app.
        """
        with gr.Blocks(title="Workshop Matrix Display") as app:
            with gr.Tab("Configuration"):
                with gr.Group():
                    gr.Markdown("## Panel Configuration")
                    with gr.Row():
                        panel_width = gr.Number(value=self.config.panel_width, label="Panel Width (pixels)", 
                                              precision=0, minimum=1)
                        panel_height = gr.Number(value=self.config.panel_height, label="Panel Height (pixels)", 
                                               precision=0, minimum=1)
                    
                    with gr.Row():
                        panel_count_x = gr.Number(value=self.config.panel_count_x, label="Panel Count X", 
                                                precision=0, minimum=1)
                        panel_count_y = gr.Number(value=self.config.panel_count_y, label="Panel Count Y", 
                                                precision=0, minimum=1)
                    
                    scan_mode = gr.Number(value=self.config.scan_mode, label="Scan Mode (1, 2, 4, 8, 16, 32)", 
                                        precision=0, minimum=1)
                    
                    brightness_override = gr.Slider(value=self.config.brightness_override, 
                                                  label="Brightness Override", 
                                                  minimum=0.0, maximum=1.0, step=0.01)
                    
                    save_btn = gr.Button("Save Configuration")
                    result = gr.Textbox(label="Result")
                    
                    save_btn.click(
                        fn=self._save_config,
                        inputs=[panel_width, panel_height, panel_count_x, panel_count_y, 
                                scan_mode, brightness_override],
                        outputs=[result]
                    )
            
            with gr.Tab("Workshops"):
                gr.Markdown("## Workshop Management")
                gr.Markdown("Workshop management will be implemented in a future update.")
            
            with gr.Tab("Logs"):
                gr.Markdown("## System Logs")
                # TODO: Implement log viewing
        
        self.app = app
        return app
    
    def launch(self, **kwargs) -> None:
        """
        Launch the Gradio app.
        
        Args:
            **kwargs: Additional arguments to pass to gr.launch().
        """
        if self.app is None:
            self.app = self.create_app()
        
        self.app.launch(**kwargs)
