#!/usr/bin/env python3
"""Small importer regression check for prose, lists and ReportTable."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tex_to_state', ROOT / 'scripts' / 'tex_to_state.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

tex = r"""
\begin{pppbox}{Progress}
\ReportSubsection{Result}
First paragraph with \qty{50}{ms}.

\ReportTable
  {L C}
  {\toprule Name & Value \\ \midrule A & 1 \\ \bottomrule}
  {Measured values.}
  {tab:result}

\begin{itemize}
  \item Kept one.
  \item Kept two.
\end{itemize}

Final paragraph.
\end{pppbox}
"""

state = module.convert(tex, '2026-09-07')
assert state['weekStart'] == '2026-09-07'
blocks = [entry['text'] for entry in state['flow'] if entry['type'] == 'block']
assert blocks == [
    r'First paragraph with \qty{50}{ms}.',
    '| Name | Value |\n| --- | --- |\n| A | 1 |\n: Measured values.',
    '- Kept one.\n- Kept two.',
    'Final paragraph.',
], blocks
print('ok: prose, ReportTable and list order preserved')
