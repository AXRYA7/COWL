"""
COWL — Launcher Entry Point
Usage: python run_cowl.py
"""
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.gui import main

if __name__ == '__main__':
    main()
