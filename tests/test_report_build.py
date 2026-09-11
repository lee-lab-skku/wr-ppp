"""Report serial-number checks with a substituted Docker build."""

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class ReportSerialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="report-count-test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        shutil.copytree(REPO / "scripts", self.repo / "scripts")
        self.output = self.root / "output"
        self.output.mkdir()
        self.source = self.root / "current report"
        self.source.mkdir()
        (self.source / "main.tex").write_text("test source\n")
        (self.repo / ".local-config").write_text(
            f"PDF_OUTPUT_DIR={shlex.quote(str(self.output))}\n"
            "DOCKER_IMAGE=test-image\n"
        )
        self.bin = self.root / "bin"
        self.bin.mkdir()
        docker = self.bin / "docker"
        docker.write_text("#!/bin/sh\ncat >/dev/null\nprintf '%%PDF-1.4\\n'\n")
        docker.chmod(0o755)

    def build(self, serial, *args):
        result = subprocess.run(
            ["bash", str(self.repo / "scripts/report-build"), *args],
            cwd=self.source,
            env=dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}"),
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"serial : #{serial}\n", result.stderr)

    def test_filters_artifacts_and_counts_regular_reports_once(self):
        for name in (
            "previous.pdf", "대문자.PDF", "line\nbreak.pdf", "_report.pdf",
            "current report.pdf", "._previous.pdf", "_.previous.pdf",
            ".hidden.pdf", "~$locked.pdf", "draft.tmp.pdf", "draft.TEMP.PDF",
            "previous.bak.pdf",
        ):
            (self.output / name).write_bytes(b"fixture")
        (self.output / "nested.pdf").mkdir()
        (self.output / "nested.pdf" / "report.pdf").write_bytes(b"fixture")
        (self.output / "linked.pdf").symlink_to(self.output / "previous.pdf")
        self.build(5)
        self.build(5, "--here")
        self.assertTrue((self.output / "._previous.pdf").exists())

    def test_empty_directory_and_explicit_override(self):
        self.build(1)
        self.build(17, "--serial", "17")

    def test_hidden_current_target_does_not_reduce_count(self):
        hidden_source = self.root / ".current"
        self.source.rename(hidden_source)
        self.source = hidden_source
        (self.output / ".current.pdf").write_bytes(b"fixture")
        self.build(1)
