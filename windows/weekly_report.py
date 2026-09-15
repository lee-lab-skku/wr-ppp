"""Source and packaged entry point."""
import sys
from wr.cli import main

if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    raise SystemExit(main(sys.argv[1:] or ['gui']))
