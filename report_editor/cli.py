"""Open a shared browser editing session; PDF generation stays in report-build."""
import argparse
import datetime
import sys
import threading
import webbrowser

from .server import VisualEditorServer
from .tex_backend import TexBackend


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', help='Existing .tex report; unsupported sources are refused')
    parser.add_argument('--output', help='New sibling .tex file (default: <source>.edited.tex)')
    parser.add_argument('--date', type=datetime.date.fromisoformat,
                        help='Reporting date for the preview; use the same date with report-build')
    parser.add_argument('--no-open', action='store_true', help='Print the local URL without opening a browser')
    args = parser.parse_args(argv)
    date = args.date or datetime.date.today()
    monday = date - datetime.timedelta(days=date.weekday())
    try:
        backend = TexBackend(args.source, args.output, monday.isoformat())
        server = VisualEditorServer(backend)
        url = server.start()
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1
    try:
        print(f'Editor: {url}', flush=True)
        print(f'Edited source: {backend.output}', flush=True)
        print('Keep this process running while editing; press Ctrl+C to stop.', flush=True)
        if not args.no_open:
            webbrowser.open(url)
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0
