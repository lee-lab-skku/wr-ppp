"""Native GUI preservation and stale browser callback tests."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'windows'))


@unittest.skipUnless(os.name == 'nt', 'Native Windows Tk test')
class EditorGuiTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from wr.gui import App
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        config = patch.dict(os.environ, WR_CONFIG=str(self.directory / 'config.json'))
        config.start()
        self.addCleanup(config.stop)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = App(self.root)
        self.app.form_file = self.directory / 'report.wr.json'
        self.app.fields['title'].set('Original')
        self.app.form_values = {'extra': {'retain': True}}
        self.app.save_report()
        from wr.visual_editor import FormBackend
        self.backend = FormBackend(self.app.form_file)
        self.state = self.backend.load()

    def update(self):
        return (self.app.form_file.resolve(), json.loads(self.app.form_file.read_text(encoding='utf-8')),
                self.backend.expected, self.backend.tex_expected)

    def test_extra_fields_survive_gui_and_browser(self):
        self.state['title'] = 'Browser'
        self.backend.save(self.state)
        self.app.apply_visual_values(self.update())
        self.app.save_report()
        values = json.loads(self.app.form_file.read_text(encoding='utf-8'))
        self.assertEqual(values['title'], 'Browser')
        self.assertEqual(values['extra'], {'retain': True})

    def test_unsaved_gui_text_is_not_overwritten_by_browser_callback(self):
        from report_editor.persistence import ConflictError
        self.app.texts['Progress'].insert('1.0', 'Unsaved form text')
        self.state['title'] = 'Browser'
        self.backend.save(self.state)
        self.app.apply_visual_values(self.update())
        self.assertEqual(self.app.texts['Progress'].get('1.0', 'end-1c'), 'Unsaved form text')
        with self.assertRaises(ConflictError):
            self.app.save_report()
        self.assertEqual(json.loads(self.app.form_file.read_text(encoding='utf-8'))['title'], 'Browser')

    def test_delayed_callback_does_not_adopt_a_newer_fingerprint(self):
        self.state['title'] = 'First'
        self.backend.save(self.state)
        first = deepcopy(self.update())
        self.state['title'] = 'Second'
        self.backend.save(self.state)
        second = self.update()
        self.app.apply_visual_values(first)
        self.assertEqual(self.app.fields['title'].get(), 'Original')
        self.app.apply_visual_values(second)
        self.assertEqual(self.app.fields['title'].get(), 'Second')
        self.app.save_report()
        self.assertEqual(json.loads(self.app.form_file.read_text(encoding='utf-8'))['title'], 'Second')


if __name__ == '__main__':
    unittest.main()
