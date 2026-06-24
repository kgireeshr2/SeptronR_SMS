"""
Symlink/alias to main.py in parent directory for uvicorn app.main:app support
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import everything from the real main.py
from main import *
