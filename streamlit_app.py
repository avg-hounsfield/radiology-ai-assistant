#!/usr/bin/env python3
"""
ECHO Radiology Assistant - Streamlit Cloud Entry Point
Main application for deployment to Streamlit Community Cloud
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run the main ECHO application
from ui.echo_unified_system import main

if __name__ == "__main__":
    main()