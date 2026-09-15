# Contributing

Thank you for contributing to the weekly research report template.
Keep changes focused, preserve the existing report workflow, and read `README.md` before changing user-facing behavior.

## Compatibility and Ownership

Treat documented setup, build, output, LaTeX, and skill behavior as stable by default.
A deliberate breaking change should explain its rationale and impact, update the relevant documentation in the same change, and provide migration guidance when users must take action.

Use the repository sources according to their roles:

- `README.md` defines shared report policy and describes the user workflow.
- The files under `scripts/` implement Linux/macOS setup and build behavior; Windows PowerShell entry points implement native automation and delegate GUI and report operations to the Python implementation.
- The files under `skills/` define agent workflows and safeguards, with task-specific procedures in selectively loaded references.
- `weekly-report.sty` defines the shared LaTeX interfaces and presentation.
- `template.tex` provides contextual writing prompts and an adaptable worked example.

Install command and skill links to canonical repository sources rather than generating duplicate implementations.
Routine report content should not require changes to the template, style, or shared build scripts.

Apply the [shared setup destination policy](README.md#quick-start) to command and skill links, preserving idempotency, explicit replacement, directory protection, and preflight before mutation.
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

Windows automation uses PowerShell 5.1 or newer, with PowerShell 7 compatibility as a design target.
Use script-relative resource paths, literal filesystem operations, explicit native-process exit checks, and argument arrays without shell command construction.
Setup must be repeatable without prompts, preserve incompatible environments, and validate destinations before changing saved configuration or links.
Preserve caller environment variables and restore any temporary working-directory or environment changes.
Python owns the native GUI, LaTeX generation, PDF operations, and administrator rules; PowerShell must not duplicate those implementations.
The native backend uses temporary source copies and disables TeX shell escape, but does not provide container OS/network isolation.
Keep the shared report policy, plan/manifest formats, publication safety, and skill destination aliases consistent across platforms.
Directory publication locks cover both PDF and history destinations and revalidate source fingerprints after acquisition; never automatically steal a NAS lock.
The Git release updater remains specific to Bash; native Windows updates are manual.

Keep POSIX scripts as LF text through `.gitattributes` so Windows checkouts remain usable from WSL.
When Windows Git materializes repository symlinks as plain files (`core.symlinks=false`), run POSIX checks in a Linux checkout that preserves the Git symlink modes; line-ending normalization alone cannot restore links.
PowerShell scripts containing non-ASCII literals require UTF-8 with BOM for Windows PowerShell 5.1; otherwise keep their source ASCII.
Validate report readability and a positive page count with container-provided `pdfinfo`; keep PDF tooling off the host.
Use the shared PDF publisher for user-facing PDFs: stage and verify bytes in the destination directory, atomically replace without a deletion gap, and update mtime for file watchers.
A timestamp-update error occurs after replacement and must be reported as such; bundle publication must still complete its matching execution record.
Do not use in-place truncation or pre-build deletion to refresh a viewer.

### Automatic Updates

See the [automatic release update workflow](README.md#automatic-release-updates) for setup options, update intervals, and recovery.
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

## Administrator Weekly Bundles

See the [administrator setup](README.md#install-administrator-mode), [manager manifest](skills/admin-wr/references/manager-manifest.md), and [rollup workflow](skills/admin-wr/references/rollup-workflow.md) for installation, configuration schema, discovery, review, and artifact formats.
Preserve the following contracts when changing this workflow.

### Setup and Storage

`--admin` requires `--skills`; `--admin-data` requires `--admin`.
Administrator output and metadata paths must be absolute or begin with `~/`.
Omitting `--admin-output` preserves the saved output location and allows an unconfigured first installation; final promotion requires an output location, but discovery and drafts do not.
Setup must not create the final output directory.

An administrator setup without `--admin-data` selects repository-local metadata, even if a previous setup saved an external directory.
Setup without `--admin` preserves the saved metadata directory, and empty or absent `ADMIN_DATA_DIR` means local storage.
Changing configuration must not copy or move existing metadata.
Create manifest parent directories as needed, but defer execution-history directory creation until a final build.

Create a missing manager manifest under `umask 077`, requesting mode `0600`.
Do not require a subsequent `chmod`: NAS filesystems may allow creation while rejecting POSIX permission changes, with effective access governed by server permissions or ACLs.
Preserve an existing regular manifest or valid symbolic link regardless of `--replace-existing`, reject a conflicting directory, and never infer member or storage values.

Use the shared metadata resolver for reads and final history destinations.
Fallback applies only to missing files, per week for history; existing invalid content or PDF hashes must be diagnosed rather than bypassed.
Reads must not move or delete metadata, and final writes must use the configured destination or its unconfigured local default even when reads used fallback.
Preserve lookup compatibility with repository-local and legacy history so migration remains optional.

### Responsibility and Artifact Safety

Keep candidate selection, evidence assessment, issue classification, and approval decisions in the agent workflow.
The deterministic builder consumes an explicit plan and selected PDFs; it must not discover reports, parse the manager configuration, or judge evidence.
Keep shared helpers canonical across command and skill entry points.

Restrict discovery to declared member roots without following directory symlinks or escaping storage.
Report filenames, internal labels, and templates must remain unrestricted; source PDFs must never be modified or deleted.
Preflight must distinguish host, Docker access, image dependency, and runtime failures while preserving the underlying error.
Keep PDF inspection dependencies in the configured container rather than requiring host Poppler tools.

Preserve all selected source pages and their aspect ratios, manifest ordering, and a single-page A4 index with cumulative inclusion history.
Reject cover overflow instead of dropping history, and keep missing, exceptional, optional, and unknown states distinguishable.
The [rollup workflow](skills/admin-wr/references/rollup-workflow.md#write-the-temporary-plan) defines plan fields and cover presentation.

Keep review drafts and their records outside the final output directory and its descendants, available after the builder exits.
A viewer opening is not approval; source or candidate changes invalidate the previous review.
Apply the workflow's approval conditions before promotion and revalidate source hashes before rebuilding the final bundle.

Validate the completed PDF before replacing final artifacts, using temporary files in each destination directory and atomic moves.
Serialize publication against both canonical PDF and execution-record destinations, using a fixed lock order and a bounded total wait.
Revalidate sources after acquiring the locks, hold them through both replacements, and release only locks acquired by the current run.
Preserve the builder's stdout contract: absolute PDF and execution-record paths, one per line in that order.
Drafts must never replace final history.
PDF and execution-record replacement is not a single transaction: an interruption between replacements must be detected through PDF-hash validation on the next run and require approval.

## Slack Hold Notifications

See the [Slack setup and operation guide](skills/admin-wr/references/slack-notifications.md) for configuration, commands, and recovery procedures.
The command requires Python 3 with the standard library only.

Keep hold decisions and notification authorization in the agent workflow, separate from deterministic PDF building.
A draft or approval request is not a decision to hold.
Preview by default; sending requires explicit destination authorization, a hold for missing required reports, and both `--held` and `--send`.
Use the draft execution manifest as evidence and disclose only the target week, reporting period, and missing required members.
Do not notify for optional omissions, clean bundles, or already promoted bundles.

Accept webhook secrets through hidden terminal input and keep them out of command arguments, tracked files, logs, PDFs, and execution records.
Configuration must not send a message.
Protect secret files through filesystem access controls without requiring post-creation `chmod` on NAS storage.
Read secrets only from the configured location; fallback could send to a different channel.

Deduplicate successful notices by target week, missing-member IDs, and webhook destination.
Serialize identical sends and recheck the receipt after acquiring the lock.
A failed or interrupted send must retain the lock and never retry automatically because delivery might already have occurred.
Slack failure must not publish a held bundle, modify execution history, or claim successful notification.
Use plain-text message blocks to prevent injected mentions or formatting, HTTPS Slack endpoints without redirects, bounded response reads, and a network timeout.
Tests must substitute transport and never send to Slack.

## Editing AI Skills

Use this order of reference when updating `skills/wr-wr` or `skills/admin-wr`:

1. Read the selected skill's `SKILL.md` and the reference file governing the behavior being changed.
1. Consult `README.md` for shared report policy, `template.tex` for contextual writing guidance, and the scripts and `weekly-report.sty` for exact build and LaTeX behavior.
   Preserve these ownership boundaries when updating skills.
1. Follow current Codex and Claude skill conventions for platform mechanics without overriding repository behavior.

Keep `SKILL.md` focused on activation scope, task routing, cross-cutting safeguards, and completion behavior.
Put task-specific procedures and safeguards in the relevant file under `references/`, and keep deterministic repository-location logic in the shared `scripts/resolve-repo-root`.
Prefer extending an existing reference over adding a new one unless the change introduces a distinct concern.

For report content work, the writing skill must explicitly direct agents to read the canonical template comments and shared report policy.
Keep the comments focused on writing decisions at each location, and distinguish requirements, adaptable suggestions, and illustrative content.
Avoid duplicating section-writing prescriptions in skill references or treating the example's organization as a requirement.
Refer to the [README's AI-assisted workflow](README.md#ai-assisted-workflow) for comment preservation and authoring behavior; keep detailed task procedures in skill references.

When editing `admin-wr`, preserve the responsibility boundary defined in [Administrator Weekly Bundles](#administrator-weekly-bundles) rather than moving judgment into deterministic scripts.
Changes to the plan or execution-manifest formats must update the workflow reference, tests, and user documentation together.

Do not duplicate the repository's full interfaces in a skill.
Refer to the canonical sources when exact behavior matters so that skill guidance does not become a stale parallel manual.
Both skills should remain usable through all supported installation destinations; avoid provider-specific instructions unless they are necessary and clearly scoped.

Keep skill behavior adaptive, evidence-grounded, protective of existing user work, and limited to authorized actions.
When its capabilities or expectations change, update the entry point, affected references, and the user-facing AI workflow documentation together as applicable.

## Validation

When changing report guidance, skills, or the illustrative template, validate against the [shared report policy](README.md#write-the-report) and [AI-assisted workflow](README.md#ai-assisted-workflow).
Page-limit exceptions belong in the authoring and review judgment, with a specific necessity rationale; deterministic builders must preserve complete content rather than truncate reports.

Validate in proportion to the change and its risks.
Exercise the affected workflow and relevant error behavior, confirm documentation against the canonical sources, and compile the example when build or LaTeX behavior changes.
Skill changes should cover representative activation, reference routing, all shared repository-resolver entry points, and affected report tasks.

Run the administrator workflow regression checks with `python3 -B -m unittest discover -s tests -v` (Python 3 standard library only).
On native Windows, use `windows/test.ps1` for native tests and common checks; POSIX-only checks must run separately in WSL/Linux.
Use `-RealBuild`, `-Gui`, and `-Package` for the opt-in native TeX, hidden GUI, and offline EXE checks described in `windows/README.md`.
These checks use isolated repositories and substitute Docker and desktop openers to exercise artifact placement, failure handling, and platform command routing without publishing reports or opening windows.
Also exercise a real Docker build when available; substituted commands do not validate TeX rendering or a desktop viewer.

Document checks that were not run when they would otherwise be relevant.
Do not claim macOS compatibility was verified unless the affected workflow was actually exercised on macOS, and identify any supported agent service that was not exercised when the distinction matters.
An unavailable macOS or agent environment does not by itself block a contribution.

## Documentation and Scope

Update `README.md` when setup arguments, generated command behavior, required software, report-writing instructions, or user-visible skill capabilities change.
Keep administrator development contracts in this document and operating procedures in the administrator references.
Limit the README's administrator section to a short pointer and basic setup options.

Keep commits limited to meaningful changes and explain user-visible behavior in the commit message.
Do not include generated PDFs or local configuration unless the contribution specifically requires updating a tracked artifact.

## Versioning and Releases

Use Semantic Versioning for the repository as a whole.
The public interface is the union of the documented LaTeX commands and environments, setup and build commands, output semantics, template usage, and skill behavior.
Determine a release increment from every changed public surface and apply the highest required increment:

- Increment MAJOR for any backward-incompatible public-interface change, such as removing or changing a documented LaTeX interface, command option, default, or output behavior in a way that requires user migration.
- Increment MINOR for backward-compatible additions or changes to substantive functionality, including a new LaTeX interface, setup capability, or skill capability, and when deprecating public functionality without removing it.
  A new command option requires MINOR only when it introduces substantive functionality.
- Increment PATCH for backward-compatible bug fixes, portability and safety corrections, documentation corrections, and internal changes that do not alter the documented interface.
  Also use PATCH for new options, accepted values, or aliases that expose existing behavior without adding or changing substantive functionality, such as supporting another agent through the existing skill-link installation mechanism.

Compatibility means that documented usage continues to work with its stated semantics; it does not require byte-identical PDFs or prevent presentation refinements that preserve those semantics.

Maintain `CHANGELOG.md` using the Keep a Changelog structure.

Begin every changelog item with the most relevant component marker: `[latex]`, `[template]`, `[build]`, `[setup]`, `[skill]`, or `[docs]`.
Describe notable user-facing differences rather than copying the commit log, and combine closely related commits into one entry when they deliver one change.

If you are an AI agent, do not increment the version or create a release tag without explicit developer confirmation.
Versions are recorded by Git tags named `vMAJOR.MINOR.PATCH`, optionally followed by exactly `-beta` or `-rc` for prereleases.
Each numeric component is `0` or a positive decimal integer without leading zeroes.
Do not use other prerelease identifiers, numbered prereleases such as `-beta.1` or `-rc.2`, or build metadata in release tags.
Compare major, minor, and patch numerically, then order equal base versions as beta, release candidate, and official release.
Published tags are immutable; use the next allowed release stage or a new base version for subsequent publications rather than rewriting a tag.
For every confirmed release, move the relevant changelog entries from `Unreleased` into a dated version section, update the version comment at the beginning of `template.tex`, commit those changes, and create the matching tag on that exact commit.
Confirm that the latest-version badge near the beginning of `README.md` remains configured to derive its value from the repository's SemVer tags.
Do not omit the changelog update, template update, badge check, or tag.

The setup and build scripts report the version derived from the current Git checkout.
A tagged release prints its tag, while later development commits may include a commit suffix and a dirty checkout may include `-dirty`.
By default the build uses the current checkout; the optional automatic updater may advance it to an eligible published release before compilation.
This channel-based update is the supported exception; do not add arbitrary per-build version selection.

### Tag-driven CI and Windows Releases

`.github/workflows/release.yml` runs on pushed `v*` tags.
The validation job accepts only the release-tag grammar above, requires the tag and triggering commit to match the checkout, checks the version comment in `template.tex`, and requires exactly one matching dated changelog section with release notes.
Complete the normal release preparation before pushing the tag; CI does not create tags, increment versions, or edit source files.

Linux and macOS run the common/POSIX regression suite on their own hosted runners, using the operating system's `/bin/bash`.
These jobs substitute Docker and desktop viewers and do not build release artifacts or install TeX.
Windows uses PowerShell 5.1 for orchestration, runs the native/common tests (including PowerShell 7 checks when available), prepares project-local TinyTeX and the checksum-pinned Inno Setup compiler, tests native PDF generation, then builds the offline installer.
The sanitized portable bundle and the installed application must pass checks with development Python/TeX excluded from PATH; the installer check also verifies uninstallation preserves user configuration and PDFs.
Run the installer check only on a clean machine; it refuses an existing Weekly Report installation.

Only the publication job has `contents: write`, and it runs after every platform succeeds.
Use the repository's automatic `GITHUB_TOKEN`; no personal access token is required.
Organization/repository Actions policies must allow the pinned official actions and release-writing job permission.
Keep third-party action revisions pinned to full commit IDs and verify the official Inno Setup checksum when updating the compiler version.

CI packages the exact triggering tag even if multiple tags refer to the same commit.
The release contains only `WeeklyReport-<tag>-Setup.exe` and its `.exe.sha256` file; the publication job revalidates both after artifact transfer and uses the matching changelog section as release notes.
Tags ending in `-beta` or `-rc` produce prereleases and cannot become Latest; stable releases use GitHub's default Latest selection.
Publication uploads to a draft before making it public.
Retry a failed run using GitHub Actions' rerun controls: unpublished drafts for the same commit can resume, but published assets are never overwritten.
An existing complete published release is left unchanged; a published release missing expected assets or a draft targeting a different commit fails for maintainer review.
Preserve published tags and use a new allowed version when source fixes are needed.

TinyTeX follows the existing daily bootstrap and current TeX package repository; release builds are tested artifacts rather than byte-reproducible rebuilds.
Failures in dependency preparation, any test, checksum verification, or asset upload prevent publication.
Windows artifacts are retained in Actions for seven days; on failure, available installer/uninstaller logs from `.runtime/qa` are retained as a separate diagnostics artifact for the same period.
