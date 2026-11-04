# Administrator Rollup Workflow

Use this workflow to select source PDFs, prepare a deterministic bundle plan, classify issues, and decide whether promotion requires approval.

On native Windows, use the PowerShell/EXE command substitutions described in the skill entry point and `windows/README.md`; every Bash block, `scripts/...` path, `/tmp` path, Docker instruction, and `.local-config` reference below applies only to Linux/macOS.
Do not execute or probe those POSIX helpers on Windows.
Use the resolved absolute `Start-Weekly-Report.ps1` or `WeeklyReportCLI.exe` path with the matching subcommand, and use Windows absolute paths for plans and review directories.
Preserve all review rules, and pass the native draft's generated `--review` record when promoting with approval.

## Prepare and Select Reports

Resolve the execution environment and reporting period, search only authorized roots, and review candidate evidence before writing the plan.

### Preflight the Administrator Tools

On Windows, run the resolved launcher with `preflight`.
The native check does not use Docker.
The remainder of this section describes Linux/macOS.

On Linux/macOS, run the following from this skill directory as its own command before reading report storage:

```bash
scripts/admin-preflight
```

Do not combine it with filters, pipelines, or unrelated shell commands.
It checks the configured Docker image and the host and container tools required by the administrator workflow.
Preserve its original Docker error output.
If Docker succeeds for the user but this direct command reports socket access denial only in the agent environment, request execution authorization for this exact helper rather than diagnosing the user's Docker installation as broken.

### Resolve the Reporting Period

On Windows, run the resolved launcher with `report-metadata --date YYYY-MM-DD`.
The Bash example below is Linux/macOS only.

Use a date supplied by the user.
Otherwise resolve the current date in the manifest timezone, not the host's implicit timezone.
Resolve the repository root and run the executable metadata helper with that explicit date:

```bash
/absolute/path/to/repository/scripts/report-metadata.sh --date 2026-09-04
```

The helper prints `report-metadata/v1` TSV containing the report date, canonical label, and Monday-to-Sunday period.
Always pass the same date to the platform's `build-bundle` command.
The canonical period identifies the bundle; it does not require each source PDF to contain the same label.

### Discover Within Authorized Roots

Discover candidates only after preflight, using the manifest's authorized roots and verified prior evidence:

1. Resolve configuration and prior bundles through [Administrator Bundle History](rollup-workflow/history.md).
   It covers per-file fallback, PDF/hash verification, cumulative inclusion evidence, final storage, and publication recovery.
   Use the most recent verified successful bundle preceding the target date for candidate comparison, and all earlier verified weeks for the cover.
   Unverifiable history is `unknown`, not evidence of a missing submission; retain the first-run issue when no valid prior bundle exists.
1. On Windows, use `admin-paths` to resolve configuration and history, then `discover` to enumerate candidates from the configured manifest.
   Do not invoke `scripts/admin-paths` or read `.local-config` directly.

   On Linux/macOS, the agent enumerates candidates directly with filesystem tools; no dedicated discovery command is installed.
   Resolve each member's `search_roots` relative to the manifest's `storage_root`, verify that they remain within that storage without traversing directory symlinks, and enumerate only those roots.
   For each member in manifest order, recursively enumerate regular files ending in `.pdf`, case-insensitively, below only that member's search roots.
   Use NUL-delimited filesystem operations so spaces and Unicode names are preserved.
   Exclude AppleDouble files named `._*.pdf`; do not follow directory symlinks.
1. Assess candidates from all available evidence:
   - whether their path, modification time, or SHA-256 differs from the prior selection;
   - proximity of filesystem or PDF metadata times to the reporting period;
   - dates or revision hints in filenames, when present;
   - extractable author, date, or reporting-period text;
   - whether multiple candidates appear to be revisions of the same report.

No single signal is mandatory.
Missing template fields or a missing internal week label is not an issue by itself.
A filesystem modification time alone is not sufficient evidence that a report belongs to the target period.

### Probe Proposed PDFs

Probe every proposed PDF before writing the plan, running each invocation as a standalone command.
On Windows use the resolved launcher's `probe-report` subcommand; the following Bash example is Linux/macOS only:

```bash
scripts/probe-report \
    --storage-root /absolute/path/to/report-storage \
    --file /absolute/path/to/report-storage/member-a/report-current.pdf
```

The probe prints `admin-wr-probe/v1` records for the canonical file path, mtime, SHA-256, readability, page count, encryption, creation date, and text status, followed by `text-begin` and `text-end` delimiters around extracted text.
If it reports a damaged, encrypted, unreadable, or uninspectable PDF, record that candidate as rejected with an `unreadable-pdf` issue.
Select a readable alternative as an `exception` when one exists; otherwise use `missing` or `optional-missing` so the draft can still be built with a status row and no invalid PDF.
Do not bypass a probe failure.

### Classify and Propose

A required member with no plausible candidate is `missing`.
An optional member with none is `optional-missing`.
When several distinct readable candidates remain plausible, choose the best one as `exception` for the proposal and report the ambiguity.
Use `included` when the report identity, target-period relevance, and final-candidate status are clear.

An explicit internal week that differs from the canonical week is `included` with an `internal-week-mismatch` warning when the author, target-period relevance, and lack of a competing final candidate are otherwise clear.
The warning still requires draft review and approval.
If another signal also conflicts or several candidates remain plausible, classify the selection as `exception` with an error instead.

### Check Length and Review Issues

The complete weekly report has a two-page maximum per person, as described in the [shared report policy](../../../docs/report-policy.md#length-and-exceptions).
For a selected report longer than two pages, add an `overlength-report` warning with its page count and any available explanation of necessity; do not invent a justification from length alone.
Keep an otherwise clear selection `included`, preserve every source page in the draft, and use the existing issue-review process before promotion.

An exception is justified only when all reasonable cuts and reorganization have been exhausted and further reduction would compromise essential research meaning or evidence; record that specific rationale in the issue message if established.
Without it, report that the submission needs shortening rather than describing it as compliant.
The bundle's index page and total combined length do not count against an individual's limit.

Approval is required for:

- a missing required report;
- an ambiguous or weakly supported selection;
- an unreadable, damaged, or encrypted selected PDF;
- an overlength report, with the necessity justification or unresolved need for revision shown in the review;
- a prior manifest whose recorded PDF hash no longer matches;
- the first run, when no valid prior bundle exists.

Record rejected candidates and concise reason codes.
Never silently choose a weak candidate merely to complete the roster.

## Build, Confirm, and Promote

Prepare the plan, publish clean bundles directly, and take every issue through temporary draft review before promotion.
On Windows, invoke `build-bundle` and `open-bundle` through the resolved launcher.
Put plans and drafts in an explicit Windows temporary or review directory.
The Bash examples below are Linux/macOS only.

### Write the Temporary Plan

Create the temporary UTF-8 plan using [Bundle Plan and Execution Formats](rollup-workflow/formats.md).
It defines required member entries, candidate and issue records, cumulative history, execution records, and cover presentation.
Include every member and the verified history prepared through [history management](rollup-workflow/history.md#prepare-cumulative-history).
Every `exception` or `missing` entry needs a member-specific issue; global issues such as `first-run` are separate.

### Publish a Clean Bundle

For a clean run:

```bash
scripts/build-bundle \
    --storage-root /absolute/path/to/report-storage \
    --plan /tmp/admin-wr-plan.tsv \
    --date 2026-09-04
```

Run each builder invocation as its own command rather than wrapping it with `bash`, a pipeline, or unrelated verification commands.
After a clean build succeeds, use the absolute final PDF path printed on stdout as the argument to the platform's `open-bundle` command, invoked separately.
Open the file in the configured administrator output directory without requesting review or approval.
If the viewer cannot be launched, report the opening failure separately from successful publication and provide a clickable final PDF path for manual opening.

### Build and Open an Issue Draft

For a run with any issue, first create a temporary draft outside the configured administrator output.
Never use `--draft` with that directory or its descendants.
An administrator output directory is required for final promotion, but a temporary draft may be built without it:

```bash
scripts/build-bundle \
    --storage-root /absolute/path/to/report-storage \
    --plan /tmp/admin-wr-plan.tsv \
    --date 2026-09-04 \
    --draft \
    --output-dir /tmp/admin-wr-review
```

The builder prints the absolute PDF and execution-manifest paths on stdout, one per line, and a shell-quoted `review command` on stderr for draft builds.
The draft PDF remains in the requested temporary directory after the builder exits; its TSV is stored in that directory's `.manifests/` subdirectory and never replaces final history.
Use the emitted command as a standalone invocation to show the PDF in the user's desktop viewer:

```bash
scripts/open-bundle /tmp/admin-wr-review/2026-09-W1.pdf
```

The helper uses `open` on macOS, `xdg-open` on Linux, or `wslview` / Windows PowerShell with `wslpath` on WSL.
It reports a failure if no opener is available or the viewer cannot be launched; in that case, provide the printed PDF path (and Windows path when available) so the user can open it manually.

### Confirm and Promote the Draft

Include a clickable absolute PDF path, proposed selections, rejected candidates, and issues in the review request.
Keep the draft and plan available until the review is resolved.
Opening the viewer does not establish approval.
After explicit approval, recheck source hashes and run:

```bash
scripts/build-bundle \
    --storage-root /absolute/path/to/report-storage \
    --plan /tmp/admin-wr-plan.tsv \
    --date 2026-09-04 \
    --approved-with-issues
```

If the user changes a candidate, update the plan, rebuild the draft, and request approval again for every remaining issue before promotion.
If the temporary directory or plan is no longer available, reconstruct it from current evidence and revalidate rather than assuming it is unchanged.
A changed source invalidates the approval and requires reassessment.

### Notify About Review Issues

During draft review, the optional [Slack notification workflow](slack-notifications.md) can report required omissions, ambiguous candidates, unreadable PDFs, overlength reports, and internal week mismatches.
Show the destination channel and complete message and obtain message-specific administrator approval before sending; a hold decision is not required.

Notification approval is separate from promotion approval; optional non-submission or history issues alone do not qualify.
The PDF builder performs no network notification; sending is a separate action after the administrator's decision.

### Read Execution History

Use [history management](rollup-workflow/history.md) to locate final records, verify PDF/manifest pairs, preserve storage destinations, and recover publication locks.
Draft TSVs never establish successful prior history, and fallback on reads never redirects configured writes.
The [execution format](rollup-workflow/formats.md#execution-manifest-tsv) defines record fields and valid state/approval pairs.
Python consumers must also follow the [administrator development contracts](../../../docs/admin-development.md#execution-records) for parsing and independent evidence checks.
