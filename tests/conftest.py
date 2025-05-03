"""
Configuration for pytest tests.

This file sets up the Python path so tests can import from the app module.
"""
import sys
from pathlib import Path

# Add the repository root directory to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
