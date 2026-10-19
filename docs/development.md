# Development Guide

Start with [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution setup and the verification entry points.

## Responsibilities

Use the repository sources according to their roles:

- `README.md` introduces the user workflow; [the report policy](report-policy.md) defines shared authoring requirements, and [the documentation index](README.md) identifies the canonical guide for each topic.
- The files under `scripts/` implement Linux/macOS setup and build behavior; the [Windows guide](../windows/README.md) defines the native Windows entry points and workflow.
- The files under `skills/` define agent workflows and safeguards, with task-specific procedures in selectively loaded references.
- `weekly-report.sty` defines the shared LaTeX interfaces and presentation.
- `template.tex` provides contextual writing prompts and an adaptable worked example.

The Docker workflow is the primary report path; native Windows adapts shared capabilities to its GUI and build environment.
Keep HTML editing resources, local browser transport, and portable LaTeX conversion in `report_editor/`, without imports from `windows/` or a dependency on an Artifact provider.
The TeX adapter exposes editing through `scripts/report-edit` and leaves PDF compilation to `report-build`.
Windows retains its native application and owns form-model conversion and persistence through an adapter to the common editor.
Keep one HTML source and one implementation of each conversion tool; root script entry points delegate to the shared package.
Preserve the source-backed editor contract: no-op exports must retain every source byte, and supported edits must leave unrelated spans intact.
Keep lexical scanning, protected source regions, stable figure identities, and lossless export in the shared package; the native form adapter retains ownership of its own model.
Do not execute TeX or expand external inputs to discover editable regions.
Ambiguous boundaries and unsupported syntax are read-only; reject operations that cross protected boundaries or discard their content.
Similarity scores are diagnostic, never permission to discard source.
State format version 2 optionally carries immutable preservation metadata; retain legacy JSON loading without claiming recovery of absent source.
Browser saves carry a revision and state snapshot; serialize writes, reject stale revisions, and mark only acknowledged snapshots clean.
Adapters must check destination fingerprints under a publication lock before writing; conflicts must preserve the newer file.

Install command and skill links to canonical repository sources rather than generating duplicate implementations.
Keep Linux/macOS operational command implementations in root `scripts/`; expose them from `skills/*/scripts/` through relative links rather than placing the canonical implementation inside a skill.
Skill-specific templates and procedural references may remain with the skill; resolve their paths from the repository root so commands work through either entry point.
Keep development-only checks in `tests/`, with names that identify their scope; preserve a documented older command with a thin wrapper when needed.
Source launchers and test entry points prepare Python import paths; importing a library package must not modify `sys.path`.
Routine report content should not require changes to the template, style, or shared build scripts.

Apply the [shared setup destination policy](setup.md#install) to command and skill links, preserving idempotency, explicit replacement, directory protection, and preflight before mutation.
Normalize supported destination aliases and deduplicate requested destinations, preserving their first occurrence.
Preflight every requested link's parent path and validate final administrator path settings with the shared path helper before changing installation state.
Prepare private configuration separately and commit it atomically only after link installation succeeds.
Journal link changes for reverse-order rollback on failure; preserve existing configuration and never overwrite an unrelated entry during rollback.
If restoration fails, report the backup path and remaining partial changes.

## Shell and Build Safety

Write shell scripts for both Linux and macOS whenever practical.
Bash is the Linux/macOS automation shell, and those scripts should remain compatible with the Bash version shipped with macOS.
Avoid features that require newer Bash releases unless the project requirements are updated explicitly.
Guard expansions of possibly empty arrays with `${items[@]+"${items[@]}"}`: Bash 3.2 treats a direct empty-array expansion as unset under `set -u`, and substituting one empty argument changes command behavior.

Linux commonly provides GNU command-line utilities, while macOS provides BSD variants.
Avoid relying on implementation-specific flags or output formats.
If GNU and BSD tools require different invocations, detect the implementation and provide both paths in the script.
Do not require Homebrew packages merely to replace standard macOS utilities when a reasonable portable implementation is available.

macOS compatibility is a source-level design target, not a tested-platform guarantee.
Contributors should account for known macOS differences, but they are not required to own macOS hardware, run the scripts on macOS, or guarantee operation on every macOS and Docker Desktop version.
State any known limitation that remains after a change.

Quote path and variable expansions, preserve `set -euo pipefail` where it is already used, and resolve script-relative paths without assuming the caller's working directory.

Preserve the builds' isolation and output-safety properties.
Linux/macOS TeX containers run without network access and compile in temporary storage.
A completed PDF should replace its target only after a successful build and validation, and containers must not modify source files.

Windows must preserve the shared report policy, plan/manifest formats, publication safety, and skill destination aliases.
Native Windows builds do not provide container OS/network isolation, and Windows updates remain manual.
Follow the [Windows development guide](../windows/CONTRIBUTING.md) for implementation constraints and platform-specific validation.

Keep POSIX scripts as LF text through `.gitattributes` so Windows checkouts remain usable from WSL.
When Windows Git materializes repository symlinks as plain files (`core.symlinks=false`), run POSIX checks in a Linux checkout that preserves the Git symlink modes; line-ending normalization alone cannot restore links.
Validate report readability and a positive page count with container-provided `pdfinfo`; keep PDF tooling off the host.
Use the shared PDF publisher for user-facing PDFs: stage and verify bytes in the destination directory, atomically replace without a deletion gap, and update mtime for file watchers.
A timestamp-update error occurs after replacement and must be reported as such; bundle publication must still complete its matching execution record.
Do not use in-place truncation or pre-build deletion to refresh a viewer.

### Automatic Updates

See the [automatic release update workflow](setup.md#automatic-release-updates) for setup options, update intervals, and recovery.
Keep development clones opted out; enabling updates authorizes release checkout changes during builds.
Implement version selection with Bash and standard utilities without new language runtimes or package dependencies, retaining the existing Linux/macOS source-level compatibility target.

Validate build arguments and inputs before invoking automatic updates or touching output PDFs.
Use only eligible tags advertised by the existing origin remote and verify the fetched commit against that advertisement.
Never force-update conflicting tags, discard tracked changes, or move to a commit that does not contain the current HEAD.
Preserve branches when switching to a release, retain report arguments and configuration, and restart with the updated build implementation.
Keep update status on stderr and leave the PDF output contract intact.

Persist check state as data rather than shell code, write it atomically, and invalidate it when the channel changes.
Hold an installation-wide directory lock through the refreshed build, recheck state after acquiring it, and release it on ordinary exit or handled signals.
Bound lock and network waits, preserve active locks, and continue with the existing checkout on update failures when no concurrent update lock prevents a consistent build.
Tests must use local Git remotes and substituted network/build dependencies without updating a real installation or contacting publication remotes.

## Editing AI Skills

Use this order of reference when updating `skills/wr-wr` or `skills/admin-wr`:

1. Read the selected skill's `SKILL.md` and the reference file governing the behavior being changed.
1. Consult [the shared report policy](report-policy.md), `template.tex` for contextual writing guidance, and the scripts and `weekly-report.sty` for exact build and LaTeX behavior.
   Preserve these ownership boundaries when updating skills.
1. Follow current Codex and Claude skill conventions for platform mechanics without overriding repository behavior.

Keep `SKILL.md` focused on activation scope, task routing, cross-cutting safeguards, and completion behavior.
Put task-specific procedures and safeguards in the relevant file under `references/`, and keep deterministic repository-location logic in the shared `scripts/resolve-repo-root`.
Prefer extending an existing reference over adding a new one unless the change introduces a distinct concern.

For report content work, the writing skill must explicitly direct agents to read the canonical template comments and shared report policy.
Keep the comments focused on writing decisions at each location, and distinguish requirements, adaptable suggestions, and illustrative content.
Avoid duplicating section-writing prescriptions in skill references or treating the example's organization as a requirement.
Treat [report conventions](../skills/wr-wr/references/report-conventions.md), [content quality](../skills/wr-wr/references/content-quality.md), and [LaTeX and build support](../skills/wr-wr/references/latex-and-build.md) as the canonical procedures for comment preservation, evidence, editorial stages, and report validation.
Keep the README's AI-assisted workflow section focused on capabilities and links to those references.

When editing `admin-wr`, preserve the responsibility boundary defined in [Administrator Development](admin-development.md) rather than moving judgment into deterministic scripts.
Changes to the plan or execution-manifest formats must update the workflow reference, tests, and user documentation together.

Do not duplicate the repository's full interfaces in a skill.
Refer to the canonical sources when exact behavior matters so that skill guidance does not become a stale parallel manual.
Both skills should remain usable through all supported installation destinations; avoid provider-specific instructions unless they are necessary and clearly scoped.

Keep skill behavior adaptive, evidence-grounded, protective of existing user work, and limited to authorized actions.
When its capabilities or expectations change, update the entry point, affected references, and the user-facing AI workflow documentation together as applicable.

## Validation

When changing report guidance, skills, or the illustrative template, validate against the [shared report policy](report-policy.md) and [authoring procedures](../skills/wr-wr/references/content-quality.md).
Page-limit exceptions belong in the authoring and review judgment, with a specific necessity rationale; deterministic builders must preserve complete content rather than truncate reports.

Validate in proportion to the change and its risks.
For shared editor changes, exercise both the TeX and Windows form adapters with `python3 -B -m unittest discover -s tests -p 'test_editor.py' -v`.
Run `python3 tests/check_editor_geometry.py`, `node tests/test_inline_render.js`, and `python3 tests/check_editor_browser.py` for layout constants, inline rendering, and browser behavior respectively; the browser check needs Chrome/Chromium or native Windows Edge (`WR_BROWSER` overrides discovery).
Run `node tests/test_editor_saves.js` for controlled save ordering and `python3 tests/check_preservation_browser.py` for the live source-backed editor, persistence, and undo/redo.
The former browser-check path `tests/run_tests.py` is now `tests/check_editor_browser.py`; `scripts/verify_geometry.py` remains a compatibility entry point for the geometry check.
Common Python tests use only the standard library, including local HTTP requests, and do not compile TeX or open a browser.
Exercise the affected workflow and relevant error behavior, confirm documentation against the canonical sources, and compile the example when build or LaTeX behavior changes.
Skill changes should cover representative activation, reference routing, all shared repository-resolver entry points, and affected report tasks.

Run the administrator workflow regression checks with `python3 -B -m unittest discover -s tests -v` (Python 3 standard library only).
On native Windows, use `windows/test.ps1` for native tests and common checks; POSIX-only checks must run separately in WSL/Linux.
Use the [Windows validation guidance](../windows/CONTRIBUTING.md#validation) for additional platform checks.
These checks use isolated repositories and substitute Docker and desktop openers to exercise artifact placement, failure handling, and platform command routing without publishing reports or opening windows.
Also exercise a real Docker build when available; substituted commands do not validate TeX rendering or a desktop viewer.

Document checks that were not run when they would otherwise be relevant.
Do not claim macOS compatibility was verified unless the affected workflow was actually exercised on macOS, and identify any supported agent service that was not exercised when the distinction matters.
An unavailable macOS or agent environment does not by itself block a contribution.

## Documentation and Scope

When editing root documents or shared guides under `docs/`, treat the Windows implementation as a black box by default.
Describe its supported capabilities, inputs and outputs, observable behavior, compatibility, and repository-wide contracts without requiring readers to understand its internal components.
Keep Windows-specific architecture, implementation rules, and dependency or packaging procedures in the [Windows development guide](../windows/CONTRIBUTING.md), and link there when detail is needed.
Use `windows/README.md`, `windows/CONTRIBUTING.md`, and `windows/CHANGELOG.md` as the three Windows documentation entry points.
Their roles mirror the root documents: user guidance, durable contributor guidance, and internal change history with relevant validation evidence.
Keep Windows internals that cannot be adequately described through the root documents' external perspective in these subordinate documents, and link to root policy instead of duplicating it.
The Windows changelog supplements the root history using dated change groups linked to commits or PRs, with relevant validation recorded alongside them; it must not introduce independent version numbers or release authority.
Keep its detailed entry conventions in [the Windows contribution guide](../windows/CONTRIBUTING.md#documenting-internal-changes).
Preserve the environment, scope, and limitations of historical validation when consolidating records; do not present past checks as verification of current source.
This perspective does not prohibit describing changes that are entirely internal: explain relevant improvements, their purpose, evidence, and limitations at the level appropriate to the root document, even when the public interface is unchanged.
For example, root documentation may describe faster CI dependency preparation or more reliable installation; the implementation and cache maintenance steps belong in the Windows guide.

Keep `README.md` and `CONTRIBUTING.md` concise entry points with essential setup, usage, and verification commands.
Update the relevant canonical guide when setup arguments, generated command behavior, required software, report-writing instructions, or user-visible skill capabilities change, and update the root entry point when its summary or links change.
Use the [documentation index](README.md) to locate topic ownership; move detailed material instead of maintaining duplicate manuals.
Keep administrator development contracts in [Administrator Development](admin-development.md) and operating procedures in the administrator references.
Limit the README's administrator section to a short pointer and basic setup options.

Keep commits limited to meaningful changes and explain user-visible behavior in the commit message.
Do not include generated PDFs or local configuration unless the contribution specifically requires updating a tracked artifact.
