"""Black-box administrator workflow checks; no Docker engine or desktop needed."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")


def executable(path, code):
    path.write_text(f"#!{sys.executable}\n{code}", encoding="utf-8")
    path.chmod(0o755)


@unittest.skipIf(os.name == 'nt', 'POSIX shell workflow; Windows-native coverage is in windows/tests')
class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="admin-wr-test ")
        self.addCleanup(self.temp.cleanup)
        # Match shell pwd -P when macOS TEMP starts with the /var symlink.
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo's files"
        self.repo.mkdir()
        for directory in ("scripts", "skills"):
            shutil.copytree(REPO / directory, self.repo / directory, symlinks=True)
        for name in ("template.tex", "weekly-report.sty"):
            shutil.copyfile(REPO / name, self.repo / name)
        self.output = self.root / "final PDFs"
        self.review = self.root / "review's PDFs"
        self.storage = self.root / "sources"
        self.storage.mkdir()
        self.source = self.storage / "구성원 가.pdf"
        self.source.write_bytes(b"%PDF-1.4\nsource fixture\n")
        (self.repo / ".local-config").write_text(
            "DOCKER_IMAGE=test-image\n"
            f"ADMIN_OUTPUT_DIR={shlex.quote(str(self.output))}\n",
            encoding="utf-8",
        )
        self.plan = self.root / "plan.tsv"
        self.clean_plan = (
            "schema\tadmin-wr-plan/v1\n"
            f"entry\t10\tmember-a\t구성원 가\trequired\tincluded\t{self.source}\tcurrent\n"
            f"candidate\tmember-a\tselected\t{self.source}\tcurrent\n"
        )
        self.plan.write_text(self.clean_plan, encoding="utf-8")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        executable(self.bin / "docker", '''
import io
import os
import re
import sys
import tarfile

args = sys.argv[1:]
if args[0] in ("info", "image") or "missing=0" in args[-1]:
    sys.exit(0)
assert "--network" in args and args[args.index("--network") + 1] == "none"
with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())) as archive:
    files = {item.name.removeprefix("./"): archive.extractfile(item).read()
             for item in archive if item.isfile()}
if "page-probe.tex" in args[-1]:
    for member in re.findall(rb"PageData\\{([^|]+)\\|", files["page-probe.tex"]):
        print(member.decode() + "|2")
else:
    if os.environ.get("ADMIN_TEST_BUILD_FAIL"):
        sys.exit(17)
    data = b"%PDF-1.4\\n" + files["bundle-data.tex"] + files["bundle-history.tex"]
    with tarfile.open(fileobj=sys.stdout.buffer, mode="w|") as archive:
        item = tarfile.TarInfo("bundle.pdf")
        item.size = len(data)
        archive.addfile(item, io.BytesIO(data))
''')
        self.env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}")
        self.builder = self.repo / "skills/admin-wr/scripts/build-bundle"

    def build(self, *flags, status=0):
        result = subprocess.run(
            [str(self.builder), "--storage-root", str(self.storage),
             "--plan", str(self.plan), "--date", "2026-09-04", *flags],
            env=self.env, cwd=self.root, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, status, result.stderr)
        return result

    def issues(self):
        self.plan.write_text(
            self.clean_plan + "issue\twarning\tfirst-run\t-\tNo previous bundle.\n",
            encoding="utf-8",
        )

    def test_final_manifest_is_separate_and_matches_pdf(self):
        source_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        result = self.build()
        pdf, manifest = map(Path, result.stdout.splitlines())
        self.assertEqual(pdf, self.output / "2026-09-W1.pdf")
        self.assertEqual(manifest, self.repo / ".admin-wr/manifests/2026-09-W1.manifest.tsv")
        self.assertEqual(list(self.output.iterdir()), [pdf])
        records = [line.split("\t") for line in manifest.read_text().splitlines()]
        bundle = next(record for record in records if record[0] == "bundle")
        self.assertEqual(bundle[5:9], ["complete", "not-required", pdf.name,
                                      hashlib.sha256(pdf.read_bytes()).hexdigest()])
        entry = next(record for record in records if record[0] == "entry")
        self.assertEqual(entry[8:13], [source_hash, "2", "2", "3", "current"])
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), source_hash)
        self.assertNotIn("review command:", result.stderr)

    def test_history_is_transposed_sorted_and_preserved(self):
        self.plan.write_text(self.clean_plan +
            "history\t2026-08-W4\tmember-a\tmissing\tverified-august\n"
            "history\t2025-12-W4\tmember-a\texception\tverified-december\n")
        result = self.build()
        pdf, manifest = map(Path, result.stdout.splitlines())
        rendered = pdf.read_text()
        self.assertIn("구성원 가", rendered)
        self.assertIn("2025-12-W4 & O*", rendered)
        self.assertIn("2026-08-W4 & X", rendered)
        self.assertIn("2026-09-W1 & O", rendered)
        self.assertLess(rendered.index("2026-09-W1 &"), rendered.index("2026-08-W4 &"))
        self.assertLess(rendered.index("2026-08-W4 &"), rendered.index("2025-12-W4 &"))
        self.assertIn("history\t2026-08-W4\tmember-a\tmissing\tverified-august", manifest.read_text())
        self.assertNotIn("2--3", rendered)

    def test_unknown_history_requires_review_and_is_not_missing(self):
        self.plan.write_text(self.clean_plan +
            "history\t2026-08-W4\tmember-a\tunknown\tinvalid-prior-hash\n")
        self.build(status=2)
        result = self.build("--draft", "--output-dir", str(self.review))
        pdf, manifest = map(Path, result.stdout.splitlines())
        self.assertIn("2026-08-W4 & ?", pdf.read_text())
        self.assertIn("history-unavailable", manifest.read_text())

    def test_twelve_members_share_one_table_with_all_weeks(self):
        plan = self.clean_plan
        for number in range(1, 12):
            plan += (f"entry\t{10 + number}\tmember-{number}\tName & {number}\toptional"
                     "\toptional-missing\t-\tno-report\n")
            plan += f"history\t2026-08-W4\tmember-{number}\toptional-missing\tverified\n"
        plan += "history\t2026-08-W4\tmember-a\tincluded\tverified\n"
        self.plan.write_text(plan)
        pdf = Path(self.build().stdout.splitlines()[0]).read_text()
        self.assertEqual(pdf.count("2026-09-W1 &"), 1)
        self.assertEqual(pdf.count("2026-08-W4 &"), 1)
        for number in range(1, 12):
            self.assertIn(f"Name \\& {number}", pdf)
        self.assertNotIn(" & ?", pdf)

    def test_absent_history_cell_requires_review(self):
        self.plan.write_text(self.clean_plan +
            "entry\t20\tmember-b\tNew member\toptional\toptional-missing\t-\tnone\n"
            "history\t2026-08-W4\tmember-a\tincluded\tverified\n")
        self.build(status=2)
        result = self.build("--draft", "--output-dir", str(self.review))
        pdf = Path(result.stdout.splitlines()[0]).read_text()
        self.assertIn("2026-08-W4 & O & ?", pdf)
        self.assertIn("2026-09-W1 & O & --", pdf)

    def test_invalid_history_rejected_before_output(self):
        rows = (
            "2026-09-W1\tmember-a\tincluded\tcurrent-week",
            "2027-01-W1\tmember-a\tincluded\tfuture",
            "2026-08-W4\tstranger\tincluded\tunknown-member",
            "2026-08-W4\tmember-a\tbogus\tinvalid-state",
            "2026-08-W4\tmember-a\tincluded\tduplicate\nhistory\t2026-08-W4\tmember-a\tmissing\tduplicate",
        )
        for row in rows:
            with self.subTest(row=row):
                self.plan.write_text(self.clean_plan + "history\t" + row + "\n")
                self.build(status=2)
                self.assertFalse(self.output.exists())

    def test_configured_history_output_and_draft_isolation(self):
        data = self.root / "admin data"
        config = self.repo / ".local-config"
        config.write_text(config.read_text() + f"ADMIN_DATA_DIR={shlex.quote(str(data))}\n")
        result = self.build()
        pdf, manifest = map(Path, result.stdout.splitlines())
        self.assertEqual(manifest, data / "manifests/2026-09-W1.manifest.tsv")
        self.assertFalse((self.repo / ".admin-wr").exists())
        history = manifest.read_bytes()
        self.issues()
        draft = self.build("--draft", "--output-dir", str(self.review))
        self.assertEqual(Path(draft.stdout.splitlines()[1]).parent, self.review / ".manifests")
        self.assertEqual(manifest.read_bytes(), history)

    def test_configured_history_write_failure_does_not_fall_back(self):
        result = self.build()
        paths = [Path(line) for line in result.stdout.splitlines()]
        before = [p.read_bytes() for p in paths]
        conflict = self.root / "blocked data"
        conflict.write_text("not a directory")
        config = self.repo / ".local-config"
        config.write_text(config.read_text() + f"ADMIN_DATA_DIR={shlex.quote(str(conflict))}\n")
        self.build(status=2)
        self.assertEqual([p.read_bytes() for p in paths], before)

    def test_draft_survives_and_prints_executable_review_command(self):
        self.issues()
        result = self.build("--draft", "--output-dir", str(self.review))
        pdf, manifest = map(Path, result.stdout.splitlines())
        self.assertTrue(pdf.is_file())
        self.assertEqual(manifest.parent, self.review / ".manifests")
        self.assertIn("\tdraft\trequired\t", manifest.read_text())
        self.assertFalse(self.output.exists())
        self.assertFalse((self.repo / ".admin-wr").exists())
        command = next(line.removeprefix("review command: ")
                       for line in result.stderr.splitlines()
                       if line.startswith("review command: "))
        # Run the emitted Bash command with a recording viewer in place of a GUI.
        executable(self.bin / "uname", 'print("Darwin")\n')
        log = self.root / "viewer.json"
        executable(self.bin / "open", f'''
import json, sys
from pathlib import Path
Path({str(log)!r}).write_text(json.dumps(sys.argv[1:]))
''')
        opened = subprocess.run([BASH, "-c", command], env=self.env, capture_output=True)
        self.assertEqual(opened.returncode, 0, opened.stderr)
        self.assertEqual(json.loads(log.read_text()), [str(pdf)])

    def test_approved_build_keeps_draft_history_and_legacy_records(self):
        self.issues()
        draft = self.build("--draft", "--output-dir", str(self.review))
        draft_manifest = Path(draft.stdout.splitlines()[1])
        draft_bytes = draft_manifest.read_bytes()
        self.output.mkdir()
        legacy = self.output / "2026-09-W1.manifest.tsv"
        legacy.write_text("existing legacy history\n")
        final = self.build("--approved-with-issues")
        manifest = Path(final.stdout.splitlines()[1])
        self.assertIn("\tapproved-with-issues\tuser-confirmed\t", manifest.read_text())
        self.assertEqual(draft_manifest.read_bytes(), draft_bytes)
        self.assertEqual(legacy.read_text(), "existing legacy history\n")
        self.assertNotEqual(manifest, legacy)

    def test_failed_rebuild_preserves_both_artifacts(self):
        result = self.build()
        artifacts = [Path(line) for line in result.stdout.splitlines()]
        before = [path.read_bytes() for path in artifacts]
        self.env["ADMIN_TEST_BUILD_FAIL"] = "1"
        self.build(status=1)
        self.assertEqual([path.read_bytes() for path in artifacts], before)
        self.assertFalse(list(self.output.glob(".*.tmp.*")))
        self.assertFalse(list(artifacts[1].parent.glob(".*.tmp.*")))

    def test_manifest_directory_conflict_preserves_existing_pdf(self):
        self.output.mkdir()
        pdf = self.output / "2026-09-W1.pdf"
        pdf.write_bytes(b"previous PDF")
        (self.repo / ".admin-wr").write_text("conflicting file")
        self.build(status=2)
        self.assertEqual(pdf.read_bytes(), b"previous PDF")

    def test_draft_cannot_write_within_final_output_including_aliases(self):
        self.issues()
        self.output.mkdir()
        alias = self.root / "output alias"
        alias.symlink_to(self.output, target_is_directory=True)
        for target in (self.output, self.output / "review", alias / "new/review"):
            with self.subTest(target=target):
                self.build("--draft", "--output-dir", str(target), status=2)
        self.assertEqual(list(self.output.iterdir()), [])


@unittest.skipIf(os.name == 'nt', 'POSIX shell workflow; Windows-native coverage is in windows/tests')
class AdminPathTests(unittest.TestCase):
    def setUp(self):
        BundleTests.setUp(self)
        self.data = self.root / "shared admin data"
        self.local = self.repo / ".manager-manifest.toml"
        self.local.write_text("local roster")
        self.history = self.repo / ".admin-wr/manifests"
        self.history.mkdir(parents=True)
        self.config = self.repo / ".local-config"
        self.config.write_text(self.config.read_text() +
            f"PDF_OUTPUT_DIR={shlex.quote(str(self.root / 'individual output'))}\n"
            f"ADMIN_DATA_DIR={shlex.quote(str(self.data))}\n")
        # Redirect installation destinations inside the fixture, including sudo.
        setup = self.repo / "scripts/setup.sh"
        setup.write_text(setup.read_text().replace(
            'REPORT_BUILD_TARGET="/usr/local/bin/report-build"',
            f'REPORT_BUILD_TARGET="{self.root / "commands/report-build"}"').replace(
            '${HOME:?HOME is not set}', str(self.root / "skill-links")))
        executable(self.bin / "sudo", "import os, sys\nos.execvp(sys.argv[1], sys.argv[1:])\n")

    def paths(self, *args, status=0, skill=False):
        command = self.repo / ("skills/admin-wr/scripts/admin-paths" if skill else "scripts/admin-paths")
        result = subprocess.run([str(command), *args], env=self.env,
                                text=True, capture_output=True, cwd=self.root)
        self.assertEqual(result.returncode, status, result.stderr)
        return result.stdout

    def setup(self, *args, status=0):
        result = subprocess.run([str(self.repo / "scripts/setup.sh"), *args], env=self.env,
                                text=True, capture_output=True, cwd=self.root)
        self.assertEqual(result.returncode, status, result.stderr)
        return result

    def test_shared_aliases_and_antigravity_install_identical_skill_links(self):
        self.setup("--skills=agents,claude,antigravity", "--admin")
        links = [self.root / "skill-links" / service / "skills" / skill
                 for service in (".agents", ".claude", ".gemini/config") for skill in ("wr-wr", "admin-wr")]
        targets = [link.readlink() for link in links]
        for link in links:
            self.assertTrue(link.samefile(self.repo / "skills" / link.name))
        for alias in ("codex", "gemini", "copilot"):
            result = self.setup(f"--skills={alias},claude,antigravity", "--admin")
            self.assertEqual([link.readlink() for link in links], targets)
            self.assertIn("Already linked: agents admin-wr skill", result.stdout)
            self.assertIn("Already linked: antigravity admin-wr skill", result.stdout)
        self.assertFalse((self.root / "skill-links/.gemini/skills").exists())
        self.assertFalse((self.root / "skill-links/.codex").exists())
        self.assertFalse((self.root / "skill-links/.copilot").exists())
        self.assertFalse(list((self.root / "skill-links").rglob("*.backup*")))

    def test_alias_and_canonical_duplicates_install_once(self):
        for services in (f"{first},{second}" for first in ("agents", "codex", "gemini", "copilot")
                         for second in ("agents", "codex", "gemini", "copilot")):
            with self.subTest(services=services):
                result = self.setup(f"--skills={services}", "--admin")
                for skill in ("wr-wr", "admin-wr"):
                    self.assertEqual(result.stdout.count(f"agents {skill} skill:"), 1)
                    link = self.root / "skill-links/.agents/skills" / skill
                    self.assertTrue(link.samefile(self.repo / "skills" / skill))

    def test_mixed_duplicate_destinations_preserve_first_occurrence(self):
        result = self.setup(
            "--skills=antigravity,copilot,agents,claude,gemini,antigravity,codex,claude",
            "--admin")
        messages = [line for line in result.stdout.splitlines() if " skill:" in line]
        self.assertEqual(len(messages), 6)
        for skill in ("wr-wr", "admin-wr"):
            services = [line.split(": ", 1)[1].split()[0]
                        for line in messages if f" {skill} skill:" in line]
            self.assertEqual(services, ["antigravity", "agents", "claude"])

    def test_duplicates_do_not_skip_invalid_services_or_parent_preflight(self):
        before = self.config.read_bytes()
        self.setup("--skills=agents,copilot,unknown", status=2)
        self.assertFalse((self.root / "commands").exists())
        self.assertFalse((self.root / "skill-links").exists())
        parent = self.root / "skill-links/.gemini"
        parent.mkdir(parents=True)
        (parent / "config").write_text("existing file")
        self.setup("--skills=gemini,copilot,antigravity,antigravity", "--admin", status=1)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual((parent / "config").read_text(), "existing file")
        self.assertFalse((self.root / "commands").exists())
        self.assertFalse((self.root / "skill-links/.agents").exists())

    def test_setup_custom_data_then_omitted_option_selects_local(self):
        self.setup("--skills=agents,claude", "--admin", f"--admin-data={self.data}")
        manifest = self.data / "manager-manifest.toml"
        self.assertIn("schema = 1", manifest.read_text())
        self.assertEqual(manifest.stat().st_mode & 0o777, 0o600)
        self.assertFalse((self.data / "manifests").exists())
        self.assertEqual(self.local.read_text(), "local roster")
        self.assertIn(str(manifest), self.paths(skill=True))
        manifest.write_text("external roster")
        self.setup("--skills=agents", "--admin", f"--admin-data={self.data}", "--replace-existing")
        self.assertEqual(manifest.read_text(), "external roster")
        self.setup()  # Non-admin setup retains saved administrator settings.
        self.assertIn(str(manifest), self.paths())
        self.setup("--skills=agents", "--admin")
        self.assertIn(f"manager-manifest\t{self.local}\n", self.paths())
        self.assertEqual(self.paths("--history-output").strip(), str(self.history))
        self.assertEqual(manifest.read_text(), "external roster")

    def test_missing_configured_files_fall_back_per_week(self):
        self.data.mkdir()
        (self.data / "manifests").mkdir()
        self.output.mkdir()
        (self.history / "2026-08-W4.manifest.tsv").write_text("local older")
        (self.history / "2026-09-W1.manifest.tsv").write_text("local shadowed")
        external = self.data / "manifests/2026-09-W1.manifest.tsv"
        external.write_text("invalid external record still takes precedence")
        legacy = self.output / "2026-08-W3.manifest.tsv"
        legacy.write_text("legacy")
        (self.output / "2026-08-W4.manifest.tsv").write_text("legacy shadowed")
        result = self.paths()
        self.assertIn(f"manager-manifest\t{self.local}\n", result)
        records = {r[1]: r[2] for line in result.splitlines()
                   if (r := line.split("\t"))[0] == "history"}
        self.assertEqual(records, {
            "2026-09-W1": str(external),
            "2026-08-W4": str(self.history / "2026-08-W4.manifest.tsv"),
            "2026-08-W3": str(legacy),
        })
        self.assertEqual(self.paths("--history-output").strip(), str(self.data / "manifests"))
        external.unlink()
        external.symlink_to(self.data / "missing-record")
        self.assertIn(str(self.history / "2026-09-W1.manifest.tsv"), self.paths())
        configured = self.data / "manager-manifest.toml"
        configured.write_text("invalid configured TOML")
        self.assertIn(f"manager-manifest\t{configured}\n", self.paths())
        self.assertNotIn(f"manager-manifest\t{self.local}\n", self.paths())

    def test_missing_directory_and_legacy_config_use_local(self):
        record = self.history / "2026-09-W1.manifest.tsv"
        record.write_text("local history")
        self.assertIn(str(record), self.paths())
        self.assertIn(f"manager-manifest\t{self.local}\n", self.paths())
        self.config.write_text("DOCKER_IMAGE=test-image\n")
        self.assertEqual(self.paths("--history-output").strip(), str(self.history))
        self.assertIn(f"manager-manifest\t{self.local}\n", self.paths(skill=True))

    def test_nas_manifest_creation_does_not_require_chmod(self):
        chmod = shutil.which("chmod")
        executable(self.bin / "chmod", f'''
import os, sys
from pathlib import Path
if Path(sys.argv[-1]).name == "manager-manifest.toml":
    print("chmod: Operation not permitted", file=sys.stderr)
    sys.exit(1)
os.execv({chmod!r}, [{chmod!r}, *sys.argv[1:]])
''')
        self.setup("--admin", "--skills=agents", f"--admin-data={self.data}")
        manifest = self.data / "manager-manifest.toml"
        self.assertIn("schema = 1", manifest.read_text())
        self.assertEqual(manifest.stat().st_mode & 0o777, 0o600)
        self.assertIn(f"manager-manifest\t{manifest}\n", self.paths())
        manifest.write_text("existing NAS roster")
        self.setup("--admin", "--skills=agents", f"--admin-data={self.data}")
        self.assertEqual(manifest.read_text(), "existing NAS roster")

    def test_existing_external_manifest_symlink_is_preserved(self):
        self.data.mkdir()
        manifest = self.data / "manager-manifest.toml"
        manifest.symlink_to(self.local)
        self.setup("--admin", "--skills=agents", f"--admin-data={self.data}", "--replace-existing")
        self.assertTrue(manifest.is_symlink())
        self.assertEqual(self.local.read_text(), "local roster")
        self.assertIn(f"manager-manifest\t{manifest}\n", self.paths())

    def test_setup_rejects_invalid_options_without_modifying_config(self):
        before = self.config.read_bytes()
        for args in (
            (f"--admin-data={self.data}",),
            ("--admin", "--skills=agents", "--admin-data="),
            ("--admin", "--skills=agents", "--admin-data=relative"),
            ("--admin", "--skills=agents", f"--admin-data={self.data}", f"--admin-data={self.data}"),
        ):
            with self.subTest(args=args):
                result = subprocess.run([str(self.repo / "scripts/setup.sh"), *args],
                                        env=self.env, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.config.read_bytes(), before)
        self.data.mkdir()
        (self.data / "manifests").write_text("conflicting file")
        self.setup("--admin", "--skills=agents", f"--admin-data={self.data}", status=1)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.data / "manager-manifest.toml").exists())


@unittest.skipIf(os.name == 'nt', 'POSIX shell workflow; Windows-native coverage is in windows/tests')
class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="admin-wr-preview ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for command in ("dirname", "basename"):
            (self.bin / command).symlink_to(shutil.which(command))
        executable(self.bin / "uname", '''
import os, sys
print(os.environ.get("ADMIN_TEST_SYSTEM", "Linux") if sys.argv[1] == "-s"
      else os.environ.get("ADMIN_TEST_RELEASE", "test-kernel"))
''')
        self.log = self.root / "viewer.json"
        self.pdf = self.root / "보고서's $(touch UNEXPECTED) `quote` [1].PDF"
        self.pdf.write_bytes(b"%PDF-1.4\npreview fixture\n")
        self.env = dict(os.environ, PATH=str(self.bin))
        self.env.pop("WSL_INTEROP", None)
        self.env.pop("WSL_DISTRO_NAME", None)
        self.opener = REPO / "skills/admin-wr/scripts/open-bundle"

    def viewer(self, command, status=0):
        executable(self.bin / command, f'''
import json, sys
from pathlib import Path
Path({str(self.log)!r}).write_text(json.dumps(sys.argv[1:]))
sys.exit({status})
''')

    def run_opener(self, *args, status=0):
        result = subprocess.run([BASH, str(self.opener), *map(str, args)],
                                env=self.env, text=True, capture_output=True,
                                cwd=self.root)
        self.assertEqual(result.returncode, status, result.stderr)
        self.assertFalse((self.root / "UNEXPECTED").exists())
        return result

    def test_linux_and_macos_pass_literal_pdf_path(self):
        for system, command in (("Linux", "xdg-open"), ("Darwin", "open")):
            with self.subTest(system=system):
                self.env["ADMIN_TEST_SYSTEM"] = system
                self.viewer(command)
                self.run_opener(self.pdf)
                self.assertEqual(json.loads(self.log.read_text()), [str(self.pdf)])

    def test_wslview_is_used_when_available(self):
        self.env["ADMIN_TEST_RELEASE"] = "6.6.87.2-microsoft-standard-WSL2"
        self.viewer("wslview")
        self.run_opener(self.pdf)
        self.assertEqual(json.loads(self.log.read_text()), [str(self.pdf)])

    def test_wsl_powershell_escapes_apostrophes_and_preserves_metacharacters(self):
        self.env["WSL_DISTRO_NAME"] = "TestDistribution"
        windows_path = r"\\wsl.localhost\TestDistribution\tmp" + "\\" + self.pdf.name
        executable(self.bin / "wslpath", f'''
import sys
assert sys.argv[1:] == ["-w", {str(self.pdf)!r}]
print({windows_path!r})
''')
        self.viewer("powershell.exe")
        result = self.run_opener(self.pdf)
        args = json.loads(self.log.read_text())
        self.assertEqual(args[:3], ["-NoProfile", "-NonInteractive", "-Command"])
        self.assertEqual(args[3], "$ErrorActionPreference = 'Stop'; Start-Process -FilePath '"
                         + windows_path.replace("'", "''") + "'")
        self.assertIn(windows_path, result.stderr)

    def test_unavailable_or_failed_viewer_reports_path_and_failure(self):
        for wsl in (False, True):
            with self.subTest(wsl=wsl):
                if wsl:
                    self.env["WSL_DISTRO_NAME"] = "TestDistribution"
                result = self.run_opener(self.pdf, status=1)
                self.assertIn(str(self.pdf), result.stderr)
                self.assertFalse(self.log.exists())
        self.env.pop("WSL_DISTRO_NAME")
        self.viewer("xdg-open", status=9)
        result = self.run_opener(self.pdf, status=1)
        self.assertIn(str(self.pdf), result.stderr)

    def test_invalid_inputs_do_not_launch_viewer(self):
        self.viewer("xdg-open")
        non_pdf = self.root / "notes.txt"
        non_pdf.write_text("notes")
        empty_pdf = self.root / "empty.pdf"
        empty_pdf.touch()
        for args in ((), (self.pdf.name,), (self.root / "missing.pdf",),
                     (non_pdf,), (empty_pdf,), (self.root,), (self.pdf, self.pdf)):
            with self.subTest(args=args):
                self.run_opener(*args, status=2)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
