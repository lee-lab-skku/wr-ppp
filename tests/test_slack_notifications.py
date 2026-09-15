"""Slack notification checks with no network requests or real credentials."""

import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/notify-held"))
NOTICE = MODULE["notice"]
SEND = MODULE["send"]
POST = MODULE["post"]
MAIN = MODULE["main"]
CONFIGURE = MODULE["configure"]
FAKE_URL = "https://hooks.slack.com/services/TEST/ONLY/fake_secret"


class SlackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="slack-notify-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "draft.tsv"
        self.rows = [
            ["schema", "admin-wr-bundle/v1"],
            ["bundle", "2026-09-10", "2026-09-W2", "2026-09-07", "2026-09-13",
             "draft", "required", "2026-09-W2.pdf", "hash"],
            ["entry", "1", "a", "구성원 <@U123>", "required", "missing", "-", "-", "-", "0", "-", "-", "missing-report"],
            ["entry", "2", "b", "Optional person", "optional", "optional-missing", "-", "-", "-", "0", "-", "-", "no-report"],
        ]
        self.write_manifest()
        (self.root / "slack-webhook.url").write_text(FAKE_URL)

    def write_manifest(self):
        self.manifest.write_text("\n".join("\t".join(r) for r in self.rows) + "\n", encoding="utf-8")

    def test_payload_only_contains_required_missing_names_and_week(self):
        payload, _ = NOTICE(self.manifest)
        self.assertIn("구성원 &lt;@U123&gt;", payload["text"])
        self.assertIn("구성원 <@U123>", payload["blocks"][0]["text"]["text"])
        self.assertIn("2026-09-W2", payload["text"])
        self.assertNotIn("Optional person", payload["text"])
        self.assertNotIn(str(self.root), json.dumps(payload))
        self.assertEqual(payload["blocks"][0]["text"]["type"], "plain_text")
        self.assertFalse(payload["mrkdwn"])

    def test_literal_quotes_do_not_strip_or_join_manifest_fields(self):
        for name in ('"Alice"', '"Alice', 'A "quoted" name'):
            with self.subTest(name=name):
                self.rows[2][3] = name
                self.write_manifest()
                payload, _ = NOTICE(self.manifest)
                self.assertIn('• ' + name, payload['blocks'][0]['text']['text'])

    def test_final_or_no_missing_records_cannot_notify(self):
        self.rows[1][5:7] = ["approved-with-issues", "user-confirmed"]
        self.write_manifest()
        with self.assertRaises(ValueError):
            NOTICE(self.manifest)
        self.rows[1][5:7] = ["draft", "required"]
        self.rows[2][4:6] = ["optional", "optional-missing"]
        self.write_manifest()
        with self.assertRaises(ValueError):
            NOTICE(self.manifest)

    def test_preview_never_sends_and_send_requires_hold(self):
        with patch.dict(MAIN.__globals__, send=lambda *a: self.fail("unexpected send")):
            with patch("sys.argv", ["notify-held", "--manifest", str(self.manifest)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(MAIN(), 0)
            with patch("sys.argv", ["notify-held", "--manifest", str(self.manifest), "--send"]), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    MAIN()
                self.assertEqual(error.exception.code, 2)

    def test_send_once_and_changed_missing_set_can_notify(self):
        payload, fingerprint = NOTICE(self.manifest)
        calls = []
        with patch.dict(SEND.__globals__, post=lambda url, data: calls.append((url, data))), contextlib.redirect_stdout(io.StringIO()):
            SEND(self.root, payload, fingerprint)
            SEND(self.root, payload, fingerprint)
            self.assertEqual(len(calls), 1)
            self.rows[2][2] = "another-member"
            self.write_manifest()
            payload2, fingerprint2 = NOTICE(self.manifest)
            SEND(self.root, payload2, fingerprint2)
            self.assertEqual(len(calls), 2)
        for path in (self.root / "notifications").iterdir():
            self.assertNotIn(FAKE_URL, path.read_text())

    def test_unconfirmed_delivery_blocks_automatic_repeat(self):
        payload, fingerprint = NOTICE(self.manifest)
        def fail(*args):
            raise ValueError("unconfirmed")
        with patch.dict(SEND.__globals__, post=fail):
            with self.assertRaisesRegex(ValueError, "unconfirmed"):
                SEND(self.root, payload, fingerprint)
        with patch.dict(SEND.__globals__, post=lambda *a: self.fail("unexpected retry")):
            with self.assertRaisesRegex(ValueError, "delivery review"):
                SEND(self.root, payload, fingerprint)
        self.assertFalse(list((self.root / "notifications").glob("*.sent")))

    def test_http_success_failure_and_url_redaction(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b"ok"
        class Opener:
            def open(inner, request, timeout):
                self.assertEqual(timeout, 15)
                self.assertEqual(json.loads(request.data), {"text": "한글"})
                return Response()
        with patch.dict(POST.__globals__, build_opener=lambda *a: Opener()):
            POST(FAKE_URL, {"text": "한글"})
        for failure in (HTTPError(FAKE_URL, 403, FAKE_URL, {}, None), URLError(FAKE_URL)):
            class FailedOpener:
                def open(self, *args, **kwargs): raise failure
            with patch.dict(POST.__globals__, build_opener=lambda *a: FailedOpener()):
                with self.assertRaises(ValueError) as error:
                    POST(FAKE_URL, {"text": "test"})
                self.assertNotIn(FAKE_URL, str(error.exception))

    def test_configure_uses_hidden_input_without_sending(self):
        with patch("sys.stdin.isatty", return_value=True), patch("getpass.getpass", return_value=FAKE_URL), contextlib.redirect_stdout(io.StringIO()):
            CONFIGURE(self.root)
        self.assertEqual((self.root / "slack-webhook.url").read_text(), FAKE_URL + "\n")
        if os.name != 'nt':  # Windows uses ACLs, not POSIX mode bits.
            self.assertEqual((self.root / "slack-webhook.url").stat().st_mode & 0o777, 0o600)
        self.assertFalse((self.root / "notifications").exists())

    def test_non_slack_urls_rejected_without_printing_secret(self):
        for value in ("http://hooks.slack.com/services/A/B/secret", "https://example.com/secret", FAKE_URL + "?secret"):
            with self.assertRaises(ValueError) as error:
                MODULE["validate_webhook"](value)
            self.assertNotIn(value, str(error.exception))


if __name__ == "__main__":
    unittest.main()
