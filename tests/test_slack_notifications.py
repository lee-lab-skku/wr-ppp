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
             "draft", "required", "2026-09-W2.pdf", "a" * 64],
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


class ReviewNoticeTests(unittest.TestCase):
    setUp = SlackTests.setUp
    write_manifest = SlackTests.write_manifest

    def selected(self, code, pages=2):
        self.rows[2] = ["entry", "1", "a", "구성원 <@U123>", "required", "included",
                        "private/report.pdf", "1", "b" * 64, str(pages), "2", str(pages + 1), "selected"]
        self.rows.append(["issue", "warning", code, "a", "Private evidence /private/report.pdf"])
        self.write_manifest()

    def proposal(self, items=None, **kwargs):
        value = {"introduction": "검토 결과를 안내합니다.", "closing": "확인 부탁드립니다.",
                 "items": items if items is not None else [{"member_id": "a", "code": "missing-report",
                    "description": "해당 기간의 제출본이 확인되지 않았습니다.", "action": "제출 여부를 알려 주세요."}]}
        value.update(kwargs)
        path = self.root / "message.json"
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def test_all_supported_types_and_included_warnings(self):
        for code in MODULE['ISSUE_TYPES']:
            with self.subTest(code=code):
                self.setUp()
                if code != 'missing-report':
                    self.selected(code, pages=3 if code == 'overlength-report' else 2)
                payload, _ = MODULE['review_notice'](self.manifest)
                self.assertIn(MODULE['ISSUE_TYPES'][code][0], payload['text'])
                self.assertNotIn('private', json.dumps(payload))
                self.assertNotIn('취합 보류', payload['text'])
                if code == 'overlength-report':
                    self.assertIn('3페이지', payload['text'])

    def test_custom_prose_and_multiple_problems_grouped(self):
        self.selected('unreadable-pdf')
        self.rows.append(['issue', 'error', 'ambiguous-report', 'a', 'Two candidates'])
        self.write_manifest()
        path = self.proposal(items=[
            {'member_id': 'a', 'code': code, 'description': '정상 대체본이 있습니다.', 'action': '최종본을 확인해 주세요.'}
            for code in ['unreadable-pdf', 'ambiguous-report']])
        payload, fingerprint = MODULE['review_notice'](self.manifest, path)
        self.assertEqual(len(fingerprint), 64)
        self.assertEqual(len(payload['blocks']), 4)
        self.assertEqual(payload['text'].count('구성원'), 1)
        self.assertIn('정상 대체본', payload['text'])
        self.assertTrue(all(block['text']['type'] == 'plain_text' for block in payload['blocks']))

    def test_optional_unreadable_report_can_notify_but_optional_omission_cannot(self):
        self.rows[2][4:6] = ['optional', 'optional-missing']
        self.rows.append(['issue', 'error', 'unreadable-pdf', 'a', 'Rejected broken PDF'])
        self.write_manifest()
        MODULE['review_notice'](self.manifest)
        self.rows.pop()
        self.rows.append(['issue', 'warning', 'first-run', '-', 'First run'])
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'No supported'):
            MODULE['review_notice'](self.manifest)

    def test_invalid_scope_and_message_schema_rejected(self):
        for items in [[], [{'member_id': 'unknown', 'code': 'missing-report', 'description': '', 'action': 'Submit'}],
                      [{'member_id': 'a', 'code': 'first-run', 'description': '', 'action': 'Submit'}],
                      [{'member_id': 'a', 'code': 'missing-report', 'description': '', 'action': 'Submit'}] * 2]:
            with self.subTest(items=items), self.assertRaises(ValueError):
                MODULE['review_notice'](self.manifest, self.proposal(items))
        with self.assertRaises(ValueError):
            MODULE['review_notice'](self.manifest, self.proposal(introduction=123))
        with self.assertRaises(ValueError):
            MODULE['review_notice'](self.manifest, self.proposal(items=[{'member_id': 'a', 'code': 'missing-report', 'description': '', 'action': ' '}]))

    def test_unknown_issue_member_and_false_overlength_rejected(self):
        self.rows.append(['issue', 'error', 'ambiguous-report', 'unknown', 'Unknown member'])
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'unknown member'):
            MODULE['review_notice'](self.manifest)
        self.rows.pop()
        self.selected('overlength-report', pages=2)
        with self.assertRaisesRegex(ValueError, 'longer than two'):
            MODULE['review_notice'](self.manifest)

    def test_final_review_record_rejected(self):
        self.rows[1][5:7] = ['approved-with-issues', 'user-confirmed']
        self.write_manifest()
        with self.assertRaises(ValueError):
            MODULE['review_notice'](self.manifest)

    def test_private_prose_and_length_limits(self):
        for prose in ['/private/report.pdf', r'C:\Review\report.pdf', r'\\server\share', 'https://example.com', FAKE_URL]:
            with self.subTest(prose=prose), self.assertRaises(ValueError):
                MODULE['review_notice'](self.manifest, self.proposal(introduction=prose))
        with self.assertRaisesRegex(ValueError, 'block limits'):
            MODULE['review_notice'](self.manifest, self.proposal(closing='a' * 3000))
        self.rows[2][3] = '"Quoted" <@U123>'
        self.write_manifest()
        payload, _ = MODULE['review_notice'](self.manifest)
        self.assertIn('&lt;@U123&gt;', payload['text'])
        self.assertIn('"Quoted" <@U123>', payload['blocks'][2]['text']['text'])

    def test_fingerprint_ignores_issue_order_duplicates_and_private_evidence(self):
        self.selected('unreadable-pdf')
        self.rows.append(['issue', 'error', 'ambiguous-report', 'a', 'First explanation'])
        self.write_manifest()
        original = MODULE['review_notice'](self.manifest)[1]
        self.rows[-2:] = list(reversed(self.rows[-2:]))
        self.rows[-1][-1] = 'Different private explanation'
        self.rows.append(self.rows[-1][:])
        self.write_manifest()
        self.assertEqual(MODULE['review_notice'](self.manifest)[1], original)
        self.rows.pop()
        self.rows = [r for r in self.rows if not (r[0] == 'issue' and r[2] == 'ambiguous-report')]
        self.write_manifest()
        self.assertNotEqual(MODULE['review_notice'](self.manifest)[1], original)

    def test_review_cli_approval_and_preview_without_config(self):
        main = MODULE['issues_main']
        with patch.dict(main.__globals__, data_directory=lambda: self.fail('preview read configuration')):
            with patch('sys.argv', ['notify-issues', '--manifest', str(self.manifest)]), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(), 0)
                preview = json.loads(out.getvalue())
        with patch.dict(main.__globals__, data_directory=lambda: self.root, post=lambda *a: self.fail('unexpected send')):
            with patch('sys.argv', ['notify-issues', '--manifest', str(self.manifest), '--send']), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(), 1)
        with patch.dict(main.__globals__, data_directory=lambda: self.root, post=lambda *a: None):
            with patch('sys.argv', ['notify-issues', '--manifest', str(self.manifest), '--approved', preview['approval'], '--send']), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
        changed = self.proposal(closing='다른 요청입니다.')
        with patch.dict(main.__globals__, data_directory=lambda: self.root, post=lambda *a: self.fail('stale approval sent')):
            with patch('sys.argv', ['notify-issues', '--manifest', str(self.manifest), '--message', str(changed), '--approved', preview['approval'], '--send']), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(), 1)

    def test_root_and_skill_entry_points_preview_without_network(self):
        import subprocess
        repository = Path(__file__).resolve().parents[1]
        expected = MODULE['review_notice'](self.manifest)[0]
        for command in ['scripts/notify-issues', 'skills/admin-wr/scripts/notify-issues']:
            result = subprocess.run([str(repository / command), '--manifest', str(self.manifest)],
                                    capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout)['payload'], expected)

    def test_legacy_receipt_is_still_recognized(self):
        import hashlib
        payload, fingerprint = NOTICE(self.manifest)
        expected = hashlib.sha256(json.dumps(['2026-09-W2', ['a']], ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(fingerprint, expected)
        receipts = self.root / 'notifications'
        receipts.mkdir()
        (receipts / (expected + '-' + hashlib.sha256(FAKE_URL.encode()).hexdigest()[:16] + '.sent')).write_text('sent\n')
        with patch.dict(SEND.__globals__, post=lambda *a: self.fail('legacy receipt was ignored')), contextlib.redirect_stdout(io.StringIO()):
            SEND(self.root, payload, fingerprint)

    def test_many_members_use_separate_blocks_and_fail_without_truncation(self):
        self.rows = self.rows[:2]
        for index in range(48):
            self.rows.append(['entry', str(index + 1), str(index), '구성원 ' + str(index), 'required', 'missing', '-', '-', '-', '0', '-', '-', 'missing-report'])
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'block limits'):
            MODULE['review_notice'](self.manifest)
        self.rows = self.rows[:4]
        self.write_manifest()
        payload, _ = MODULE['review_notice'](self.manifest)
        self.assertIn('구성원 0', payload['text'])
        self.assertIn('구성원 1', payload['text'])
        self.assertEqual(len(payload['blocks']), 5)

    def test_changed_message_can_notify_but_same_message_deduplicates(self):
        payload, fingerprint = MODULE['review_notice'](self.manifest)
        with patch.dict(SEND.__globals__, post=lambda *a: None), contextlib.redirect_stdout(io.StringIO()):
            SEND(self.root, payload, fingerprint)
            receipt = next((self.root / 'notifications').glob('*.sent'))
            SEND(self.root, payload, fingerprint)
            self.assertEqual(len(list((self.root / 'notifications').glob('*.sent'))), 1)
            new_payload, new_fingerprint = MODULE['review_notice'](self.manifest, self.proposal())
            SEND(self.root, new_payload, new_fingerprint)
            self.assertEqual(len(list((self.root / 'notifications').glob('*.sent'))), 2)
            self.assertTrue(receipt.exists())


if __name__ == "__main__":
    unittest.main()
