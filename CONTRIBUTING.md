# Contributing

Thank you for contributing to the weekly research report template. Keep changes
focused, preserve the existing report workflow, and read `README.md` before
changing user-facing behavior.

## Compatibility and Ownership

Treat documented setup, build, output, LaTeX, and skill behavior as stable by
default. A deliberate breaking change should explain its rationale and impact,
update the relevant documentation in the same change, and provide migration
guidance when users must take action.

Use the repository sources according to their roles:

- `README.md` defines shared report policy and describes the user workflow.
- The files under `scripts/` implement setup and build behavior.
- The files under `skills/` define agent workflows and safeguards, with task-specific procedures in selectively loaded references.
- `weekly-report.sty` defines the shared LaTeX interfaces and presentation.
- `template.tex` provides contextual writing prompts and an adaptable worked example.

The `report-build` implementation lives in `scripts/report-build`;
`scripts/setup.sh` installs a link to that canonical script rather than
generating another copy. Routine report content should not require changes to
the template, style, or shared build scripts.

Keep system-command and agent-skill link installation on the shared setup
policy. Treat a link to the same source as an idempotent success, preserve
conflicting destinations by default, and require the explicit replacement
option before backing up and replacing a file or link. Never replace a
directory. Preflight every requested destination before changing the local
configuration or installing any link.

## Shell and Build Safety

Write shell scripts for both Linux and macOS whenever practical. Bash is the
project shell, and scripts should remain compatible with the Bash version
shipped with macOS. Avoid features that require newer Bash releases unless the
project requirements are updated explicitly.

Linux commonly provides GNU command-line utilities, while macOS provides BSD
variants. Avoid relying on implementation-specific flags or output formats. If
GNU and BSD tools require different invocations, detect the implementation and
provide both paths in the script. Do not require Homebrew packages merely to
replace standard macOS utilities when a reasonable portable implementation is
available.

macOS compatibility is a source-level design target, not a tested-platform
guarantee. Contributors should account for known macOS differences, but they
are not required to own macOS hardware, run the scripts on macOS, or guarantee
operation on every macOS and Docker Desktop version. State any known limitation
that remains after a change.

Quote path and variable expansions, preserve `set -euo pipefail` where it is
already used, and resolve script-relative paths without assuming the caller's
working directory.

Preserve the builds' isolation and output-safety properties.
TeX containers run without network access and compile in temporary storage.
A completed PDF should replace its target only after a successful build and validation, and containers must not modify source files.

## Administrator Weekly Bundles

Administrator mode is a maintainer workflow that installs the separate `admin-wr` skill alongside `wr-wr` for every service named by `--skills`:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest \
    --skills=agents,claude \
    --admin \
    --admin-output=/absolute/path/to/admin-bundles
```

`--admin` requires `--skills` because it changes which skills are installed.
The canonical shared skill destination is `agents` (`~/.agents/skills`); normalize the backward-compatible `codex` alias to `agents` before duplicate checks and installation.
Reject lists containing both names as duplicate destinations, while preserving the separate `claude` destination.
`--admin-output` is optional and accepts only an absolute path or a path beginning with `~/`.
If it is omitted, setup preserves any saved administrator output; a first installation without one succeeds and reports `Admin output: not configured`.
The administrator output directory is required only for final promotion and is not created merely by setup.

Use optional `--admin-data=<absolute-directory>` to store administrator metadata under one directory:

```text
<admin-data>/manager-manifest.toml
<admin-data>/manifests/<week>.manifest.tsv
```

This option requires `--admin` and accepts an absolute path or `~/` path, saved as `ADMIN_DATA_DIR` in `.local-config`.
If `--admin-data` is omitted on an administrator setup, use the existing local layout: `<repository>/.manager-manifest.toml` and `<repository>/.admin-wr/manifests/`, even if a previous setup saved an external directory.
Setup without `--admin` preserves the saved metadata directory.
Empty or absent `ADMIN_DATA_DIR` also means local storage, so existing configurations need no migration.
Setup creates the chosen manifest's parent directories as needed but leaves the execution-history directory uncreated until a final build.
It does not copy or move prior metadata when changing the configuration.

The first administrator-mode setup creates a manifest skeleton under `umask 077`, requesting mode `0600`; the default local manifest is Git-ignored.
Do not require a subsequent `chmod` for this newly created file: NAS filesystems may allow creation while rejecting POSIX permission changes, and their effective access is governed by server permissions or ACLs.
Setup must preserve an existing regular manifest or valid symbolic link regardless of `--replace-existing`, reject a conflicting directory, and never infer member or storage values.
Configure the manifest before discovery:

```toml
schema = 1
storage_root = "/absolute/path/to/report-storage"
timezone = "Asia/Seoul"

[[members]]
id = "member-a"
display_name = "구성원 가"
order = 10
required = true
search_roots = ["member-a"]

[[members]]
id = "member-b"
display_name = "구성원 나"
order = 20
required = true
search_roots = ["member-b/current-period"]
```

The manifest must use schema `1`, an absolute `storage_root`, an IANA timezone, and one or more members.
Member IDs and positive integer orders must be unique, and every member must have at least one search root.
Search roots are relative to `storage_root`; reject absolute roots, `..`, missing directories, directory-symlink components, and any physical resolution outside storage.
Different members may use different directory depths, and report filenames and templates remain unrestricted.

The agent recursively considers ordinary PDFs only inside each member's declared roots, uses NUL-delimited enumeration, excludes AppleDouble files, and never follows or expands through directory links.
It evaluates prior bundle records, file changes, filesystem and PDF timestamps, filename hints, extractable dates and authors, and possible revision relationships without treating any single signal as mandatory.
A missing internal week label, author header, or repository template is not an issue by itself.
A conflicting internal week remains `included` with an approval-requiring warning when the report identity, target-period evidence, and final candidate are otherwise clear; modification time alone is not sufficient evidence.
If other evidence also conflicts or competing candidates remain, use an `exception` and error instead.

Run `skills/admin-wr/scripts/admin-preflight` as a standalone command before discovery.
It distinguishes a missing Docker CLI, denied socket access, an unreachable daemon or environment integration, an absent local image, missing image dependencies, and container runtime failure while preserving the underlying Docker error.
The configured image must provide XeLaTeX, latexmk, `tar`, `pdfpages`, KoTeX, `pdfinfo`, and `pdftotext`; host Poppler tools are not required.

Probe each proposed source with `skills/admin-wr/scripts/probe-report` before writing the temporary plan.
The probe copies the PDF to temporary storage, runs without container networking, and reports its page count, encryption and creation metadata, extracted text, mtime, and SHA-256 without modifying the source.

The agent writes its proposed selections and issues to a temporary TSV plan.
For each selected report exceeding the two-page maximum per person per week, record an `overlength-report` warning with the page count and any specific necessity justification under the README's length policy.
An otherwise clear selection remains `included`, but the warning requires the existing draft review and approval; preserve all source pages and identify an unjustified excess as needing revision.
`skills/admin-wr/scripts/build-bundle` consumes only that plan and its explicit PDFs; it does not parse TOML or search storage.
It stages normalized PDF names, builds without container networking, verifies source hashes and page counts, and creates an A4 bundle whose first page is a fixed one-page index rather than an AI-written narrative.
The cover omits source page counts and ranges and adds a cumulative O/X inclusion table: weeks are rows in descending order, with this week first, and current members are columns in manifest order.
The agent supplies all earlier weeks from verified final records as optional `history` records in the existing plan schema; the builder renders those records without discovering or judging evidence.
Exceptions, optional omissions, and unknown history have distinct markers, and unknown cells require review.
All members share one table, with compact spacing and angled name headings; all weeks are retained, and the existing one-page cover check rejects overflow instead of dropping history.
See the [rollup workflow](skills/admin-wr/references/rollup-workflow.md#write-the-temporary-plan) for the additive plan and execution-history fields and legacy compatibility.
The remaining pages contain the selected reports in manifest order with their aspect ratios preserved.

Missing required reports, unresolved or weak candidate choices, unreadable PDFs, invalid prior bundle hashes, and first runs require approval.
The agent first writes a visibly marked draft outside the configured final directory and its descendants.
The builder prints a shell-quoted review command invoking `skills/admin-wr/scripts/open-bundle`, which opens the PDF using the desktop viewer on Linux, macOS, or WSL.
The agent runs it to show the draft and includes a clickable PDF path with the proposed choices and issues; an unavailable viewer leaves the path available for manual review.
Draft PDFs remain available after the builder exits, with their execution TSVs in the temporary review directory's `.manifests/` subdirectory.
After explicit approval it rechecks source hashes and rebuilds the final bundle, retaining distinct inclusion, missing, approved-exception, and optional-omission markers while removing the draft mark.
A user-selected replacement candidate requires a new draft and approval for every remaining issue.

Final artifacts use the canonical week label and separate output locations:

```text
<admin-output>/2026-09-W1.pdf
<admin-data>/manifests/2026-09-W1.manifest.tsv
```

Without `--admin-data`, the TSV destination is `<repository>/.admin-wr/manifests/2026-09-W1.manifest.tsv`.

The repository's `.admin-wr/` directory is Git-ignored; the default metadata layout keeps execution history out of the final PDF directory.
The builder continues to print the absolute PDF and TSV paths on stdout, one per line.
Use the shared `scripts/admin-paths` resolver, also exposed through the administrator skill, for read locations and the history write destination.
It prefers a configured metadata file, falls back to the repository-local file when absent, and finally considers legacy history beside final PDFs.
History fallback is per week, including when a configured directory exists but lacks that week's record.
Existing invalid files keep precedence and must be diagnosed; fallback cannot bypass failed content or PDF-hash validation.
Drafts never replace these records, and reads never move or delete them.
Final writes always use the configured destination (or the local default when unconfigured), even if reads used fallback.
Administrators may move prior TSVs into the configured history directory without overwriting newer records, but migration is not required for history lookup.
Resolve the manifest's PDF filename against the configured administrator output, not the manifest directory.
The execution manifest records the official date and period, completion and approval state, candidates, selection reasons, source paths relative to storage, mtimes, hashes, page ranges, missing members, and issue codes.
The builder validates the new PDF completely before using hidden temporary files in each artifact's destination directory and atomic moves to replace an existing week without a backup.
If only one artifact is replaced before an interruption, the next run must detect the PDF hash mismatch and require approval.
Source PDFs must never be modified or deleted.

The implementation is split across `skills/admin-wr` for agent behavior and deterministic assembly, root `scripts/` for administrator preflight and PDF probing, and `scripts/resolve-repo-root` for repository resolution shared with both skills.
The administrator skill exposes relative links to the root helper implementations so diagnostics and probing have one canonical source.

## Editing AI Skills

Use this order of reference when updating `skills/wr-wr` or `skills/admin-wr`:

1. Read the selected skill's `SKILL.md` and the reference file governing the behavior being changed.
1. Consult `README.md` for shared report policy, `template.tex` for contextual writing guidance, and the scripts and `weekly-report.sty` for exact build and LaTeX behavior.
   Preserve these ownership boundaries when updating skills.
1. Follow current Codex and Claude skill conventions for platform mechanics
   without overriding repository behavior.

Keep `SKILL.md` focused on activation scope, task routing, cross-cutting safeguards, and completion behavior.
Put task-specific procedures and safeguards in the relevant file under `references/`, and keep deterministic repository-location logic in the shared `scripts/resolve-repo-root`.
Prefer extending an existing reference over adding a new one unless the change introduces a distinct concern.

For report content work, the writing skill must explicitly direct agents to read the canonical template comments and shared report policy.
Keep the comments focused on writing decisions at each location, and distinguish requirements, adaptable suggestions, and illustrative content.
Avoid duplicating section-writing prescriptions in skill references or treating the example's organization as a requirement.
Retain references for source conventions and comment preservation, editorial judgment and evidence, and LaTeX and build validation.
For new reports, agents preserve retained instructional comments verbatim; only comments exclusive to omitted optional examples may be removed with those examples.
Existing reports are not automatically synchronized to new template comments, and new author-only notes remain separate.

When editing `admin-wr`, preserve the responsibility boundary defined in [Administrator Weekly Bundles](#administrator-weekly-bundles) rather than moving judgment into deterministic scripts.
Changes to the plan or execution-manifest formats must update the workflow reference, tests, and user documentation together.

Do not duplicate the repository's full interfaces in a skill.
Refer to the canonical sources when exact behavior matters so that skill guidance does not become a stale parallel manual.
Both skills should remain usable through the supported Codex and Claude links; avoid provider-specific instructions unless they are necessary and clearly scoped.

Keep skill behavior adaptive, evidence-grounded, protective of existing user
work, and limited to authorized actions. When its capabilities or expectations
change, update the entry point, affected references, and the user-facing AI
workflow documentation together as applicable.

## Validation

When changing report guidance, skills, or the illustrative template, preserve the README's research focus, clear relationships among claims, support, and implications, author choice in presentation, and strict two-page policy.
Page-limit exceptions belong in the authoring and review judgment, with a specific necessity rationale; deterministic builders must preserve complete content rather than truncate reports.

Validate in proportion to the change and its risks.
Exercise the affected workflow and relevant error behavior, confirm documentation against the canonical sources, and compile the example when build or LaTeX behavior changes.
Skill changes should cover representative activation, reference routing, all shared repository-resolver entry points, and affected report tasks.

Run the administrator workflow regression checks with `python3 -B -m unittest discover -s tests -v` (Python 3 standard library only).
These checks use isolated repositories and substitute Docker and desktop openers to exercise artifact placement, failure handling, and platform command routing without publishing reports or opening windows.
Also exercise a real Docker build when available; substituted commands do not validate TeX rendering or a desktop viewer.

Document checks that were not run when they would otherwise be relevant. Do
not claim macOS compatibility was verified unless the affected workflow was
actually exercised on macOS, and identify any supported agent service that was
not exercised when the distinction matters. An unavailable macOS or agent
environment does not by itself block a contribution.

## Documentation and Scope

Update `README.md` when setup arguments, generated command behavior, required software, report-writing instructions, or user-visible skill capabilities change.
Keep maintainer-only administrator details in this document and limit the README to a short pointer and basic setup options.

Keep commits limited to meaningful changes and explain user-visible behavior in
the commit message. Do not include generated PDFs or local configuration unless
the contribution specifically requires updating a tracked artifact.

## Versioning and Releases

Use Semantic Versioning for the repository as a whole. The public interface is
the union of the documented LaTeX commands and environments, setup and build
commands, output semantics, template usage, and skill behavior. Determine a
release increment from every changed public surface and apply the highest
required increment:

- Increment MAJOR for any backward-incompatible public-interface change, such
  as removing or changing a documented LaTeX interface, command option,
  default, or output behavior in a way that requires user migration.
- Increment MINOR for backward-compatible functionality, including a new
  LaTeX interface, command option, setup capability, or skill capability, and
  when deprecating public functionality without removing it.
- Increment PATCH for backward-compatible bug fixes, portability and safety
  corrections, documentation corrections, and internal changes that do not
  alter the documented interface.

Compatibility means that documented usage continues to work with its stated
semantics; it does not require byte-identical PDFs or prevent presentation
refinements that preserve those semantics.

Maintain `CHANGELOG.md` using the Keep a Changelog structure.

Begin every changelog item with the most relevant component marker:
`[latex]`, `[template]`, `[build]`, `[setup]`, `[skill]`, or `[docs]`. Describe
notable user-facing differences rather than copying the commit log, and combine
closely related commits into one entry when they deliver one change.

If you are an AI agent, do not increment the version or create a release tag
without explicit developer confirmation. Versions are recorded by Git tags
named `vMAJOR.MINOR.PATCH`. For every confirmed release, move the relevant
changelog entries from `Unreleased` into a dated version section, update the
version comment at the beginning of `template.tex`, commit those changes, and
create the matching tag on that exact commit. Confirm that the latest-version
badge near the beginning of `README.md` remains configured to derive its value
from the repository's SemVer tags. Do not omit the changelog update, template
update, badge check, or tag.

The setup and build scripts report the version derived from the current Git
checkout. A tagged release prints its tag, while later development commits may
include a commit suffix and a dirty checkout may include `-dirty`. The build
always uses the current checkout; do not add a facility for selecting another
repository version at build time.
