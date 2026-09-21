#!/usr/bin/env python3
"""Small importer regression check for prose, lists and ReportTable."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from report_editor.tex_to_state import convert

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

class TexImporterTests(unittest.TestCase):
    def test_preserves_week_and_prose_table_list_order(self):
        state = convert(tex, '2026-09-07')
        self.assertEqual(state['weekStart'], '2026-09-07')
        blocks = [entry['text'] for entry in state['flow'] if entry['type'] == 'block']
        self.assertEqual(blocks, [
            r'First paragraph with \qty{50}{ms}.',
            '| Name | Value |\n| --- | --- |\n| A | 1 |\n: Measured values.',
            '- Kept one.\n- Kept two.',
            'Final paragraph.',
        ])


if __name__ == '__main__':
    unittest.main()
