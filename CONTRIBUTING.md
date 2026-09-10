# Contributing

Thank you for contributing to the weekly research report template.
Keep changes focused, preserve the existing report workflow, and read `README.md` before changing user-facing behavior.

## Compatibility and Ownership

Treat documented setup, build, output, LaTeX, and skill behavior as stable by default.
A deliberate breaking change should explain its rationale and impact, update the relevant documentation in the same change, and provide migration guidance when users must take action.

Use the repository sources according to their roles:

- `README.md` defines shared report policy and describes the user workflow.
- The files under `scripts/` implement setup and build behavior.
- The files under `skills/` define agent workflows and safeguards, with task-specific procedures in selectively loaded references.
- `weekly-report.sty` defines the shared LaTeX interfaces and presentation.
- `template.tex` provides contextual writing prompts and an adaptable worked example.

Install command and skill links to canonical repository sources rather than generating duplicate implementations.
Routine report content should not require changes to the template, style, or shared build scripts.

Apply the [shared setup destination policy](README.md#quick-start) to command and skill links, preserving idempotency, explicit replacement, directory protection, and preflight before mutation.
Normalize supported destination aliases before checking for duplicates.

## Shell and Build Safety

Write shell scripts for both Linux and macOS whenever practical.
Bash is the project shell, and scripts should remain compatible with the Bash version shipped with macOS.
Avoid features that require newer Bash releases unless the project requirements are updated explicitly.

Linux commonly provides GNU command-line utilities, while macOS provides BSD variants.
Avoid relying on implementation-specific flags or output formats.
If GNU and BSD tools require different invocations, detect the implementation and provide both paths in the script.
Do not require Homebrew packages merely to replace standard macOS utilities when a reasonable portable implementation is available.

macOS compatibility is a source-level design target, not a tested-platform guarantee.
Contributors should account for known macOS differences, but they are not required to own macOS hardware, run the scripts on macOS, or guarantee operation on every macOS and Docker Desktop version.
State any known limitation that remains after a change.

Quote path and variable expansions, preserve `set -euo pipefail` where it is already used, and resolve script-relative paths without assuming the caller's working directory.

Preserve the builds' isolation and output-safety properties.
TeX containers run without network access and compile in temporary storage.
A completed PDF should replace its target only after a successful build and validation, and containers must not modify source files.

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
Both skills should remain usable through the supported Codex and Claude links; avoid provider-specific instructions unless they are necessary and clearly scoped.

Keep skill behavior adaptive, evidence-grounded, protective of existing user work, and limited to authorized actions.
When its capabilities or expectations change, update the entry point, affected references, and the user-facing AI workflow documentation together as applicable.

## Validation

When changing report guidance, skills, or the illustrative template, validate against the [shared report policy](README.md#write-the-report) and [AI-assisted workflow](README.md#ai-assisted-workflow).
Page-limit exceptions belong in the authoring and review judgment, with a specific necessity rationale; deterministic builders must preserve complete content rather than truncate reports.

Validate in proportion to the change and its risks.
Exercise the affected workflow and relevant error behavior, confirm documentation against the canonical sources, and compile the example when build or LaTeX behavior changes.
Skill changes should cover representative activation, reference routing, all shared repository-resolver entry points, and affected report tasks.

Run the administrator workflow regression checks with `python3 -B -m unittest discover -s tests -v` (Python 3 standard library only).
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
- Increment MINOR for backward-compatible functionality, including a new LaTeX interface, command option, setup capability, or skill capability, and when deprecating public functionality without removing it.
- Increment PATCH for backward-compatible bug fixes, portability and safety corrections, documentation corrections, and internal changes that do not alter the documented interface.

Compatibility means that documented usage continues to work with its stated semantics; it does not require byte-identical PDFs or prevent presentation refinements that preserve those semantics.

Maintain `CHANGELOG.md` using the Keep a Changelog structure.

Begin every changelog item with the most relevant component marker: `[latex]`, `[template]`, `[build]`, `[setup]`, `[skill]`, or `[docs]`.
Describe notable user-facing differences rather than copying the commit log, and combine closely related commits into one entry when they deliver one change.

If you are an AI agent, do not increment the version or create a release tag without explicit developer confirmation.
Versions are recorded by Git tags named `vMAJOR.MINOR.PATCH`.
For every confirmed release, move the relevant changelog entries from `Unreleased` into a dated version section, update the version comment at the beginning of `template.tex`, commit those changes, and create the matching tag on that exact commit.
Confirm that the latest-version badge near the beginning of `README.md` remains configured to derive its value from the repository's SemVer tags.
Do not omit the changelog update, template update, badge check, or tag.

The setup and build scripts report the version derived from the current Git checkout.
A tagged release prints its tag, while later development commits may include a commit suffix and a dirty checkout may include `-dirty`.
The build always uses the current checkout; do not add a facility for selecting another repository version at build time.
