#!/usr/bin/env python3
"""
Launch script for Automaton Auditor Web UI
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the Streamlit web UI."""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    ui_dir = script_dir / "web_ui"
    
    # Check if web_ui directory exists
    if not ui_dir.exists():
        print("❌ Error: web_ui directory not found!")
        print("Please ensure the web_ui directory exists with app.py")
        sys.exit(1)
    
    # Change to web_ui directory
    os.chdir(ui_dir)
    
    # Check if app.py exists
    if not Path("app.py").exists():
        print("❌ Error: app.py not found in web_ui directory!")
        sys.exit(1)
    
    print("🚀 Starting Automaton Auditor Web UI...")
    print("📍 Location:", ui_dir)
    print("🌐 Opening in browser...")
    print()
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down web UI...")
        sys.exit(0)

if __name__ == "__main__":
    main()
