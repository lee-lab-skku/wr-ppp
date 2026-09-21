#!/usr/bin/env python3
"""Compatibility entry point for the development-only editor geometry check."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'tests' / 'check_editor_geometry.py'),
                   run_name='__main__')
