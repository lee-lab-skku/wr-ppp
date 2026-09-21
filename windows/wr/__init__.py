"""Native Windows adapters for shared repository resources."""
from pathlib import Path
import sys

# Source entry points run with windows/ on sys.path. Frozen builds collect the
# common package through PyInstaller's repository-root analysis path instead.
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
