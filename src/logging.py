import logging
import os
import sys
from typing import Optional

class Logger:
    _logger: Optional[logging.Logger] = None
    
    @staticmethod
    def get_logger() -> logging.Logger:
        """
        Get or create a logger instance with consistent configuration.
        """
        if Logger._logger is None:
            # Create logger
            logger = logging.getLogger("ws_display")
            logger.setLevel(logging.INFO)
            
            # Create console handler and set level
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(console_handler)
            
            Logger._logger = logger
        
        return Logger._logger
