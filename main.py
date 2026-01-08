"""
Lighthouse Node Editor Application

A visual node-based editor built with DearPyGui for creating and configuring
workflow nodes. Supports various node types including HTTP requests, command
execution, and chat model integration with a drag-and-drop interface.

Author: Ray B.
Version: 1.0.0
"""

from src.lighthouse import LighthouseApp

if __name__ == "__main__":
    # Create and run the application
    app = LighthouseApp()
    app.run()
