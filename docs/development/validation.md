# Development Validation

Use this guide to select checks for the behavior changed and to report what those checks establish.
Commands and source paths are relative to the repository root.
Validate in proportion to the change and its risks.

## Report Guidance and Skills

When changing report guidance, skills, or the illustrative template, validate against the [shared report policy](../report-policy.md) and [authoring procedures](../../skills/wr-wr/references/content-quality.md).
Page-limit exceptions belong in the authoring and review judgment, with a specific necessity rationale; deterministic builders must preserve complete content rather than truncate reports.

Exercise the affected workflow and relevant error behavior, confirm documentation against the canonical sources, and compile the example when build or LaTeX behavior changes.
Skill changes should cover representative activation, reference routing, all shared repository-resolver entry points, and affected report tasks.

## Shared Editor

Select the checks for the affected editor behavior:

- **Adapters**: For shared editor changes, exercise both the TeX and Windows form adapters with `python3 -B -m unittest discover -s tests -p 'test_editor.py' -v`.
- **Rendering**: Run `python3 tests/check_editor_geometry.py`, `node tests/test_inline_render.js`, and `python3 tests/check_editor_browser.py` for layout constants, inline rendering, and browser behavior respectively; the browser check needs Chrome/Chromium or native Windows Edge (`WR_BROWSER` overrides discovery).
- **Persistence**: Run `node tests/test_editor_saves.js` for controlled save ordering and `python3 tests/check_preservation_browser.py` for the live source-backed editor, persistence, and undo/redo.
- **Command compatibility**: The former browser-check path `tests/run_tests.py` is now `tests/check_editor_browser.py`; `scripts/verify_geometry.py` remains a compatibility entry point for the geometry check.

## Common and Administrator Workflows

Common Python tests use only the standard library, including local HTTP requests, and do not compile TeX or open a browser.
Run the administrator workflow regression checks with `python3 -B -m unittest discover -s tests -v` (Python 3 standard library only).

On native Windows, use `windows/test.ps1` for native tests and common checks; POSIX-only checks must run separately in WSL/Linux.
Use the [Windows validation guidance](../../windows/CONTRIBUTING.md#validation) for additional platform checks.

These checks use isolated repositories and substitute Docker and desktop openers to exercise artifact placement, failure handling, and platform command routing without publishing reports or opening windows.
Also exercise a real Docker build when available; substituted commands do not validate TeX rendering or a desktop viewer.

## Reporting Limits

Document checks that were not run when they would otherwise be relevant.
Do not claim macOS compatibility was verified unless the affected workflow was actually exercised on macOS, and identify any supported agent service that was not exercised when the distinction matters.
An unavailable macOS or agent environment does not by itself block a contribution.
