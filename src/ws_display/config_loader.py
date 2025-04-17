import os
import yaml
from typing import Optional

from src.constants import RUNTIME_ARTIFACTS_PATH
from src.logging import Logger
from src.ws_display.Config import Config

def get_config() -> Config:
    """
    Load configuration from YAML file or create a new configuration if the file doesn't exist.
    Calls SetDefaults() to ensure all values have sensible defaults if not specified.
    Saves the configuration back to the YAML file.
    """
    logger = Logger.get_logger()
    config_path = os.path.join(RUNTIME_ARTIFACTS_PATH, "config.yaml")
    
    # Try to load existing configuration
    config = None
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as file:
                config_dict = yaml.safe_load(file)
                if config_dict:
                    config = Config(**config_dict)
                    logger.info(f"Loaded configuration from {config_path}")
                else:
                    logger.warning(f"Configuration file {config_path} is empty, creating new configuration")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
    
    # Create new configuration if loading failed
    if config is None:
        config = Config()
        logger.info("Created new configuration")
    
    # Set defaults for any None values
    config.SetDefaults()
    
    # Save configuration back to file
    try:
        with open(config_path, 'w') as file:
            yaml.dump(vars(config), file)
            logger.info(f"Saved configuration to {config_path}")
    except Exception as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")
    
    return config
