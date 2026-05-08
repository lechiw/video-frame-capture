# -*- coding: utf-8 -*-
"""Entry point for PyInstaller packaging."""
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from video_frame_capture.__main__ import main

if __name__ == '__main__':
    main()
