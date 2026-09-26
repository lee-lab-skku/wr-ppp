#!/usr/bin/env python3
"""Check exact source preservation through the editor's lossless model.

The similarity percentage is diagnostic only; --min cannot permit source loss.
Unsupported syntax remains read-only rather than disappearing during import.
"""
import difflib
import re
import sys
from pathlib import Path

from .preservation import import_source
from .state_to_tex import render


def normalise(text):
    return re.sub(r'\s+', ' ', text).strip()


def assess(original):
    """Return diagnostic similarity and exact-preservation failures."""
    state = import_source(original)
    back = render(state)
    ratio = difflib.SequenceMatcher(None, normalise(original), normalise(back), autojunk=False).ratio()
    # Similarity is descriptive, never an authorization to drop source.
    return ratio, ([] if original == back else ['source is not preserved exactly'])


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    floor = 0.99
    for a in sys.argv[2:]:
        if a.startswith('--min'):
            floor = float(a.split('=', 1)[1] if '=' in a else sys.argv[sys.argv.index(a) + 1])
    try:
        ratio, found = assess(src.read_bytes().decode('utf-8'))
    except (ValueError, KeyError) as error:
        print('FAIL: conversion errored\n' + str(error))
        return 1
    print(f'round-trip fidelity: {ratio*100:.1f}%  (floor {floor*100:.0f}%)')
    for why in found:
        print('  unsupported:', why)
    if ratio >= floor and not found:
        print('Source preserved exactly; unsupported regions remain read-only.')
        return 0
    print('\nNOT safe to edit: writing the artifact back would drop the content above.')
    print('Keep this report in LaTeX; do not remove content to pass this check.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
