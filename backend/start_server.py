#!/usr/bin/env python3
"""
Support AI Backend Startup Script
Run this script to start the FastAPI backend server
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    # Get the backend directory
    backend_dir = Path(__file__).parent
    
    print("🚀 Starting Support AI Backend...")
    print(f"📁 Working directory: {backend_dir}")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Check if virtual environment exists
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Determine the activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = venv_dir / "Scripts" / "activate.bat"
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:  # Unix/Linux/Mac
        activate_script = venv_dir / "bin" / "activate"
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    # Install dependencies
    print("📋 Installing dependencies...")
    try:
        subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies. Please check requirements.txt")
        return 1
    
    # Start the FastAPI server
    print("\n🌟 Starting FastAPI server on http://localhost:8000")
    print("📊 API docs available at http://localhost:8000/docs")
    print("💡 Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([
            str(python_exe), "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return 1

if __name__ == "__main__":
    exit(main())