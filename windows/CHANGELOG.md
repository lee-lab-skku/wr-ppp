<!-- markdownlint-disable MD024 -->

# Windows Implementation Changelog

This log records Windows internal changes and their validation evidence.
User-visible release changes and repository versions remain in the [root changelog](../CHANGELOG.md).
There is no independent Windows version sequence.
See [CONTRIBUTING.md](CONTRIBUTING.md#documenting-internal-changes) for entry conventions.

## Unreleased

## 2026-09-23 &mdash; Windows distribution notices and source references

Changes: [57be8ab](https://github.com/lee-lab-skku/wr-ppp/commit/57be8ab), [127f313](https://github.com/lee-lab-skku/wr-ppp/commit/127f313), [4266ed1](https://github.com/lee-lab-skku/wr-ppp/commit/4266ed1), and [cf140f7](https://github.com/lee-lab-skku/wr-ppp/commit/cf140f7a7cded729d27bf8eb00db0b087df523da).

### Fixed

- Collect the canonical project license and notice plus the KaTeX license in PyInstaller resources; retain the upstream KaTeX text inside editor HTML for source, local-server, and standalone-export use.
- Compare full legal resources and attributed editor HTML with the selected checkout in portable and installed smoke tests, with missing-file and changed-content regression cases.
- Collect the selected Python installation and package licenses, actual PyInstaller runtime-hook attribution, and native payload hashes; verify the generated inventory after packaging and installation.
- Prepare TeX packages and named legal/readme documents from one resolved mirror, updating existing packages before installation; retain checksum-matched notices with the dependency cache without enabling full documentation installation.
  Reject mismatched repository content before downloading documentation archives, reporting the selected mirror, package revisions, and differing hashes.
- Sanitize offline portable bundles as well as installers, preserve collected notices, and identify TeX packaging modifications in the distributed notice.
- Include Ghostscript 10.08.0 source/Windows-patch locations, hashes, historical retrieval and patch instructions in the distributed TeX notice, with source directions in release notes and a package-identity check to reject stale references.
  Preserve the canonical notice with LF line endings for byte comparisons across Windows and WSL.

### Validation

- Working-tree notice changes on Linux: five shared-editor tests passed, covering both HTTP adapters and standalone HTML export; geometry, inline rendering, upstream license byte comparison, and whitespace checks passed.
  Chrome/Chromium and native Windows PowerShell were unavailable, so browser and PowerShell checks skipped execution; no new portable bundle or installer was built.
- Runtime/TeX notice implementation on Linux: all 129 common regression tests passed, followed by all 15 collector/sanitizer tests after the final preservation adjustment.
  Checksum-verified UnFonts core/extra documentation archives exercised the real archive layout and selective extraction without installation or network access.
  Python/spec syntax, PowerShell ASCII source, and whitespace checks passed; five native PowerShell tests skipped, and Windows packaging/installation remains untested.
- Repository alignment changes on Linux: all 16 collector/sanitizer tests passed, including rejection of a late package mismatch before any documentation archive download.
  Six native PowerShell tests skipped locally, including the new orchestration check for shared mirror selection, update ordering, and stopping on resolution/update failures.
- [CI run 35839416523](https://github.com/lee-lab-skku/wr-ppp/actions/runs/35839416523) passed for `4266ed1`, including Windows packaging, portable/installed checks and uninstallation; the user also confirmed report builds from the installed artifact.
- Ghostscript source-reference changes on Linux: all 18 collector/sanitizer tests passed, including rejection of changed package revisions/checksums with an otherwise intact prepared inventory.
  The installed artifact matches the reviewed package identity; source hashes and inclusion of both source directions in a temporary release-note preview passed.
  The upstream Windows patch passed a zero-fuzz dry run against 41 source files; native Ghostscript compilation, historical Subversion retrieval and a new Windows installer build were not run.

## 2026-09-21 &mdash; Documentation consolidation and figure compatibility

Changes: [2177d35](https://github.com/lee-lab-skku/wr-ppp/commit/2177d35), [daf9985](https://github.com/lee-lab-skku/wr-ppp/commit/daf9985), and [b7c64d7](https://github.com/lee-lab-skku/wr-ppp/commit/b7c64d7).

### Changed

- Consolidate user guidance, contributor procedures, and internal history into English README, CONTRIBUTING, and CHANGELOG documents with one sentence per source line; retain historical validation scope and limitations here rather than in separate validation documents.
- Stage available local images from shared report figure commands while leaving unavailable or excluded linked images to the shared style's placeholder rendering, including pairs with only one available image.

### Validation

- Report-figure staging, 2026-09-21: four focused tests passed on native Windows Python 3.13.7 with pypdf 6.18.0, covering referenced assets, missing single/paired images, and source preservation.
  Native Windows TeX Live 2026 produced a one-page PDF with two expected placeholders from a source containing a missing single image and a pair with one available image.
  A missing raw `\includegraphics` file still produced a LaTeX error.
  These checks exercised the figure-staging change recorded in [b7c64d7](https://github.com/lee-lab-skku/wr-ppp/commit/b7c64d7), not a rebuilt installer; GUI and packaged application checks were not rerun.

## 2026-09-21 &mdash; Shared editor and source entry points

Changes: [b82dfac](https://github.com/lee-lab-skku/wr-ppp/commit/b82dfac) and [91b01be](https://github.com/lee-lab-skku/wr-ppp/commit/91b01be).

### Changed

- Move browser transport and editor assets into the common package while keeping the native form model, persistence callbacks, GUI, and PDF workflow in the Windows application.
- Collect shared resources through the PyInstaller repository import root and prepare source import paths at launch and test entry points instead of during `wr` package import.

### Validation

- Shared-editor change: 111 common tests passed, including HTTP save checks for both the TeX and native form adapters; a shared-editor output compiled through Docker to a one-page PDF.
- Entry-point follow-up: 114 common tests passed, then the converted importer regression passed as an individual unittest case.
- HTML and core conversion implementations were checked against their previous sources; geometry, inline rendering, skill metadata, and local documentation links passed their checks.
- WSL mirrored mode: a Windows PowerShell HTTP client loaded the WSL-hosted editor (200) and saved edited TeX into WSL (204), leaving the original source unchanged.
- Browser interaction, the native Windows GUI, and the rebuilt Windows installer were not exercised for these changes; adapter tests on WSL do not certify those native paths.

## 2026-09-15 &mdash; Tag-driven installer validation

Record source: [a4f507f / VALIDATION.md](https://github.com/lee-lab-skku/wr-ppp/blob/a4f507f843af9566cbb19e8146f9e89adb90d782/windows/VALIDATION.md).
The original record did not identify the exact tested commit or a CI run.

### Added

- Validate the tag-driven Windows installer pipeline, including offline operation and installation/uninstallation checks.

### Validation

The scripts used by the tag-push workflow were tested on Windows 11 x64 with PowerShell 5.1 and CPython 3.13.7.

- Passed 58 Windows tests and 19 common tests; skipped 31 POSIX-only tests on Windows.
- Used real PowerShell processes to verify selection of the triggering tag when multiple tags exist and rejection of dirty checkouts.
- Passed 95 common/POSIX tests on WSL Ubuntu 24.04 using a source copy that preserved symbolic links and executable permissions.
- Validated GitHub Actions workflow syntax with actionlint 1.7.12.
- Installed required packages in a fresh project-local TinyTeX and built Korean reports and administrator draft/final bundles.
- Generated the offline installer and SHA256 using checksum-verified Inno Setup 6.7.3; the local development installer was 489,314,308 bytes.
- Built the English template PDF using only the sanitized portable executable and bundled TeX, and passed hidden GUI and resource self-checks.
- Performed an unattended installation into a path containing spaces on a machine without an existing installation, and verified version and per-user uninstall registration.
  Built a Korean PDF and ran hidden GUI self-checks with development Python/TeX excluded from PATH, then verified that uninstall removed the application and registration while preserving user configuration and PDFs.
- Tested release metadata, checksums, prerelease settings, draft retry after an upload failure, and preservation of published assets with GitHub transport substituted.

Actual hosted Linux/macOS/Windows runners and Release publication remained to be checked after a tag push.
This validation did not change the repository version or create or push a release tag.

## 2026-09-15 &mdash; PowerShell launcher refactor

Record source: [a4f507f / VALIDATION.md](https://github.com/lee-lab-skku/wr-ppp/blob/a4f507f843af9566cbb19e8146f9e89adb90d782/windows/VALIDATION.md).
The original record did not identify the exact tested commit or a CI run.

### Changed

- Exercise native PowerShell launchers and packaging boundaries while preserving configuration, argument handling, and publication contracts.

### Validation

These results describe the PowerShell refactor at that time, separately from the earlier implementation.
Environment: Windows 11 x64, Windows PowerShell 5.1, CPython 3.13.7, pypdf 6.18.0, and PyInstaller 6.21.0.

- Passed 57 Windows tests: 55 application-logic tests and two real PowerShell process tests.
- Passed nine common Slack tests; POSIX-only classes and modules were explicitly skipped on Windows.
- Passed 85 common/POSIX tests on WSL Ubuntu 24.04.
  Used an equivalent source copy with Git's symbolic-link modes and executable permissions, rather than Windows Git's plain-file link substitutes.
- Checked PowerShell invocation from another working directory, Korean/space/bracket/ampersand paths, repeat installation, preservation of non-Windows virtual environments, empty arguments, quotes, trailing backslashes, UNC strings, and preservation of `WR_CONFIG` and exit codes.
- Checked configuration preflight, repair of invalid saved paths, skill-alias deduplication, protection of concurrent user changes, publication locks, source revalidation after waiting, and detection of interruption between PDF and record replacement.
- Used the existing `C:\texlive\2026` installation to build the two-page English template, a one-page Korean form report, and administrator draft/final bundles.
  Rendered both template pages, the Korean form report, and the bundle cover to PNG for inspection.
- Built a two-page A4 PDF with Windows Docker's `danteev/texlive:latest`, using the same template, style, and metadata.
  The build disabled networking and used a read-only source mount and temporary working storage.
- Checked input and saving in a hidden Tk GUI, GUI/CLI executable packaging, executable self-checks, and the bundled version file.

Project-local TinyTeX and Inno Setup were unavailable for this pass, so fresh TinyTeX installation, `-IncludeTeX` offline operation, and installer creation, installation, and uninstallation were not revalidated.
TinyTeX is not included with Python itself; offline installers bundle a separately prepared TeX distribution.
PowerShell 7, real UNC/NAS access and ACLs, macOS, external AI service link discovery, and real Slack delivery were not tested.
Docker Desktop integration was disabled for the WSL distribution, so this pass did not run an actual Docker build inside that distribution.

## 2026-09-15 &mdash; Distribution cleanup review

Record source: [a4f507f / RELEASE-CHECKS.md](https://github.com/lee-lab-skku/wr-ppp/blob/a4f507f843af9566cbb19e8146f9e89adb90d782/windows/RELEASE-CHECKS.md).
The original record did not identify the exact tested commit or a CI run.

### Changed

- Remove development-machine traces from distribution resources and review tracked and bundled artifacts.

### Validation

- Reviewed tracked files and new source files for developer profile names, personal email addresses, private keys, common access-token formats and Slack webhook URLs.
  No real credentials or personal profile data were detected in the source candidate set.
  Webhook URLs in tests are explicit dummy values.
- Local configuration, Python environments, report output, temporary files, build tools, executables and signing keys are excluded from Git.
- Removed generated TinyTeX logs, font caches and unused non-XeTeX format dumps.
  Removed developer paths from generated comments and made font directories relative to the bundled font configuration.
- Scanned the distribution, including decompressed gzip format data, for the developer profile/email and common credential patterns.
  No remaining matches were detected after cleanup.
  This is a targeted privacy check, not a guarantee against every possible secret or third-party binary issue.
- The earlier record recommended a GitHub noreply author/committer email for release commits; current commit attribution follows the repository contribution policy.

## 2026-09-14 &mdash; Initial installer validation

Record source: [a4f507f / VALIDATION.md](https://github.com/lee-lab-skku/wr-ppp/blob/a4f507f843af9566cbb19e8146f9e89adb90d782/windows/VALIDATION.md).
The original record did not identify the exact tested commit or a CI run.

### Added

- Package and exercise the earlier native installer; the artifact filename below is historical evidence, not a Windows version policy.

### Validation

- Generated `WeeklyReport-0.1.0-Setup.exe` with Inno Setup 6.7.3: 527,593,901 bytes.
  A SHA256 file was also generated.
- Rebuilt the PyInstaller distribution from the source available at the time.
  Passed 46 Windows unit tests.
- Installed successfully for the current user at the time.
  Verified the desktop shortcut target, Start menu shortcut, uninstaller, and Windows uninstall registration.
- Used the installed executable's self-check to verify GUI creation, PDF library loading, and template resource loading.
- Generated an actual PDF using the installed executable and bundled TinyTeX with development Python/TeX excluded from PATH.
- Left the installation on the validation PC at the time.
  Other PCs, uninstallation, and code signing were not tested.

## Undated &mdash; Earlier native implementation

Record source: [a4f507f / VALIDATION.md](https://github.com/lee-lab-skku/wr-ppp/blob/a4f507f843af9566cbb19e8146f9e89adb90d782/windows/VALIDATION.md).
The original record did not identify the exact tested commit or a CI run.
Its execution date was not recorded; no date or repository release has been inferred.

### Added

- Exercise native report creation, administrator workflows, GUI persistence, and portable distribution.

### Validation

Validation environment: Windows 11 x64, Python 3.14.7 (MinGW), PyInstaller 6.21.0, pypdf 6.18.0, and Windows TinyTeX/TeX Live 2026.

#### Verified Scope

- Automated Windows module checks covered reporting weeks across month/year boundaries, plain-text escaping and `$...$`/`$$...$$` math preservation, PDF inspection and encrypted-file rejection, path boundaries, serial numbers, output preservation on failure, member configuration, candidate selection, complete-page and page-size preservation, history hashes, draft/final separation, approval invalidation after source content or timestamp changes, storage conflicts, skill installation conflicts and rollback, and Slack deduplication.
- Passed eight common Slack tests with substituted transport and no real delivery.
- Skipped 26 POSIX shell tests on Windows.
  The shell implementation was unchanged, and this did not replace Linux/macOS execution checks.
- Checked Tk report-form creation, Korean input, and report-data saving.
- Created PyInstaller GUI/CLI executables and ran hidden GUI, PDF library, and template-loading self-checks.
- Checked the runtime environment and generated a Korean PDF using only the offline distribution's `WeeklyReportCLI.exe` and bundled `tex` directory, with development Python, MSYS, and existing TeX excluded from PATH.
- Built the English `template.tex` with native Windows XeLaTeX: two pages.
- Built a form-generated report containing Korean text, special characters, a table, and a PNG figure: one page.
- Built an administrator cover and combined source PDFs, displayed prior-week history and current missing submissions, and exercised draft &rightarrow; review record &rightarrow; final generation.
- Rendered the PDF pages to PNG to inspect text, tables, figures, and the bundle cover.

#### Unverified Scope

- Real NAS connectivity, ACLs, and concurrent user access.
- Real Slack delivery and external AI service skill discovery.
- Other Windows PCs, Windows ARM, and code signing.
- Arbitrary user LaTeX extensions and custom build stages involving BibTeX/Biber or user latexmk configuration.

Native builds used temporary copies and disabled shell escape, without providing Docker's OS or network isolation.
The Docker path remained available.
Existing skill policies for evidence assessment and writing were preserved, and no AI API was embedded in the application.

The actual-build checks are in `tests/real_build.py`, with visual-inspection support in `tests/render_qa.py`.
Generated validation reports are explicit test fixtures, not research results.

## Undated &mdash; Earlier release checks

Record source: [a4f507f / RELEASE-CHECKS.md](https://github.com/lee-lab-skku/wr-ppp/blob/a4f507f843af9566cbb19e8146f9e89adb90d782/windows/RELEASE-CHECKS.md).
The original record did not identify the exact tested commit or a CI run.
Its execution date was not recorded; no date or repository release has been inferred.

### Changed

- Check the sanitized distribution and installer on the development machine.

### Validation

- Windows native tests: 46 passed.
- Common tests: 8 passed; 26 POSIX-only tests skipped on Windows.
- The Slack manifest fixture explicitly uses UTF-8 so tests work with the Windows locale.
- The sanitized distribution generated a Korean PDF successfully with development Python/TeX excluded from PATH.
- Installer and shortcuts were tested on the development Windows PC.
  A separate clean PC, Windows ARM and uninstallation remain untested; the installer is unsigned.
