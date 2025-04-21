#!/usr/bin/env python3
"""
Entry point for the Workshop Matrix Display application.
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# include the self compiled matrix library
sys.path.append('src/lib/rpi-rgb-led-matrix/bindings/python')

# Import and run the main application
from src.ws_display.main import main
import asyncio

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application stopped by user")

