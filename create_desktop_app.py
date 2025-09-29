#!/usr/bin/env python3
"""
Create a desktop app version of ECHO using webview
Install with: pip install pywebview
"""

import webview
import threading
import time
import subprocess
import sys
import os
from pathlib import Path

class ECHODesktopApp:
    def __init__(self):
        self.streamlit_process = None
        self.port = 8501
        
    def start_streamlit(self):
        """Start Streamlit server in background"""
        try:
            # Change to project directory
            project_dir = Path(__file__).parent
            os.chdir(project_dir)
            
            # Start Streamlit
            self.streamlit_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run",
                "src/ui/simple_radiology_app.py",
                "--server.port", str(self.port),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
                "--server.address", "127.0.0.1"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(5)
            print(f"Streamlit server started on port {self.port}")
            
        except Exception as e:
            print(f"Error starting Streamlit: {e}")
    
    def stop_streamlit(self):
        """Stop Streamlit server"""
        if self.streamlit_process:
            self.streamlit_process.terminate()
            print("Streamlit server stopped")
    
    def on_window_closing(self):
        """Handle window closing"""
        self.stop_streamlit()
        
    def run(self):
        """Run the desktop app"""
        # Start Streamlit in background thread
        streamlit_thread = threading.Thread(target=self.start_streamlit)
        streamlit_thread.daemon = True
        streamlit_thread.start()
        
        # Wait a moment for server to be ready
        time.sleep(6)
        
        # Create desktop window
        webview.create_window(
            title="ECHO - Radiology CORE AI Assistant",
            url=f"http://127.0.0.1:{self.port}",
            width=1400,
            height=900,
            min_size=(1000, 700),
            resizable=True,
            shadow=True,
            on_top=False
        )
        
        # Start the app
        try:
            webview.start(debug=False)
        finally:
            self.stop_streamlit()

if __name__ == "__main__":
    print("ECHO Desktop App")
    print("=================")
    print("Starting ECHO as a desktop application...")
    print("This may take a moment to load...")
    
    try:
        app = ECHODesktopApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error running desktop app: {e}")
        print("Make sure you have installed: pip install pywebview")