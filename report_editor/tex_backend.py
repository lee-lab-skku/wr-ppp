"""Connect the shared editor to TeX sources used by the Docker build workflow."""
from copy import deepcopy
import os
from pathlib import Path
import tempfile

from .check_roundtrip import assess
from .state_to_tex import render
from .tex_to_state import convert


def atomic_write(path, data):
    """Replace an editor output only after its complete contents are staged."""
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data.encode('utf-8') if isinstance(data, str) else data)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class TexBackend:
    """Edit a supported source into a separate sibling, retaining the original.

    Keep the output beside the input so existing relative figure paths continue
    to work. The existing importer is deliberately unchanged; its fidelity guard
    must pass before the browser can trigger any saves.
    """
    def __init__(self, source, output=None, week_start=''):
        source = Path(source).resolve()
        if source.suffix.lower() != '.tex' or not source.is_file():
            raise ValueError('The source must be an existing .tex report.')
        self.directory = source.parent
        self.output = (Path(output).absolute() if output else
                       source.with_name(source.stem + '.edited.tex'))
        if self.output.parent.resolve() != self.directory or self.output.suffix.lower() != '.tex':
            raise ValueError('Choose a .tex output beside the source to preserve relative asset paths.')
        if self.output.exists() or self.output.is_symlink():
            raise ValueError(f'Output already exists; choose another --output: {self.output}')
        original = source.read_text(encoding='utf-8')
        ratio, unsupported = assess(original)
        if ratio < 0.99 or unsupported:
            detail = '; '.join(unsupported) or 'content or structure changes during conversion'
            raise ValueError(f'Cannot edit this source safely ({ratio:.1%} fidelity): {detail}. Keep it in LaTeX.')
        self.state = convert(original, week_start)

    def load(self):
        state = deepcopy(self.state)
        for entry in state['flow']:
            for item in entry.get('items', []):
                path = item.get('path', '')
                if path.startswith('figures/'):
                    item.setdefault('prev', '/' + path)
        return state

    def save(self, state):
        tex = render(state)
        atomic_write(self.output, tex)
        self.state = deepcopy(state)

    def write_image(self, target, data):
        atomic_write(target, data)
