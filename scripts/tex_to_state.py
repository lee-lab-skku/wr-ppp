#!/usr/bin/env python3
"""Compatibility entry point for the shared report editor."""
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if __name__ == '__main__':
    runpy.run_module('report_editor.tex_to_state', run_name='__main__')
